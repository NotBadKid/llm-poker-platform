import time
from math import inf
from pokerkit import Automation, Mode, NoLimitTexasHoldem
from pokerkit.state import State
import app.llm_manager as llm_manager
import app.state_broadcaster as broadcaster


def card_to_str(card):
    """ Safely converts a pokerkit card object to a string (e.g., 'As', 'Td'). """
    return str(card) if card else None


def start_game_session(game_config: dict):
    """
    Main function called by /game/start in a separate thread.
    Runs and manages the full poker game session.
    """
    print(f"[Poker Engine] Starting game with config: {game_config}")

    # --- 1. Game Setup ---
    player_map = {i: player for i, player in enumerate(game_config['players'])}
    player_count = len(player_map)

    current_stacks = tuple([game_config.get('initial_stack', 10000)] * player_count)
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
    )

    # --- Hand Limit Settings ---
    max_hands_to_play = game_config.get('number_of_hands')
    hands_played = 0
    if max_hands_to_play:
        print(f"[Poker Engine] Game will run for a maximum of {max_hands_to_play} hands.")
    else:
        print("[Poker Engine] No hand limit set. Game will run until one player remains.")

    # --- 2. Main Game Loop (hand after hand) ---
    while True:
        if max_hands_to_play is not None and hands_played >= max_hands_to_play:
            print(f"[Poker Engine] Game over: Reached hand limit of {max_hands_to_play}.")
            break

        players_with_chips = sum(1 for stack in current_stacks if stack > 0)
        if players_with_chips <= 1:
            print("[Poker Engine] Game over: Only one player has chips remaining.")
            break

        hands_played += 1
        game_story = []
        chat_log = []
        last_event = None

        print(f"\n[Poker Engine] New hand started (#{hands_played}).")

        state = NoLimitTexasHoldem.create_state(
            automations_tuple,  # Use standard automations
            False,  # uniform_antes
            {},  # antes
            blinds,  # blinds_or_straddles
            big_blind,  # min_bet
            current_stacks,  # Pass the *current* stacks
            player_count,
            mode=Mode.CASH_GAME
        )

        # --- 3. Hand Loop (betting round after betting round) ---
        while state.status:
            #state.collect_bets()

            if not state.status:
                break

            player_index = state.actor_index
            if player_index is None:
                break
            player_data = player_map[player_index]

            print(f"[Poker Engine] Player to move: {player_data['name']} (Index: {player_index})")

            # --- 4. Generate JSON for LLM ---
            prompt_json = build_llm_prompt(state, player_index, player_map, game_story)

            # --- 5. Call LLM Manager ---
            action_response = llm_manager.get_llm_action(
                model_id=player_data['model_id'],
                prompt_json=prompt_json
            )

            # --- 6. Validate and Execute Action ---
            action_str, amount_validated, message = validate_and_execute_action(
                state,
                action_response
            )

            print(f"[Poker Engine] LLM ({player_data['name']}) chose: {action_str}, Value: {amount_validated}")

            # --- 7. Update History and Logs ---
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

            # --- 8. Generate JSON for Frontend ---
            frontend_state = build_frontend_state(state, player_map, chat_log, last_event, player_count)

            # --- 9. Broadcast State to Frontend ---
            broadcaster.broadcast_game_state(frontend_state)

            time.sleep(0.5)

        # --- 10. End of Hand ---
        print("[Poker Engine] Hand finished. Settling pot.")

        current_stacks = tuple(state.stacks)

        final_state = build_frontend_state(state, player_map, chat_log, last_event, player_count, hand_over=True)
        broadcaster.broadcast_game_state(final_state)

        players_with_chips_check = sum(1 for stack in current_stacks if stack > 0)
        if players_with_chips_check > 1 and (max_hands_to_play is None or hands_played < max_hands_to_play):
            print(f"[Poker Engine] Next hand in 5 seconds...")
            time.sleep(5)

    print("[Poker Engine] Final game state. Session ended.")


