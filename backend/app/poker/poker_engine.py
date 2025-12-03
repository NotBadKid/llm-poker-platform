import time
from math import inf
import json
import uuid
from pokerkit import Automation, Mode, NoLimitTexasHoldem
from pokerkit.state import State
import app.llm_manager as llm_manager
import app.state_broadcaster as broadcaster
import app.database as db


def card_to_str(card):
    """ Safely converts a pokerkit card object to a string (e.g., 'As', 'Td'). """
    return str(card) if card else None


def start_game_session(game_config: dict):
    """
    Main function called by /game/start in a separate thread.
    Runs and manages the full poker game session.
    """
    print(f"[Poker Engine] Initializing statistics database...")
    db.init_db()

    game_id = str(uuid.uuid4())
    print(f"[Poker Engine] Starting game {game_id} with config: {game_config}")

    try:
        players_info = [
            {'name': p['name'], 'model': p['model_id'], 'temp': p.get('temperature', 1.0)}
            for p in game_config['players']
        ]
        db.create_new_game(game_id, game_config, players_info)
    except Exception as e:
        print(f"[Poker Engine] Error saving game info: {e}")

    # --- 1. Game Setup ---
    # We maintain a master list of players to keep indices consistent
    master_player_list = list(game_config['players'])

    # We maintain master stacks. If a player busts, their stack here becomes 0.
    master_stacks = list([game_config.get('initial_stack', 10000)] * len(master_player_list))

    blinds = (game_config.get('small_blind', 10), game_config.get('big_blind', 20))
    big_blind = blinds[1]

    automations_tuple = (
        Automation.ANTE_POSTING,
        Automation.BET_COLLECTION,
        Automation.BLIND_OR_STRADDLE_POSTING,
        Automation.HOLE_DEALING,
        Automation.HAND_KILLING,
        Automation.CHIPS_PUSHING,
        Automation.CHIPS_PULLING,
    )

    max_hands_to_play = game_config.get('number_of_hands')
    hands_played = 0

    # --- 2. Main Game Loop ---
    while True:
        if max_hands_to_play is not None and hands_played >= max_hands_to_play:
            print(f"[Poker Engine] Game over: Reached hand limit of {max_hands_to_play}.")
            break

        # [FIX] Filter Active Players (Survivors)
        # We find indices of players who still have chips
        active_indices = [i for i, stack in enumerate(master_stacks) if stack > 0]

        # Check Bankruptcy
        if len(active_indices) <= 1:
            print("[Poker Engine] Game over: Only one player has chips remaining.")
            break

        # Prepare stacks just for this hand
        current_hand_stacks = tuple(master_stacks[i] for i in active_indices)
        player_count = len(active_indices)

        # [DB] Store stacks before hand for stats
        stacks_before_hand = list(master_stacks)

        hands_played += 1
        game_story = []
        chat_log = []
        last_event = None

        print(f"\n[Poker Engine] New hand started (#{hands_played}). Survivors: {len(active_indices)}")

        state = NoLimitTexasHoldem.create_state(
            automations_tuple,
            False,  # uniform_antes
            {},  # antes
            blinds,
            big_blind,
            current_hand_stacks,
            player_count,
            mode=Mode.CASH_GAME
        )

        # --- 3. Hand Loop ---
        while state.status:
            # [CRITICAL FIX] Manual Dealing Logic
            # Because we disabled automation, we must check if we need to burn/deal.
            # This handles the All-in situations correctly.

            if state.can_burn_card():
                state.burn_card()
                # No broadcast needed just for burn
                continue

            if state.can_deal_board():
                state.deal_board()
                # Broadcast the new card(s) (Flop/Turn/River)
                frontend_state = build_frontend_state(state, master_player_list, active_indices, chat_log, None)
                broadcaster.broadcast_game_state(frontend_state)
                time.sleep(1.0)  # Wait so users can see the card
                continue

            if state.can_show_or_muck_hole_cards():
                state.show_or_muck_hole_cards()
                continue

            # Standard Actor Logic
            # We map the relative 'actor_index' (0..survivors) back to the original list
            relative_actor_index = state.actor_index

            if relative_actor_index is not None:
                original_player_index = active_indices[relative_actor_index]
                player_data = master_player_list[original_player_index]

                print(f"[Poker Engine] Player to move: {player_data['name']} (Index: {original_player_index})")

                # --- 4. Prompt ---
                prompt_json = build_llm_prompt(state, relative_actor_index, master_player_list, active_indices,
                                               game_story)
                user_strategy = player_data.get('user_prompt')
                user_temperature = player_data.get('temperature', 1.0)

                # --- 5. LLM Call ---
                action_response = llm_manager.get_llm_action(
                    model_id=player_data['model_id'],
                    prompt_json=prompt_json,
                    user_prompt=user_strategy,
                    temperature=user_temperature
                )

                # --- 6. Validate ---
                action_str, amount_validated, message = validate_and_execute_action(
                    state,
                    action_response
                )

                # [DB] Log Event
                try:
                    # Use full string for DB, sliced for Frontend
                    current_hole_cards = [card_to_str(c) for c in state.hole_cards[relative_actor_index]]
                    db.log_game_event(
                        game_id=game_id,
                        hand_num=hands_played,
                        player_name=player_data['name'],
                        model_id=player_data['model_id'],
                        hole_cards=current_hole_cards,
                        action=action_str,
                        amount=amount_validated,
                        message=message,
                        prompt_json=prompt_json
                    )
                except Exception as e:
                    print(f"[Poker Engine] Logging error: {e}")

                print(f"[Poker Engine] LLM ({player_data['name']}) chose: {action_str}, Value: {amount_validated}")

                # --- 7. History ---
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

                # --- 8. Broadcast ---
                frontend_state = build_frontend_state(state, master_player_list, active_indices, chat_log, last_event)
                broadcaster.broadcast_game_state(frontend_state)
                time.sleep(0.5)

            else:
                # If no actor and no dealing possible, break to avoid infinite loop
                if not state.status:
                    break

        # --- 10. End of Hand ---
        print("[Poker Engine] Hand finished. Settling pot.")

        # Update Master Stacks based on results
        for rel_i, stack_val in enumerate(state.stacks):
            orig_i = active_indices[rel_i]
            master_stacks[orig_i] = stack_val

        # [DB] Save Stats
        try:
            stats_data = []
            for i in range(len(master_player_list)):
                p_data = master_player_list[i]
                stats_data.append({
                    'name': p_data['name'],
                    'model': p_data['model_id'],
                    'temp': p_data.get('temperature', 1.0),
                    'before': stacks_before_hand[i],
                    'after': master_stacks[i]
                })
            db.save_hand_result(game_id, hands_played, stats_data)
            print(f"[Poker Engine] Stats saved for hand {hands_played}")
        except Exception as e:
            print(f"[Poker Engine] Error saving stats: {e}")

        final_state = build_frontend_state(state, master_player_list, active_indices, chat_log, last_event,
                                           hand_over=True)
        broadcaster.broadcast_game_state(final_state)

        # Check if we should pause (if game not over)
        check_survivors = sum(1 for s in master_stacks if s > 0)
        if check_survivors > 1 and (max_hands_to_play is None or hands_played < max_hands_to_play):
            print(f"[Poker Engine] Next hand in 5 seconds...")
            time.sleep(5)

    print("[Poker Engine] Final game state. Session ended.")


