import time
import uuid
import json
from math import inf
from collections import Counter
from pokerkit import Automation, Mode, NoLimitTexasHoldem
from pokerkit.state import State
from pokerkit import Card

from .game_data_validator import verify_if_scenario_matches_default, map_game_config_to_scenario, \
    check_if_llm_models_are_all_different_players
import app.llm_manager as llm_manager
import app.state_broadcaster as broadcaster
import app.database as db
from app.game_controller import register_controller, remove_controller


# --- Custom Exception for Benchmark ---
class LLMFailure(Exception):
    """Raised when LLM fails and we want to retry the hand (Benchmark mode)."""
    pass


# --- Helpers ---

def card_to_str(card):
    """ Safely converts a pokerkit card object to a string (e.g., 'As', 'Td'). """
    return str(card) if card else None


def make_player_names_unique(players_list: list):
    """
    Modifies the list of players in-place to ensure unique names.
    """
    original_names = [p['name'] for p in players_list]
    counts = Counter(original_names)
    current_counters = {name: 0 for name in original_names}

    for p in players_list:
        name = p['name']
        if counts[name] > 1:
            current_counters[name] += 1
            p['name'] = f"{name} {current_counters[name]}"


def print_hand_results(state: State, player_map: dict, active_indices: list, initial_cards: dict):
    print("\n" + "=" * 60)
    print(f"--- HAND RESULTS (Pot: {state.total_pot_amount}) ---")
    board_str = [str(c) for c in state.board_cards] if state.board_cards else "No Board"
    print(f"Board: {board_str}")

    for i, payoff in enumerate(state.payoffs):
        global_idx = active_indices[i]
        player_name = player_map[global_idx]['name']
        hole_cards = initial_cards.get(i, ["??", "??"])

        result_str = "WINNER" if payoff > 0 else "Neutral/Loser"
        print(f"Player {player_name} (Seat {global_idx}): Cards: {hole_cards} -> {result_str} ({payoff})")
    print("=" * 60 + "\n")


# --- CORE LOGIC: SINGLE HAND EXECUTION ---

