import time
import uuid
import json
from math import inf
from pokerkit import Automation, Mode, NoLimitTexasHoldem
from pokerkit.state import State

from .game_data_validator import verify_if_scenario_matches_default, map_game_config_to_scenario
import app.llm_manager as llm_manager
import app.state_broadcaster as broadcaster
import app.database as db
from app.game_controller import register_controller, remove_controller


def card_to_str(card):
    """ Safely converts a pokerkit card object to a string (e.g., 'As', 'Td'). """
    return str(card) if card else None


def print_hand_results(state: State, player_map: dict, active_indices: list, initial_cards: dict):
    """
    Helper function to print detailed results after the hand finishes.
    """
    print("\n" + "=" * 60)
    print(f"--- HAND RESULTS (Pot: {state.total_pot_amount}) ---")

    board_str = [str(c) for c in state.board_cards] if state.board_cards else "No Board"
    print(f"Board: {board_str}")

    for i, payoff in enumerate(state.payoffs):
        global_idx = active_indices[i]
        player_name = player_map[global_idx]['name']

        hole_cards = initial_cards.get(i, ["??", "??"])

        hand_description = "Folded"
        if state.statuses[i]:
            try:
                best_hand = state.get_hand(i, 0, 0)
                if best_hand:
                    hand_description = str(best_hand)
            except:
                pass

        result_str = "WINNER" if payoff > 0 else "Neutral/Loser"
        print(f"Player {player_name} (Seat {global_idx}):")
        print(f"  - Cards: {hole_cards}")
        print(f"  - Result: {result_str} (Payoff: {payoff})")
        print(f"  - Hand: {hand_description}")

    print("=" * 60 + "\n")


