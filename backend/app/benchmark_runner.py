import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import time
import json
import random
import itertools
import uuid
from copy import deepcopy
from pokerkit import Card, Deck, Automation

try:
    from run import app
except ImportError:
    from app import create_app

    app = create_app()

import app.database as db
import config
from app.poker.poker_engine import play_single_hand, LLMFailure

API_KEYS = [
    # Wklej swój klucz tutaj
    "",
]

HAND_DELAY_SECONDS = 0.5
INITIAL_STACK = 10000
BLINDS = (50, 100)

# Scenariusze wczytywane z pliku
SCENARIOS_FILE = "backend/example_hands.json"

PLAYERS = [
    {
        "id": "p1_conservative",
        "name": "Conservative Bot",
        "model": "mistralai/devstral-2512:free",
        "prompt": "You are a tight-passive player. Only play strong hands (Pairs, AK, AQ). Fold everything else.",
        "target_vpip": 15.0,
        "temperature": 0.7
    },
    {
        "id": "p2_aggressive",
        "name": "Aggressive Bot",
        "model": "mistralai/devstral-2512:free",
        "prompt": "You are a loose-aggressive player. Bet and raise often. Bluff when you sense weakness.",
        "target_vpip": 40.0,
        "temperature": 1.0
    },
    {
        "id": "p3_gto",
        "name": "GTO Bot",
        "model": "mistralai/devstral-2512:free",
        "prompt": "Play optimally based on GTO principles. Balance your range.",
        "target_vpip": 25.0,
        "temperature": 1.0
    },
    {
        "id": "p4_random",
        "name": "Wild Bot",
        "model": "mistralai/devstral-2512:free",
        "prompt": "Play unpredictably. Mix your strategies randomly.",
        "target_vpip": 50.0,
        "temperature": 1.2
    }
]