def play_single_hand(
        game_id: str,
        player_map: dict,
        starting_stacks: list,
        blinds: tuple,
        automations: tuple,
        controller,
        hand_number: int,
        deck: list = None,  # <--- Lista obiektów Card (nie stringów!)
        is_benchmark: bool = False,
        structured_output: bool = False
):
    """
    Executes exactly one hand of poker.
    """

    # 1. Determine Active Players
    active_indices = [i for i, stack in enumerate(starting_stacks) if stack > 0]
    if len(active_indices) <= 1:
        return {"status": "skipped", "reason": "not_enough_players"}

    pokerkit_stacks = [starting_stacks[i] for i in active_indices]
    pokerkit_player_count = len(active_indices)

    # 2. Initialize Stats
    hand_stats = {
        g_idx: {
            "vpip": False,
            "errors": 0,
            "initial_stack": starting_stacks[g_idx],
            "final_stack": starting_stacks[g_idx],
            "profit": 0,
            "actions_count": 0
        } for g_idx in active_indices
    }

    # 3. Create PokerKit State
    state = NoLimitTexasHoldem.create_state(
        automations,  # 1. automations
        False,  # 2. divmod
        {},  # 3. ante_trimming_status
        blinds,  # 5. raw_blinds_or_straddles
        blinds[1],  # 6. min_bet (Big Blind)
        tuple(pokerkit_stacks),  # 7. raw_starting_stacks
        pokerkit_player_count  # 8. player_count
    )

    # === DECK INJECTION ===
    if deck is not None:
        # Nadpisujemy losową talię tą, którą podał benchmark (Rigged Deck)
        state.deck = deck
    # ======================

    # 4. Capture and Log Hole Cards (Dla Monitoringu Benchmarku)
    initial_hole_cards = {}
    print(f"\n[Poker Engine] --- DEALING HOLE CARDS (Hand {hand_number}) ---")
    for local_i in range(pokerkit_player_count):
        cards_str = [card_to_str(c) for c in state.hole_cards[local_i]]
        initial_hole_cards[local_i] = cards_str

        global_idx = active_indices[local_i]
        player_name = player_map[global_idx]['name']
        print(f"  > {player_name} (Seat {global_idx}): {cards_str}")
    print(f"---------------------------------------------------")

    game_story = []
    chat_log = []

    # --- Hand Loop ---
    last_board_len = 0
    while state.status:
        # Logowanie Boardu w trakcie gry
        if len(state.board_cards) > last_board_len:
            new_cards = [str(c) for c in state.board_cards[last_board_len:]]
            print(f"[Poker Engine] *** BOARD: {new_cards} (Full: {[str(c) for c in state.board_cards]})")
            last_board_len = len(state.board_cards)

        if controller:
            if controller.is_aborted_flag: return {"status": "aborted"}
            if state.actor_index is not None:
                controller.wait_for_turn()
                if controller.is_aborted_flag: return {"status": "aborted"}

        if state.actor_index is None:
            if not is_benchmark: time.sleep(0.1)
            continue

        local_actor_index = state.actor_index
        global_player_index = active_indices[local_actor_index]
        player_data = player_map[global_player_index]

        prompt_json = build_llm_prompt(state, local_actor_index, active_indices, player_map, game_story)
        user_strategy = player_data.get('user_prompt')

        # LLM Call
        action_response = None
        if structured_output:
            action_response = llm_manager.get_llm_action(
                model_id=player_data['model_id'],
                prompt_json=prompt_json,
                user_prompt=user_strategy,
                temperature=player_data.get('temperature', 1.0)
            )
        else:
            action_response = llm_manager.get_llm_action_text(
                model_id=player_data['model_id'],
                prompt_json=prompt_json,
                user_prompt=user_strategy,
                temperature=player_data.get('temperature', 1.0)
            )

        if action_response is None and is_benchmark:
            raise LLMFailure(f"LLM {player_data['model_id']} failed to respond.")

        action_str, amount_validated, message, is_error = validate_and_execute_action(state, action_response)

        # Stats Update
        stats = hand_stats[global_player_index]
        stats["actions_count"] += 1
        if is_error:
            stats["errors"] += 1
        if action_str in ["call", "bet", "raise", "all_in"]:
            stats["vpip"] = True

        last_event = {
            "action": action_str,
            "player": player_data['name'],
            "amount": amount_validated,
            "comment": message
        }
        game_story.append(last_event)
        if message:
            chat_log.append(last_event)

        if not is_benchmark:
            frontend_state = build_frontend_state(
                state, player_map, active_indices, chat_log, last_event,
                len(player_map), starting_stacks, initial_hole_cards
            )
            broadcaster.broadcast_game_state(frontend_state, game_id)
            time.sleep(0.5)

    # --- End of Hand ---
    final_global_stacks = list(starting_stacks)
    for local_i, stack_val in enumerate(state.stacks):
        global_i = active_indices[local_i]
        final_global_stacks[global_i] = stack_val
        hand_stats[global_i]["final_stack"] = stack_val
        hand_stats[global_i]["profit"] = stack_val - hand_stats[global_i]["initial_stack"]

    if not is_benchmark:
        print_hand_results(state, player_map, active_indices, initial_hole_cards)

    return {
        "status": "completed",
        "hand_stats": hand_stats,
        "final_stacks": final_global_stacks,
        "initial_hole_cards": initial_hole_cards,
        "game_story": game_story,
        "is_valid_scenario": True
    }


# --- MAIN WEB SESSION LOOP ---