def build_llm_prompt(state: State, rel_index: int, master_player_list: list, active_indices: list,
                     game_story: list) -> dict:
    """
    Creates prompt. 'rel_index' is the index in the current 'state' (0..active-1).
    """
    # Map back to original data
    orig_index = active_indices[rel_index]
    player_data = master_player_list[orig_index]

    hole_cards = [card_to_str(c) for c in state.hole_cards[rel_index]]

    board_cards = []
    if state.board_cards:
        # Accessing [0] because board_cards is list of lists
        board_cards = [card_to_str(c) for c in state.board_cards[0]]

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

    # Opponents
    opponents = []
    for i in range(state.player_count):
        if i == rel_index: continue

        opp_orig_idx = active_indices[i]
        opponent_data = master_player_list[opp_orig_idx]
        is_active = state.statuses[i]

        opponents.append({
            "name": opponent_data['name'],
            "stack": state.stacks[i],
            "position": "Unknown",
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
        "your_stack": state.stacks[rel_index],
        "bet_to_call": state.checking_or_calling_amount,
        "min_raise": state.min_completion_betting_or_raising_to_amount,
        "max_raise": state.max_completion_betting_or_raising_to_amount,
        "game_story": game_story
    }

    return prompt


def build_frontend_state(state: State, master_player_list: list, active_indices: list, chat_log: list, last_event: dict,
                         hand_over: bool = False) -> dict:
    """
    Creates JSON for frontend. Reconstructs full player list (including busted ones).
    """
    board_cards = []
    if state.board_cards:
        # [USER LOGIC] Slicing string [-3:-1]
        board_cards = [card_to_str(c)[-3:-1] if card_to_str(c) else None for c in state.board_cards[0]]

    community_cards = board_cards + [None] * (5 - len(board_cards))

    players_frontend = []

    # Map: Original Index -> Relative Index (if active)
    orig_to_rel = {orig: rel for rel, orig in enumerate(active_indices)}

    for i in range(len(master_player_list)):
        p_data = master_player_list[i]

        # Defaults for busted players
        p_stack = 0
        p_bet = 0
        p_cards = [None, None]
        p_status = "out"

        if i in orig_to_rel:
            rel_idx = orig_to_rel[i]
            p_stack = state.stacks[rel_idx]
            p_bet = state.bets[rel_idx]
            is_active = state.statuses[rel_idx]
            p_status = "playing" if is_active else "folded"

            # [USER LOGIC] Slicing string [-3:-1]
            c_str = [card_to_str(c) for c in state.hole_cards[rel_idx]]
            raw_cards = [s[-3:-1] if s else None for s in c_str]

            if is_active or (hand_over and not is_active):
                p_cards = raw_cards

            if not is_active and not hand_over:
                p_cards = [None, None]

        players_frontend.append({
            "name": p_data['name'],
            "chipCount": p_stack,
            "currentBet": p_bet,
            "holeCards": p_cards,
            "status": p_status
        })

    active_player_name = None
    if state.status and state.actor_index is not None:
        rel_idx = state.actor_index
        orig_idx = active_indices[rel_idx]
        active_player_name = master_player_list[orig_idx]['name']

    state_json = {
        "pot": state.total_pot_amount,
        "communityCards": community_cards,
        "players": players_frontend,
        "activePlayerId": active_player_name,
        "chatLog": chat_log,
        "lastEvent": last_event
    }

    return state_json


def validate_and_execute_action(state: State, llm_response: dict | None) -> tuple:
    """
    Validates and executes LLM action.
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
    if state.can_check_or_call and state.checking_or_calling_amount == 0:
        state.check_or_call()
        return "check", 0, message
    elif state.can_fold:
        state.fold()
        return "fold", 0, message
    else:
        print("[Poker Engine] CRITICAL: No safe action found! Player is all-in or similar.")
        return "error", 0, "No safe action"