def start_game_session(game_config: dict, game_id: str):
    """
    Main function called by /game/start in a separate thread.
    Runs and manages the full poker game session.
    """
    game_id = str(uuid.uuid4())
    print(f"[Poker Engine] Starting game {game_id} with config: {game_config}")
    is_data_valid_with_default_scenario = verify_if_scenario_matches_default(
        map_game_config_to_scenario(game_config)
    )
    controller = register_controller(game_id)
    try:
        if is_data_valid_with_default_scenario is True:
            db.init_db()
            db.create_new_game(game_id, game_config, game_config['players'])

        # --- Game Setup ---
        player_map = {i: player for i, player in enumerate(game_config['players'])}
        total_players_count = len(player_map)

        current_stacks = [game_config.get('initial_stack', 10000)] * total_players_count
        blinds = (game_config.get('small_blind', 10), game_config.get('big_blind', 20))
        big_blind = blinds[1]

        automations_tuple = (
            Automation.ANTE_POSTING,
            Automation.BET_COLLECTION,
            Automation.BLIND_OR_STRADDLE_POSTING,
            Automation.CARD_BURNING,
            Automation.HOLE_DEALING,
            Automation.BOARD_DEALING,
            Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
            Automation.HAND_KILLING,
            Automation.CHIPS_PUSHING,
            Automation.CHIPS_PULLING,
            Automation.RUNOUT_COUNT_SELECTION,
        )

        max_hands_to_play = game_config.get('number_of_hands')
        hands_played = 0
        if max_hands_to_play:
            print(f"[Poker Engine] Game will run for a maximum of {max_hands_to_play} hands.")
        else:
            print("[Poker Engine] No hand limit set. Game will run until one player remains.")

        # --- 2. Main Game Loop ---
        while True:
            if max_hands_to_play is not None and hands_played >= max_hands_to_play:
                print(f"[Poker Engine] Game over: Reached hand limit of {max_hands_to_play}.")
                break

            controller.wait_for_turn()

            active_indices = [i for i, stack in enumerate(current_stacks) if stack > 0]

            if len(active_indices) <= 1:
                print("[Poker Engine] Game over: Only one player has chips remaining.")
                break

            pokerkit_stacks = [current_stacks[i] for i in active_indices]
            pokerkit_player_count = len(active_indices)

            hands_played += 1

            stacks_before_hand = list(current_stacks)

            game_story = []
            chat_log = []
            last_event = None

            print(f"\n[Poker Engine] New hand started (#{hands_played}). Active players: {len(active_indices)}")

            state = NoLimitTexasHoldem.create_state(
                automations_tuple,
                False, {}, blinds, big_blind,
                tuple(pokerkit_stacks),
                pokerkit_player_count,
                mode=Mode.CASH_GAME
            )

            initial_hole_cards = {}

            print(f"[Poker Engine] --- DEALING HOLE CARDS ---")
            for local_i in range(pokerkit_player_count):
                initial_hole_cards[local_i] = [card_to_str(c) for c in state.hole_cards[local_i]]

                global_idx = active_indices[local_i]
                player_name = player_map[global_idx]['name']
                print(f"  {player_name} (Seat {global_idx}): {initial_hole_cards[local_i]}")
            print(f"---------------------------------------")

            last_board_count = 0

            # --- 3. Hand Loop ---
            while state.status:
                if len(state.board_cards) > last_board_count:
                    new_cards = state.board_cards[last_board_count:]
                    print(
                        f"[Poker Engine] *** BOARD UPDATED *** New: {[str(c) for c in new_cards]} | Full: {[str(c) for c in state.board_cards]}")
                    last_board_count = len(state.board_cards)

                if state.actor_index is None:
                    time.sleep(0.1)
                    continue

                print(f"[Poker Engine] Waiting for controller permit...")
                controller.wait_for_turn()

                local_actor_index = state.actor_index
                global_player_index = active_indices[local_actor_index]
                player_data = player_map[global_player_index]

                print(f"[Poker Engine] Player to move: {player_data['name']} (Global Index: {global_player_index})")

                prompt_json = build_llm_prompt(state, local_actor_index, active_indices, player_map, game_story)
                user_strategy = player_data.get('user_prompt')

                action_response = llm_manager.get_llm_action(
                    model_id=player_data['model_id'],
                    prompt_json=prompt_json,
                    user_prompt=user_strategy
                )

                action_str, amount_validated, message = validate_and_execute_action(state, action_response)

            print(f"[Poker Engine] LLM ({player_data['name']}) chose: {action_str}, Value: {amount_validated}")
            if is_data_valid_with_default_scenario is True:
                db.log_game_event(
                    game_id=game_id,
                    hand_num=hands_played,
                    player_name=player_data['name'],
                    model_id=player_data['model_id'],
                    hole_cards=initial_hole_cards[local_actor_index],
                    action=action_str,
                    amount=amount_validated,
                    message=message,
                    prompt_json=prompt_json
                )

                last_event = {
                    "action": action_str,
                    "player": player_data['name'],
                    "amount": amount_validated,
                    "comment": message
                }
                game_story.append(last_event)
                if message:
                    chat_log.append({
                        "player": player_data['name'],
                        "action": action_str,
                        "amount": amount_validated,
                        "message": message
                    })

                frontend_state = build_frontend_state(
                    state, player_map, active_indices, chat_log, last_event,
                    total_players_count, current_stacks, initial_hole_cards
                )
                broadcaster.broadcast_game_state(frontend_state)
                time.sleep(0.5)

            # --- 10. End of Hand ---
            print("[Poker Engine] Hand finished. Settling pot.")

            print_hand_results(state, player_map, active_indices, initial_hole_cards)

            for local_i, final_stack in enumerate(state.stacks):
                global_i = active_indices[local_i]
                current_stacks[global_i] = final_stack

            hand_stats = []
            for g_idx, p_data in player_map.items():

                stats_entry = {
                    'name': p_data['name'],
                    'model': p_data['model_id'],
                    'temp': p_data.get('temperature', 1.0),
                    'before': stacks_before_hand[g_idx],
                    'after': current_stacks[g_idx]
                }
                hand_stats.append(stats_entry)

            if is_data_valid_with_default_scenario is True:
                db.save_hand_result(game_id, hands_played, hand_stats)

                final_state = build_frontend_state(
                    state, player_map, active_indices, chat_log, last_event,
                    total_players_count, current_stacks, initial_hole_cards, hand_over=True
                )
                broadcaster.broadcast_game_state(final_state)

                players_with_chips_check = sum(1 for stack in current_stacks if stack > 0)
                if players_with_chips_check > 1 and (max_hands_to_play is None or hands_played < max_hands_to_play):
                    print(f"[Poker Engine] Next hand in 5 seconds...")
                    time.sleep(5)
    except Exception as e:
        print(f"[Poker Engine] Error in game {game_id}: {e}")
    finally:
        remove_controller(game_id)
        print(f"[Poker Engine] Game {game_id} finished. Controller removed.")



def build_llm_prompt(state: State, local_player_index: int, active_indices: list, player_map: dict,
                     game_story: list) -> dict:
    global_player_index = active_indices[local_player_index]
    player_data = player_map[global_player_index]

    hole_cards = [card_to_str(c) for c in state.hole_cards[local_player_index]]
    board_cards = [card_to_str(c) for c in state.board_cards] if state.board_cards else []

    legal_moves = []
    if state.can_fold: legal_moves.append("fold")
    if state.can_check_or_call:
        legal_moves.append("check" if state.checking_or_calling_amount == 0 else "call")
    if state.can_complete_bet_or_raise_to:
        legal_moves.append("bet" if state.checking_or_calling_amount == 0 else "raise")

    opponents = []
    for local_i in range(state.player_count):
        if local_i == local_player_index: continue
        global_op_index = active_indices[local_i]
        opponent_data = player_map[global_op_index]
        is_active = state.statuses[local_i]
        opponents.append({
            "name": opponent_data['name'],
            "stack": state.stacks[local_i],
            "position": "Unknown",
            "status": "playing" if is_active else "folded",
            "currentBet": state.bets[local_i]
        })

    prompt = {
        "type": "prompt_action",
        "to": player_data['name'],
        "hole_cards": hole_cards,
        "board": board_cards,
        "legal_moves": legal_moves,
        "pot": state.total_pot_amount,
        "opponents": opponents,
        "your_stack": state.stacks[local_player_index],
        "bet_to_call": state.checking_or_calling_amount,
        "min_raise": state.min_completion_betting_or_raising_to_amount,
        "max_raise": state.max_completion_betting_or_raising_to_amount,
        "game_story": game_story
    }
    return prompt


