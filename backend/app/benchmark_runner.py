import time
import json
import random
import itertools
import uuid
import sys
from copy import deepcopy
from pokerkit import Card, Deck, Automation

# === DB INTEGRATION ===
try:
    from run import app
except ImportError:
    from app import create_app

    app = create_app()

import app.database as db
# ======================

import config
from app.poker.poker_engine import play_single_hand, LLMFailure

# ==========================================
# CONFIGURATION
# ==========================================

API_KEYS = [
    "",
]

HAND_DELAY_SECONDS = 0.5
HANDS_PER_MATCH = 2
INITIAL_STACK = 10000
BLINDS = (50, 100)

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


# ==========================================
# BENCHMARK ENGINE
# ==========================================

class PokerBenchmark:
    def __init__(self):
        self.decks = []
        self.results = {p['id']: {
            "profit": 0,
            "hands_played": 0,
            "errors": 0,
            "actions": 0,
            "vpip_count": 0,
            "target_vpip": p['target_vpip']
        } for p in PLAYERS}

        self.current_key_index = 0
        self.hand_scenarios_file = "benchmark_decks.json"
        self.results_file = "benchmark_results.json"

#     def rotate_api_key(self):
#         self.current_key_index = (self.current_key_index + 1) % len(API_KEYS)
#         config.OPENROUTER_API_KEY = API_KEYS[self.current_key_index]
#         print(f"\n[System] 🔑 Rotating Key. Using Key #{self.current_key_index + 1}")

    def generate_or_load_decks(self):
        try:
            with open(self.hand_scenarios_file, 'r') as f:
                raw_decks = json.load(f)
                self.decks = [[Card.parse(c) for c in d] for d in raw_decks]
                print(f"[System] Loaded {len(self.decks)} decks.")
        except FileNotFoundError:
            print(f"[System] Generating {HANDS_PER_MATCH} new decks...")
            self.decks = []
            raw_to_save = []
            for _ in range(HANDS_PER_MATCH):
                d = list(Deck.STANDARD)
                random.shuffle(d)
                self.decks.append(d)
                raw_to_save.append([str(c) for c in d])
            with open(self.hand_scenarios_file, 'w') as f:
                json.dump(raw_to_save, f)

    def save_results_to_file(self):
        """Zapisuje aktualny stan wyników do pliku JSON."""
        with open(self.results_file, "w") as f:
            json.dump(self.results, f, indent=4)

    def run(self):
        with app.app_context():
            print("=" * 60)
            print("STARTING BENCHMARK (Continuous Save Mode)")
            print("=" * 60)

            config.OPENROUTER_API_KEY = API_KEYS[0]
            self.generate_or_load_decks()

            pairs = list(itertools.combinations(PLAYERS, 2))
            total_matches = len(pairs)

            try:
                for idx, (p1, p2) in enumerate(pairs):
                    print(f"\n🏆 MATCH {idx + 1}/{total_matches}: {p1['name']} vs {p2['name']}")
                    self._play_match_series(p1, p2)

                    # === RAPORT CZĘŚCIOWY PO KAŻDYM MECZU ===
                    print(f"\n--- INTERMEDIATE RESULTS (After Match {idx + 1}) ---")
                    self.calculate_and_print_metrics()
                    # ========================================

            except KeyboardInterrupt:
                print("\n\n" + "!" * 60)
                print("🛑 USER INTERRUPT DETECTED (Ctrl+C)")
                print("Saving current progress and generating report...")
                print("!" * 60 + "\n")

            finally:
                self.calculate_and_print_metrics()
                print(f"\n[System] Final results saved to {self.results_file}")

    def _play_match_series(self, p1_config, p2_config):

        def make_player(p_conf):
            return {
                "name": p_conf['name'], "model_id": p_conf['model'],
                "user_prompt": p_conf['prompt'], "temperature": p_conf.get('temperature', 1.0)
            }

        player_a = make_player(p1_config)
        player_b = make_player(p2_config)

        match_game_id = str(uuid.uuid4())
        match_config = {
            "initial_stack": INITIAL_STACK, "small_blind": BLINDS[0], "big_blind": BLINDS[1],
            "game_mode": "BENCHMARK_PAIR", "players": [player_a, player_b]
        }
