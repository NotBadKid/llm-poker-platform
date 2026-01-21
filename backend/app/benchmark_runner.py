import time
import json
import random
import itertools
import uuid
from copy import deepcopy
from pokerkit import Card, Deck

# === IMPORTY APLIKACJI (DB INTEGRATION) ===
# Zakładam, że masz plik run.py lub app/__init__.py, który eksponuje obiekt 'app'
# Jeśli używasz factory pattern (create_app), odkomentuj odpowiednią linię.

try:
    from run import app  # Przypadek 1: Importujemy instancję app
except ImportError:
    from app import create_app  # Przypadek 2: Factory pattern

    app = create_app()

import app.database as db
# ==========================================

import config
from app.poker.poker_engine import play_single_hand, LLMFailure

# ==========================================
# CONFIGURATION
# ==========================================

API_KEYS = [
    # Wklej swoje klucze tutaj
    "sk-or-v1-...",
]

HAND_DELAY_SECONDS = 1
HANDS_PER_MATCH = 100
INITIAL_STACK = 10000
BLINDS = (50, 100)

PLAYERS = [
    {
        "id": "p1_conservative",
        "name": "Conservative Bot",
        "model": "mistralai/mistral-7b-instruct:free",
        "prompt": "You are a tight-passive player. Only play strong hands (Pairs, AK, AQ). Fold everything else.",
        "target_vpip": 15.0,
        "temperature": 0.7
    },
    {
        "id": "p2_aggressive",
        "name": "Aggressive Bot",
        "model": "mistralai/mistral-7b-instruct:free",
        "prompt": "You are a loose-aggressive player. Bet and raise often. Bluff when you sense weakness.",
        "target_vpip": 40.0,
        "temperature": 1.0
    },
    {
        "id": "p3_gto",
        "name": "GTO Bot",
        "model": "mistralai/mistral-7b-instruct:free",
        "prompt": "Play optimally based on GTO principles. Balance your range.",
        "target_vpip": 25.0,
        "temperature": 1.0
    },
    {
        "id": "p4_random",
        "name": "Wild Bot",
        "model": "mistralai/mistral-7b-instruct:free",
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

    def rotate_api_key(self):
        self.current_key_index = (self.current_key_index + 1) % len(API_KEYS)
        new_key = API_KEYS[self.current_key_index]
        config.OPENROUTER_API_KEY = new_key
        print(f"\n[System] 🔑 Rotating API Key. Using Key #{self.current_key_index + 1}")

    def generate_or_load_decks(self):
        try:
            with open(self.hand_scenarios_file, 'r') as f:
                raw_decks = json.load(f)
                self.decks = [[Card(c) for c in d] for d in raw_decks]
                print(f"[System] Loaded {len(self.decks)} decks from {self.hand_scenarios_file}")
        except FileNotFoundError:
            print(f"[System] Generating {HANDS_PER_MATCH} new decks...")
            self.decks = []
            raw_decks_to_save = []
            for _ in range(HANDS_PER_MATCH):
                deck = list(Deck.STANDARD)
                random.shuffle(deck)
                self.decks.append(deck)
                raw_decks_to_save.append([str(c) for c in deck])

            with open(self.hand_scenarios_file, 'w') as f:
                json.dump(raw_decks_to_save, f)
            print(f"[System] Decks saved to {self.hand_scenarios_file}")

    def run(self):
        # ### DB INTEGRATION: Otwieramy kontekst aplikacji
        with app.app_context():
            print("=" * 60)
            print("🚀 STARTING POKER BENCHMARK (Round Robin + DB Logging)")
            print("=" * 60)

            config.OPENROUTER_API_KEY = API_KEYS[0]
            self.generate_or_load_decks()

            pairs = list(itertools.combinations(PLAYERS, 2))
            total_matches = len(pairs)

            for idx, (p1, p2) in enumerate(pairs):
                print(f"\n🏆 MATCH {idx + 1}/{total_matches}: {p1['name']} vs {p2['name']}")
                self._play_match_series(p1, p2)

            self.calculate_and_print_metrics()

    def _play_match_series(self, p1_config, p2_config):

        def make_engine_player(p_conf):
            return {
                "name": p_conf['name'],
                "model_id": p_conf['model'],
                "user_prompt": p_conf['prompt'],
                "temperature": p_conf.get('temperature', 1.0)
            }

        player_a = make_engine_player(p1_config)
        player_b = make_engine_player(p2_config)

        # ### DB INTEGRATION: Tworzymy nową grę w bazie dla tego Meczu
        match_game_id = str(uuid.uuid4())
        match_config = {
            "initial_stack": INITIAL_STACK,
            "small_blind": BLINDS[0],
            "big_blind": BLINDS[1],
            "game_mode": "BENCHMARK_PAIR",
            "players": [player_a, player_b]
        }
        # Inicjalizacja wpisu w tabeli Games
        db.create_new_game(match_game_id, match_config, match_config['players'])
        print(f"  [DB] Created Match Game ID: {match_game_id}")

        automations = (
            Automation.ANTE_POSTING, Automation.BET_COLLECTION, Automation.BLIND_OR_STRADDLE_POSTING,
            Automation.CARD_BURNING, Automation.HOLE_DEALING, Automation.BOARD_DEALING,
            Automation.HOLE_CARDS_SHOWING_OR_MUCKING, Automation.HAND_KILLING,
            Automation.CHIPS_PUSHING, Automation.CHIPS_PULLING, Automation.RUNOUT_COUNT_SELECTION,
        )

        for i in range(HANDS_PER_MATCH):
            deck_scenario = self.decks[i]

            # --- PHASE A: Normal ---
            players_ordered = [player_a, player_b]
            player_map_a = {0: player_a, 1: player_b}
            ids_ordered_a = [p1_config['id'], p2_config['id']]

            print(f"  Hand {i + 1}/{HANDS_PER_MATCH} [Normal]...", end="\r")

            # Uruchamiamy rozdanie (przekazujemy match_game_id dla logów)
            result_a = self._execute_safe_hand(match_game_id, (i * 2) + 1, players_ordered, player_map_a, deck_scenario,
                                               automations)

            if result_a:
                self._update_stats(ids_ordered_a, result_a['hand_stats'])
            else:
                print(f"\n  [!] Hand {i + 1} [Normal] DISCARDED (Failed)")

            # --- PHASE B: Mirror ---
            deck_scenario_copy = list(deck_scenario)
            players_ordered_mirror = [player_b, player_a]
            player_map_b = {0: player_b, 1: player_a}
            ids_ordered_b = [p2_config['id'], p1_config['id']]

            # (i * 2) + 2 -> Numeracja rozdań w bazie: 1, 2, 3, 4... (Normal, Mirror, Normal, Mirror...)
            result_b = self._execute_safe_hand(match_game_id, (i * 2) + 2, players_ordered_mirror, player_map_b,
                                               deck_scenario_copy, automations)

            if result_b:
                self._update_stats(ids_ordered_b, result_b['hand_stats'])

            if HAND_DELAY_SECONDS > 0:
                time.sleep(HAND_DELAY_SECONDS)

    def _execute_safe_hand(self, game_id, hand_num, players_list, player_map, deck, automations):
        """
        Executes hand, handles retries, and SAVES TO DB if successful.
        """
        MAX_RETRIES = 3
        original_deck = list(deck)

        for attempt in range(MAX_RETRIES):
            try:
                stacks = [INITIAL_STACK, INITIAL_STACK]

                result = play_single_hand(
                    game_id=game_id,  # Przekazujemy ID meczu
                    player_map=player_map,
                    starting_stacks=stacks,
                    blinds=BLINDS,
                    automations=automations,
                    controller=None,
                    hand_number=hand_num,
                    deck=list(original_deck),
                    is_benchmark=True,
                    structured_output=True
                )

                # ### DB INTEGRATION: Zapisujemy logi i wyniki TYLKO jeśli się udało
                self._save_hand_to_db(game_id, hand_num, result, player_map, stacks)

                return result

            except LLMFailure:
                print(f"    [Error] LLM Failure. Retrying ({attempt + 1}/{MAX_RETRIES})...")
                self.rotate_api_key()
                time.sleep(2)
            except Exception as e:
                print(f"    [Error] Critical: {e}")
                self.rotate_api_key()
                time.sleep(2)

        return None

    def _save_hand_to_db(self, game_id, hand_num, result, player_map, initial_stacks):
        """
        Helper to interact with app.database
        """
        try:
            # 1. Zapisujemy logi akcji (Game Story)
            game_story = result.get("game_story", [])
            initial_hole_cards = result.get("initial_hole_cards", {})

            for event in game_story:
                # Odtwarzamy brakujące dane dla funkcji log_game_event
                # W story mamy nazwę gracza, musimy znaleźć model_id
                model_id = "unknown"
                hole_cards = []

                # Proste wyszukiwanie metadanych gracza po nazwie
                for idx, p_data in player_map.items():
                    if p_data['name'] == event['player']:
                        model_id = p_data['model_id']
                        # Pobieramy karty tego gracza (idx to local_index)
                        hole_cards = initial_hole_cards.get(idx, [])
                        break

                db.log_game_event(
                    game_id=game_id,
                    hand_num=hand_num,
                    player_name=event['player'],
                    model_id=model_id,
                    hole_cards=hole_cards,
                    action=event['action'],
                    amount=event['amount'],
                    message=event.get('comment', ''),
                    prompt_json={}  # Benchmark nie zapisuje pełnych promptów JSON dla oszczędności
                )

            # 2. Zapisujemy wynik finansowy (HandResult)
            hand_stats = result['hand_stats']
            final_stacks = result['final_stacks']

            db_stats_list = []
            for g_idx, stats in hand_stats.items():
                p_data = player_map[g_idx]
                db_stats_list.append({
                    'name': p_data['name'],
                    'model': p_data['model_id'],
                    'temp': p_data.get('temperature', 1.0),
                    'before': initial_stacks[g_idx],  # Always 10000 in duplicate
                    'after': final_stacks[g_idx]
                })

            db.save_hand_result(game_id, hand_num, db_stats_list)

        except Exception as e:
            print(f"    [DB Error] Failed to save hand {hand_num}: {e}")

    def _update_stats(self, player_ids, hand_stats):
        for seat_idx, p_id in enumerate(player_ids):
            s = hand_stats[seat_idx]
            self.results[p_id]["profit"] += s['profit']
            self.results[p_id]["hands_played"] += 1
            self.results[p_id]["errors"] += s['errors']
            self.results[p_id]["actions"] += s['actions_count']
            if s['vpip']: self.results[p_id]["vpip_count"] += 1

    def calculate_and_print_metrics(self):
        # ... (Ta metoda pozostaje bez zmian jak w poprzedniej wersji) ...
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
            vpip_target = data['target_vpip']

            metric_basic = bb_100 - (2 * error_rate)
            vpip_diff = abs(vpip_target - vpip_actual)
            metric_paqs = bb_100 - (2 * error_rate) - (2 * vpip_diff)

            name = [p['name'] for p in PLAYERS if p['id'] == p_id][0]
            print(
                f"{name:<20} | {bb_100:>9.2f} | {error_rate:>7.2f}% | {vpip_actual:>7.2f}% | {metric_basic:>8.2f} | {metric_paqs:>8.2f}")

        print("=" * 80)
        with open("benchmark_results.json", "w") as f:
            json.dump(self.results, f, indent=4)
        print("Detailed results saved to 'benchmark_results.json'")


if __name__ == "__main__":
    benchmark = PokerBenchmark()
    benchmark.run()