def build_frontend_state(state: State, player_map: dict, active_indices: list, chat_log: list, last_event: dict,
                         total_players_count: int, current_global_stacks: list, initial_hole_cards: dict,
                         hand_over: bool = False) -> dict:
    """
    Constructs frontend JSON.
    Uses 'initial_hole_cards' to ensure cards are always visible (spectator mode).
    """

    # Formatting helper
    def fmt_card(c_str):
        if not c_str: return None
        return c_str[-3:-1]

    board_cards = [fmt_card(str(c)) for c in state.board_cards] if state.board_cards else []
    community_cards = board_cards + [None] * (5 - len(board_cards))

    players = []
    global_to_local = {global_idx: local_idx for local_idx, global_idx in enumerate(active_indices)}

    for global_i in range(total_players_count):
        player_data = player_map[global_i]

        chip_count = current_global_stacks[global_i]
        current_bet = 0
        cards_to_show = [None, None]
        status = "eliminated" if chip_count == 0 else "waiting"

        if global_i in global_to_local:
            local_i = global_to_local[global_i]
            chip_count = state.stacks[local_i]
            current_bet = state.bets[local_i]
            is_active_in_hand = state.statuses[local_i]
            status = "playing" if is_active_in_hand else "folded"

            raw_cards = initial_hole_cards.get(local_i)
            if raw_cards:
                cards_to_show = [fmt_card(c) for c in raw_cards]
            else:
                cards_to_show = [None, None]

        players.append({
            "name": player_data['name'],
            "chipCount": chip_count,
            "currentBet": current_bet,
            "holeCards": cards_to_show,
            "status": status
        })

    active_player_name = None
    if state.status and state.actor_index is not None:
        global_active_idx = active_indices[state.actor_index]
        active_player_name = player_map[global_active_idx]['name']

    return {
        "pot": state.total_pot_amount,
        "communityCards": community_cards,
        "players": players,
        "activePlayer": active_player_name,
        "chatLog": chat_log,
        "lastEvent": last_event
    }


def validate_and_execute_action(state: State, llm_response: dict | None) -> tuple:
    if llm_response is None:
        print("[Poker Engine] Error: LLM did not respond. Auto-folding.")
        return safe_default_action(state, "LLM Error: No response")

    action_str = llm_response.get("action", "fold").lower()
    amount = llm_response.get("amount")
    message = llm_response.get("message", "")

    # Debug limits
    try:
        min_r = state.min_completion_betting_or_raising_to_amount
        max_r = state.max_completion_betting_or_raising_to_amount
        # print(f"[Debug Action] ...")
    except:
        pass

    try:
        if action_str == "fold":
            if state.can_fold:
                state.fold()
                return "fold", 0, message
            else:
                if state.can_check_or_call:
                    state.check_or_call()
                    return "check", 0, message
                raise Exception("Cannot fold/check")

        elif action_str == "check" or action_str == "call":
            if state.can_check_or_call:
                bet_called = state.checking_or_calling_amount
                state.check_or_call()
                return "call" if bet_called > 0 else "check", bet_called, message
            else:
                raise Exception("Cannot check or call")

        elif action_str == "bet" or action_str == "raise" or action_str == "all_in":
            if state.can_complete_bet_or_raise_to:
                min_bet = state.min_completion_betting_or_raising_to_amount
                max_bet = state.max_completion_betting_or_raising_to_amount

                if min_bet is None: min_bet = 0
                if max_bet is None: max_bet = inf

                if not isinstance(amount, (int, float)): amount = min_bet
                if action_str == "all_in": amount = max_bet

                clamped_amount = max(min_bet, min(amount, max_bet))

                state.complete_bet_or_raise_to(clamped_amount)
                return "raise", clamped_amount, message
            else:
                if state.can_check_or_call:
                    bet_called = state.checking_or_calling_amount
                    state.check_or_call()
                    return "call", bet_called, message
                raise Exception("Cannot bet or raise")
        else:
            raise Exception(f"Unknown action: {action_str}")

    except Exception as e:
        print(f"[Poker Engine] Error: LLM action '{action_str}' failed ('{e}'). Using safe default.")
        return safe_default_action(state, f"Action failed, auto-move.")


def safe_default_action(state: State, message: str) -> tuple:
    if state.can_check_or_call:
        amt = state.checking_or_calling_amount
        state.check_or_call()
        return "call" if amt > 0 else "check", amt, message
    elif state.can_fold:
        state.fold()
        return "fold", 0, message
    else:
        return "error", 0, "No safe action"