class PokerBenchmark:
    def __init__(self):
        self.scenarios = []
        self.results = {p['id']: {
            "profit": 0,
            "hands_played": 0,
            "errors": 0,
            "actions": 0,
            "vpip_count": 0,
            "target_vpip": p['target_vpip']
        } for p in PLAYERS}

        self.results_file = "benchmark_results.json"

    def load_scenarios_from_json(self):

        try:
            with open(SCENARIOS_FILE, 'r') as f:
                self.scenarios = json.load(f)
            print(f"[System] Loaded {len(self.scenarios)} scenarios from {SCENARIOS_FILE}.")
            print(f"Scenarios: {self.scenarios}")
        except FileNotFoundError:
            print(f"[Error] Could not find {SCENARIOS_FILE}. Please create it.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"[Error] Invalid JSON format in {SCENARIOS_FILE}.")
            sys.exit(1)

    def construct_rigged_deck(self, scenario, swap_players=False):
        """
        Creates a list of Cards in REVERSE dealing order to match PokerKit stack logic.
        """
        try:
            if not swap_players:
                p1_cards = [next(Card.parse(c)) for c in scenario['player_hand']]
                p2_cards = [next(Card.parse(c)) for c in scenario['opponent_hand']]
            else:
                p1_cards = [next(Card.parse(c)) for c in scenario['opponent_hand']]
                p2_cards = [next(Card.parse(c)) for c in scenario['player_hand']]

            board_flop = [next(Card.parse(c)) for c in scenario['flop']]
            board_turn = [next(Card.parse(c)) for c in scenario['turn']]
            board_river = [next(Card.parse(c)) for c in scenario['river']]

            used_cards = set(p1_cards + p2_cards + board_flop + board_turn + board_river)

            full_deck = list(Deck.STANDARD)
            filler_cards = [c for c in full_deck if c not in used_cards]
            random.shuffle(filler_cards)

            deal_sequence = []

            # Preflop
            deal_sequence.append(p1_cards[0])
            deal_sequence.append(p2_cards[0])
            deal_sequence.append(p1_cards[1])
            deal_sequence.append(p2_cards[1])

            # Flop (Burn + 3)
            deal_sequence.append(filler_cards.pop())
            deal_sequence.extend(board_flop)

            # Turn (Burn + 1)
            deal_sequence.append(filler_cards.pop())
            deal_sequence.extend(board_turn)

            # River (Burn + 1)
            deal_sequence.append(filler_cards.pop())
            deal_sequence.extend(board_river)

            final_deck = filler_cards

            for card in reversed(deal_sequence):
                final_deck.append(card)

            return final_deck

        except Exception as e:
            print(f"[Error] Failed to construct deck for scenario: {e}")
            return None

    def save_results_to_file(self):
        with open(self.results_file, "w") as f:
            json.dump(self.results, f, indent=4)

    def run(self):
        with app.app_context():
            print("=" * 60)
            print("STARTING SCENARIO BENCHMARK (Duplicate Poker)")
            print("=" * 60)

            if API_KEYS:
                config.OPENROUTER_API_KEY = API_KEYS[0]

            self.load_scenarios_from_json()

            hands_count = len(self.scenarios)
            pairs = list(itertools.combinations(PLAYERS, 2))
            total_matches = len(pairs)

            try:
                for idx, (p1, p2) in enumerate(pairs):
                    print(f"\n🏆 MATCH {idx + 1}/{total_matches}: {p1['name']} vs {p2['name']}")
                    self._play_match_series(p1, p2, hands_count)

                    print(f"\n--- INTERMEDIATE RESULTS (After Match {idx + 1}) ---")
                    self.calculate_and_print_metrics()

            except KeyboardInterrupt:
                print("\n\n" + "!" * 60)
                print("🛑 USER INTERRUPT DETECTED")
                print("!" * 60 + "\n")

            finally:
                self.calculate_and_print_metrics()
                print(f"\n[System] Final results saved to {self.results_file}")

    def _play_match_series(self, p1_config, p2_config, hands_count):

        def make_player(p_conf):
            return {
                "name": p_conf['name'], "model_id": p_conf['model'],
                "user_prompt": p_conf['prompt'], "temperature": p_conf.get('temperature', 1.0)
            }

        player_a = make_player(p1_config)
        player_b = make_player(p2_config)

        match_game_id = "bench_" + str(uuid.uuid4())[:8]
        # db.create_new_game(...)

        automations = (
            Automation.ANTE_POSTING, Automation.BET_COLLECTION, Automation.BLIND_OR_STRADDLE_POSTING,
            Automation.CARD_BURNING, Automation.HOLE_DEALING, Automation.BOARD_DEALING,
            Automation.HOLE_CARDS_SHOWING_OR_MUCKING, Automation.HAND_KILLING,
            Automation.CHIPS_PUSHING, Automation.CHIPS_PULLING, Automation.RUNOUT_COUNT_SELECTION,
        )

        for i in range(hands_count):
            scenario = self.scenarios[i]

            # --- PHASE A: Normal ---
            rigged_deck_a = self.construct_rigged_deck(scenario, swap_players=False)
            if not rigged_deck_a: continue

            print(f"  Hand {i + 1}/{hands_count} [Normal]...", end="\r")
            res_a = self._execute_safe_hand(match_game_id, (i * 2) + 1, [player_a, player_b],
                                            {0: player_a, 1: player_b}, rigged_deck_a, automations)
            if res_a:
                self._update_stats([p1_config['id'], p2_config['id']], res_a['hand_stats'])

            # --- PHASE B: Mirror ---
            rigged_deck_b = self.construct_rigged_deck(scenario, swap_players=True)
            if not rigged_deck_b: continue

            res_b = self._execute_safe_hand(match_game_id, (i * 2) + 2, [player_b, player_a],
                                            {0: player_b, 1: player_a}, rigged_deck_b, automations)
            if res_b:
                self._update_stats([p2_config['id'], p1_config['id']], res_b['hand_stats'])

            if HAND_DELAY_SECONDS > 0: time.sleep(HAND_DELAY_SECONDS)

    def _execute_safe_hand(self, gid, h_num, p_list, p_map, deck, autos):
        MAX_RETRIES = 3
        orig_deck = list(deck)

        for attempt in range(MAX_RETRIES):
            try:
                stacks = [INITIAL_STACK, INITIAL_STACK]
                res = play_single_hand(gid, p_map, stacks, BLINDS, autos, None, h_num,
                                       list(orig_deck), is_benchmark=True, structured_output=True)
                return res

            except Exception as e:
                print(f"    [Warning] Hand failed (Attempt {attempt + 1}/{MAX_RETRIES}). Error: {e}")
                time.sleep(2)

        print(f"    [Error] Failed hand {h_num} after {MAX_RETRIES} attempts.")
        return None

    def _save_hand_to_db(self, game_id, hand_num, result, player_map, initial_stacks):
        pass

    def _update_stats(self, p_ids, h_stats):
        for s_idx, pid in enumerate(p_ids):
            s = h_stats[s_idx]
            self.results[pid]["profit"] += s['profit']
            self.results[pid]["hands_played"] += 1
            self.results[pid]["errors"] += s['errors']
            self.results[pid]["actions"] += s['actions_count']
            if s['vpip']: self.results[pid]["vpip_count"] += 1
        self.save_results_to_file()

    def calculate_and_print_metrics(self):
        print("\n" + "=" * 80)
        print(f"{'PLAYER':<20} | {'BB/100':<10} | {'ERR %':<8} | {'VPIP %':<8} | {'BASIC':<8} | {'PAQS':<8}")
        print("-" * 80)

        for p_id, data in self.results.items():
            hands = data['hands_played']
            if hands == 0:
                print(f"{p_id:<20} | NO DATA")
                continue

            bb_val = BLINDS[1]
            total_bb_profit = data['profit'] / bb_val
            bb_100 = (total_bb_profit / hands) * 100

            actions = max(data['actions'], 1)
            error_rate = (data['errors'] / actions) * 100

            vpip_actual = (data['vpip_count'] / hands) * 100
            vpip_diff = abs(data['target_vpip'] - vpip_actual)

            metric_basic = bb_100 - (2 * error_rate)
            metric_paqs = bb_100 - (2 * error_rate) - (2 * vpip_diff)

            name = [p['name'] for p in PLAYERS if p['id'] == p_id][0]
            print(
                f"{name:<20} | {bb_100:>9.2f} | {error_rate:>7.2f}% | {vpip_actual:>7.2f}% | {metric_basic:>8.2f} | {metric_paqs:>8.2f}")
        print("=" * 80)


if __name__ == "__main__":
    benchmark = PokerBenchmark()
    benchmark.run()