def start_game_session(game_config: dict, game_id: str):
    """
    Main function called by /game/start (Web API).
    """
    print(f"[Poker Engine] Starting game {game_id} with config: {game_config}")
    make_player_names_unique(game_config['players'])

    is_valid_scenario = verify_if_scenario_matches_default(
        map_game_config_to_scenario(game_config)
    ) is True and check_if_llm_models_are_all_different_players(game_config['players'])

    controller = register_controller(game_id)
    game_end_reason = "unknown"

    try:
        if is_valid_scenario:
            db.init_db()
            db.create_new_game(game_id, game_config, game_config['players'])

        player_map = {i: player for i, player in enumerate(game_config['players'])}
        current_stacks = [game_config.get('initial_stack', 10000)] * len(player_map)
        blinds = (game_config.get('small_blind', 10), game_config.get('big_blind', 20))
        automations = (
            Automation.ANTE_POSTING, Automation.BET_COLLECTION, Automation.BLIND_OR_STRADDLE_POSTING,
            Automation.CARD_BURNING, Automation.HOLE_DEALING, Automation.BOARD_DEALING,
            Automation.HOLE_CARDS_SHOWING_OR_MUCKING, Automation.HAND_KILLING,
            Automation.CHIPS_PUSHING, Automation.CHIPS_PULLING, Automation.RUNOUT_COUNT_SELECTION,
        )

        max_hands = game_config.get('number_of_hands')
        hands_played = 0

        # === GAME LOOP ===
        while True:
            if controller.is_aborted_flag:
                game_end_reason = "user_abort"
                break
            if max_hands and hands_played >= max_hands:
                game_end_reason = "hand_limit"
                break
            if sum(1 for s in current_stacks if s > 0) <= 1:
                game_end_reason = "elimination"
                break

            controller.wait_for_turn()
            if controller.is_aborted_flag:
                game_end_reason = "user_abort"
                break

            hands_played += 1
            print(f"\n[Poker Engine] Starting Hand #{hands_played}")

            # CALL SINGLE HAND
            result = play_single_hand(
                game_id=game_id,
                player_map=player_map,
                starting_stacks=current_stacks,
                blinds=blinds,
                automations=automations,
                controller=controller,
                hand_number=hands_played,
                deck=None,  # WEB MODE = RANDOM DECK
                is_benchmark=False,
                structured_output=game_config.get('structured_output', False)
            )

            if result["status"] == "aborted":
                game_end_reason = "user_abort"
                break

            current_stacks = result["final_stacks"]

            if is_valid_scenario:
                db_stats = []
                for g_idx, stats in result['hand_stats'].items():
                    db_stats.append({
                        'name': player_map[g_idx]['name'],
                        'model': player_map[g_idx]['model_id'],
                        'temp': player_map[g_idx].get('temperature', 1.0),
                        'before': stats['initial_stack'],
                        'after': stats['final_stack']
                    })
                db.save_hand_result(game_id, hands_played, db_stats)

            # Broadcast End of Hand signal (optional update)
            final_fe_state = build_frontend_state(
                None, player_map, [], [], {}, len(player_map), current_stacks,
                result.get("initial_hole_cards", {}), hand_over=True
            )
            # broadcaster.broadcast_game_state(final_fe_state, game_id)

            time.sleep(5)

    except Exception as e:
        print(f"[Poker Engine] Critical Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        summary = build_game_over_summary(
            game_id, player_map, current_stacks, game_config.get('initial_stack', 10000), hands_played, game_end_reason
        )
        broadcaster.broadcast_game_over(summary, game_id)
        remove_controller(game_id)
        print(f"[Poker Engine] Game {game_id} finished.")


# --- VALIDATION & PROMPTS ---

def validate_and_execute_action(state: State, llm_response: dict | None) -> tuple:
    is_error = False
    if llm_response is None:
        print("[Poker Engine] Error: LLM did not respond. Auto-folding.")
        act, amt, msg = safe_default_action(state, "LLM Error: No response")
        return act, amt, msg, True

    action_str = llm_response.get("action", "fold").lower()
    amount = llm_response.get("amount")
    message = llm_response.get("message", "")

    try:
        if action_str == "fold":
            if state.can_fold:
                state.fold()
                return "fold", 0, message, False
            else:
                if state.can_check_or_call:
                    state.check_or_call()
                    return "check", 0, message, True
                raise Exception("Cannot fold/check")

        elif action_str == "check" or action_str == "call":
            if state.can_check_or_call:
                bet_called = state.checking_or_calling_amount
                state.check_or_call()
                return ("call" if bet_called > 0 else "check"), bet_called, message, False
            else:
                raise Exception("Cannot check or call")

        elif action_str in ["bet", "raise", "all_in"]:
            if state.can_complete_bet_or_raise_to:
                min_bet = state.min_completion_betting_or_raising_to_amount
                max_bet = state.max_completion_betting_or_raising_to_amount

                if min_bet is None: min_bet = 0
                if max_bet is None: max_bet = inf

                if not isinstance(amount, (int, float)): amount = min_bet
                if action_str == "all_in": amount = max_bet

                clamped = max(min_bet, min(amount, max_bet))
                state.complete_bet_or_raise_to(clamped)
                return "raise", clamped, message, False
            else:
                if state.can_check_or_call:
                    amt = state.checking_or_calling_amount
                    state.check_or_call()
                    return "call", amt, message, True
                raise Exception("Cannot bet or raise")
        else:
            raise Exception(f"Unknown action: {action_str}")

    except Exception as e:
        print(f"[Poker Engine] Action Error: '{action_str}' -> {e}")
        act, amt, msg = safe_default_action(state, "Action failed, auto-move.")
        return act, amt, msg, True


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