#         db.create_new_game(match_game_id, match_config, match_config['players'])
        print(f"  [DB] Match ID: {match_game_id}")

        automations = (
            Automation.ANTE_POSTING, Automation.BET_COLLECTION, Automation.BLIND_OR_STRADDLE_POSTING,
            Automation.CARD_BURNING, Automation.HOLE_DEALING, Automation.BOARD_DEALING,
            Automation.HOLE_CARDS_SHOWING_OR_MUCKING, Automation.HAND_KILLING,
            Automation.CHIPS_PUSHING, Automation.CHIPS_PULLING, Automation.RUNOUT_COUNT_SELECTION,
        )

        for i in range(HANDS_PER_MATCH):
            deck = self.decks[i]

            # Phase A: Normal
            print(f"  Hand {i + 1}/{HANDS_PER_MATCH} [Normal]...", end="\r")
            res_a = self._execute_safe_hand(match_game_id, (i * 2) + 1, [player_a, player_b],
                                            {0: player_a, 1: player_b}, deck, automations)
            if res_a:
                self._update_stats([p1_config['id'], p2_config['id']], res_a['hand_stats'])

            # Phase B: Mirror
            res_b = self._execute_safe_hand(match_game_id, (i * 2) + 2, [player_b, player_a],
                                            {0: player_b, 1: player_a}, list(deck), automations)
            if res_b:
                self._update_stats([p2_config['id'], p1_config['id']], res_b['hand_stats'])

            if HAND_DELAY_SECONDS > 0: time.sleep(HAND_DELAY_SECONDS)

    def _execute_safe_hand(self, gid, h_num, p_list, p_map, deck, autos):
            MAX_RETRIES = 3
            orig_deck = list(deck)

            for attempt in range(MAX_RETRIES):
                try:
                    stacks = [INITIAL_STACK, INITIAL_STACK]
                    # Tutaj wywołujemy silnik pokera
                    res = play_single_hand(gid, p_map, stacks, BLINDS, autos, None, h_num,
                                           list(orig_deck), is_benchmark=True, structured_output=True)

                    self._save_hand_to_db(gid, h_num, res, p_map, stacks)
                    return res

                except Exception as e:
                    # Tutaj usunęliśmy rotację kluczy, ale zostawiamy retry w razie błędu
                    print(f"    [Warning] Hand failed (Attempt {attempt+1}/{MAX_RETRIES}). Error: {e}")
                    time.sleep(2)

            print(f"    [Error] Failed hand {h_num} after {MAX_RETRIES} attempts.")
            return None

    def _save_hand_to_db(self, game_id, hand_num, result, player_map, initial_stacks):
        try:
            game_story = result.get("game_story", [])
            initial_hole_cards = result.get("initial_hole_cards", {})

            for event in game_story:
                model_id = "unknown"
                hole_cards = []
                for idx, p_data in player_map.items():
                    if p_data['name'] == event['player']:
                        model_id = p_data['model_id']
                        hole_cards = initial_hole_cards.get(idx, [])
                        break

#                 db.log_game_event(game_id, hand_num, event['player'], model_id, hole_cards,
#                                   event['action'], event['amount'], event.get('comment', ''), {})

            stats_list = []
            for g_idx, stats in result['hand_stats'].items():
                p_data = player_map[g_idx]
                stats_list.append({
                    'name': p_data['name'], 'model': p_data['model_id'],
                    'temp': p_data.get('temperature', 1.0),
                    'before': initial_stacks[g_idx], 'after': stats['final_stack']
                })
#             db.save_hand_result(game_id, hand_num, stats_list)
        except Exception as e:
            print(f"    [DB Error] {e}")

    def _update_stats(self, p_ids, h_stats):
        for s_idx, pid in enumerate(p_ids):
            s = h_stats[s_idx]
            self.results[pid]["profit"] += s['profit']
            self.results[pid]["hands_played"] += 1
            self.results[pid]["errors"] += s['errors']
            self.results[pid]["actions"] += s['actions_count']
            if s['vpip']: self.results[pid]["vpip_count"] += 1

        # === CONTINUOUS SAVE ===
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