def build_llm_prompt(state: State, player_index: int, player_map: dict, game_story: list) -> dict:
    """
    Creates a dictionary (JSON) prompt for the LLM based on the current game state.
    """
    player_data = player_map[player_index]

    hole_cards = [card_to_str(c) for c in state.hole_cards[player_index]]
    board_cards = []
    if state.board_cards:
        board_cards = [card_to_str(c) for c in state.board_cards]

    legal_moves = []
    if state.can_fold:
        legal_moves.append("fold")
    if state.can_check_or_call:
        if state.checking_or_calling_amount == 0:
            legal_moves.append("check")
        else:
            legal_moves.append("call")
    if state.can_complete_bet_or_raise_to:
        if state.checking_or_calling_amount == 0:
            legal_moves.append("bet")
        else:
            legal_moves.append("raise")

    # Build the list of opponents
    opponents = []
    for i in range(state.player_count):
        if i == player_index: continue
        opponent_data = player_map[i]
        is_active = state.statuses[i]

        opponents.append({
            "name": opponent_data['name'],
            "stack": state.stacks[i],
            "position": "Unknown",  # ZMIANA: Usunięto 'dealer_index'
            "status": "playing" if is_active else "folded",
            "currentBet": state.bets[i]
        })

    prompt = {
        "type": "prompt_action",
        "to": player_data['name'],
        "hole_cards": hole_cards,
        "board": board_cards,
        "legal_moves": legal_moves,
        "pot": state.total_pot_amount,
        "opponents": opponents,
        "your_stack": state.stacks[player_index],
        "bet_to_call": state.checking_or_calling_amount,  # ZMIANA
        "min_raise": state.min_completion_betting_or_raising_to_amount,
        "max_raise": state.max_completion_betting_or_raising_to_amount,
        "game_story": game_story
    }

    return prompt


def build_frontend_state(state: State, player_map: dict, chat_log: list, last_event: dict, player_count: int,
                         hand_over: bool = False) -> dict:
    """
    Creates a dictionary (JSON) for the frontend based on the current game state.
    """
    board_cards = []
    if state.board_cards:
        board_cards = [card_to_str(c)[-3:-1] for c in state.board_cards]
    community_cards = board_cards + [None] * (5 - len(board_cards))

    players = []
    for i in range(player_count):
        player_data = player_map[i]
        hole_cards = [card_to_str(c)[-3:-1] for c in state.hole_cards[i]]
        cards_to_show = hole_cards if hole_cards else [None, None]

        is_active = state.statuses[i]
        if not is_active:
            cards_to_show = [None, None]

        players.append({
            "name": player_data['name'],
            "chipCount": state.stacks[i],
            "currentBet": state.bets[i],
            "holeCards": cards_to_show,
            "status": "playing" if is_active else "folded"
        })

    active_player = None
    if state.status and state.actor_index is not None:
        active_player = player_map[state.actor_index]['name']

    state_json = {
        "pot": state.total_pot_amount,
        "communityCards": community_cards,
        "players": players,
        "activePlayer": active_player,
        "chatLog": chat_log,
        "lastEvent": last_event
    }

    return state_json


def validate_and_execute_action(state: State, llm_response: dict | None) -> tuple:
    """
    Validates the LLM's response and EXECUTES the action directly on the 'state' object.
    Returns: (action_str, amount, message) for logging.
    """
    if llm_response is None:
        print("[Poker Engine] Error: LLM did not respond. Auto-folding.")
        return safe_default_action(state, "LLM Error: No response")

    action_str = llm_response.get("action", "fold").lower()
    amount = llm_response.get("amount")
    message = llm_response.get("message")

    try:
        if action_str == "fold":
            if state.can_fold:
                state.fold()
                return "fold", 0, message
            else:
                raise Exception("Cannot fold")

        elif action_str == "check" or action_str == "call":
            if state.can_check_or_call:
                bet_called = state.checking_or_calling_amount
                state.check_or_call()
                return "call" if bet_called > 0 else "check", bet_called, message
            else:
                raise Exception("Cannot check or call")

        elif action_str == "bet" or action_str == "raise":
            if state.can_complete_bet_or_raise_to:
                min_bet = state.min_completion_betting_or_raising_to_amount
                max_bet = state.max_completion_betting_or_raising_to_amount

                if not isinstance(amount, (int, float)):
                    print(f"[Poker Engine] Error: LLM bet/raise without amount. Using min-raise.")
                    amount = min_bet

                clamped_amount = max(min_bet, min(amount, max_bet))

                if clamped_amount != amount:
                    print(f"[Poker Engine] LLM amount ({amount}) out of range. Clamping to: {clamped_amount}")

                state.complete_bet_or_raise_to(clamped_amount)
                is_raise = state.checking_or_calling_amount > 0
                return "raise" if is_raise else "bet", clamped_amount, message
            else:
                raise Exception("Cannot bet or raise")

        else:
            raise Exception(f"Unknown action: {action_str}")

    except Exception as e:
        print(f"[Poker Engine] Error: LLM action '{action_str}' failed ('{e}'). Using safe default.")
        return safe_default_action(state, f"Illegal move ({action_str}), auto-action.")


def safe_default_action(state: State, message: str) -> tuple:
    """
    Performs the safest legal action (Check or, if not possible, Fold).
    """
    if state.can_check_or_call and state.checking_or_calling_amount == 0:
        state.check_or_call()
        return "check", 0, message
    elif state.can_fold:
        state.fold()
        return "fold", 0, message
    else:
        print("[Poker Engine] CRITICAL: No safe action found! Player is all-in or similar.")
        return "error", 0, "No safe action"