def build_llm_prompt(state: State, local_player_index: int, active_indices: list, player_map: dict,
                     game_story: list) -> dict:
    global_idx = active_indices[local_player_index]
    player_data = player_map[global_idx]

    hole_cards = [card_to_str(c) for c in state.hole_cards[local_player_index]]
    board = [card_to_str(c) for c in state.board_cards] if state.board_cards else []

    legal_moves = []
    if state.can_fold: legal_moves.append("fold")
    if state.can_check_or_call: legal_moves.append("check" if state.checking_or_calling_amount == 0 else "call")
    if state.can_complete_bet_or_raise_to: legal_moves.append(
        "bet" if state.checking_or_calling_amount == 0 else "raise")

    opponents = []
    for i in range(state.player_count):
        if i == local_player_index: continue
        g_idx = active_indices[i]
        opponents.append({
            "name": player_map[g_idx]['name'],
            "stack": state.stacks[i],
            "status": "playing" if state.statuses[i] else "folded",
            "currentBet": state.bets[i]
        })

    return {
        "type": "prompt_action",
        "to": player_data['name'],
        "hole_cards": hole_cards,
        "board": board,
        "legal_moves": legal_moves,
        "pot": state.total_pot_amount,
        "opponents": opponents,
        "your_stack": state.stacks[local_player_index],
        "bet_to_call": state.checking_or_calling_amount,
        "min_raise": state.min_completion_betting_or_raising_to_amount,
        "max_raise": state.max_completion_betting_or_raising_to_amount,
        "game_story": game_story
    }


def build_frontend_state(state: State, player_map: dict, active_indices: list, chat_log: list, last_event: dict,
                         total_players_count: int, current_global_stacks: list, initial_hole_cards: dict,
                         hand_over: bool = False) -> dict:
    pot = state.total_pot_amount if state else 0
    board_cards = []
    if state and state.board_cards:
        board_cards = [str(c)[-3:-1] for c in state.board_cards]

    community_cards = board_cards + [None] * (5 - len(board_cards))

    players = []
    global_to_local = {g: l for l, g in enumerate(active_indices)} if state else {}

    for global_i in range(total_players_count):
        p_data = player_map[global_i]
        chip_count = current_global_stacks[global_i]
        current_bet = 0
        cards = [None, None]
        status = "eliminated" if chip_count == 0 else "waiting"

        if state and global_i in global_to_local:
            local_i = global_to_local[global_i]
            chip_count = state.stacks[local_i]
            current_bet = state.bets[local_i]
            status = "playing" if state.statuses[local_i] else "folded"

            raw = initial_hole_cards.get(local_i)
            if raw: cards = [r[-3:-1] for r in raw]

        players.append({
            "name": p_data['name'],
            "chipCount": chip_count,
            "currentBet": current_bet,
            "holeCards": cards,
            "status": status
        })

    return {
        "pot": pot,
        "communityCards": community_cards,
        "players": players,
        "chatLog": chat_log,
        "lastEvent": last_event,
        "activePlayer": player_map[active_indices[state.actor_index]]['name'] if (
                state and state.actor_index is not None) else None
    }


def build_game_over_summary(game_id, player_map, current_stacks, initial_stack, hands_played, reason):
    ranking = []
    for i, p in player_map.items():
        ranking.append({
            "name": p['name'],
            "model": p['model_id'],
            "final_stack": current_stacks[i],
            "net_profit": current_stacks[i] - initial_stack
        })
    ranking.sort(key=lambda x: x['final_stack'], reverse=True)
    return {
        "type": "GAME_OVER",
        "game_id": game_id,
        "reason": reason,
        "total_hands": hands_played,
        "ranking": ranking
    }