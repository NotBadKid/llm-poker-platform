import sys
import os

# ==========================================
# PATH FIX (DODAJ TO NA SAMĄ GÓRĘ)
# ==========================================
# Pobieramy ścieżkę do folderu, w którym jest ten plik (backend/app)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Pobieramy ścieżkę do folderu nadrzędnego (backend)
parent_dir = os.path.dirname(current_dir)
# Dodajemy 'backend' do ścieżek, gdzie Python szuka modułów
sys.path.append(parent_dir)
# ==========================================

import time
import json
import random
import itertools
import uuid
from copy import deepcopy
from pokerkit import Card, Deck, Automation

# === DB INTEGRATION ===
try:
    # Teraz to zadziała, bo Python widzi folder 'backend'
    from run import app
except ImportError:
    from app import create_app
    app = create_app()

import app.database as db
# ======================

import config
# Zauważ zmianę importu poniżej - skoro jesteśmy w 'app', importujemy z 'poker'
from app.poker.poker_engine import play_single_hand, LLMFailure


# ==========================================
# CONFIGURATION
# ==========================================

API_KEYS = [
    # Tutaj Twój klucz (bez rotacji)
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


# ==========================================
# BENCHMARK ENGINE
# ==========================================

class PokerBenchmark:
    def __init__(self):
        self.scenarios = []  # Lista słowników ze scenariuszami
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
        """Wczytuje scenariusze z pliku scenarios.json"""
        try:
            with open(SCENARIOS_FILE, 'r') as f:
                self.scenarios = json.load(f)
            print(f"[System] Loaded {len(self.scenarios)} scenarios from {SCENARIOS_FILE}.")
            print(f"Scenarios: {self.scenarios}")
        except FileNotFoundError:
            print(f"[Error] Could not find {SCENARIOS_FILE}. Please provide the file.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"[Error] Invalid JSON format in {SCENARIOS_FILE}.")
            sys.exit(1)

    def construct_rigged_deck(self, scenario, swap_players=False):
        """
        Tworzy talię (listę obiektów Card) ułożoną tak, aby PokerKit rozdał
        dokładnie karty ze scenariusza.

        Kolejność rozdawania w PokerKit (2 graczy):
        1. P1 Card 1
        2. P2 Card 1
        3. P1 Card 2
        4. P2 Card 2
        5. Burn Card (jeśli Automation.CARD_BURNING jest włączone)
        6. Flop (3 karty)
        7. Burn Card
        8. Turn
        9. Burn Card
        10. River

        Talia w PokerKit jest "stosem", więc pobiera się z KOŃCA listy (pop()).
        Musimy więc zbudować listę w ODWRÓCONEJ kolejności rozdawania.
        """

        # 1. Parsowanie kart ze scenariusza
        if not swap_players:
            p1_cards = [next(Card.parse(c)) for c in scenario['player_hand']]
            p2_cards = [next(Card.parse(c)) for c in scenario['opponent_hand']]
        else:
            # Mirror Match: Zamieniamy ręce
            p1_cards = [next(Card.parse(c)) for c in scenario['opponent_hand']]
            p2_cards = [next(Card.parse(c)) for c in scenario['player_hand']]

        board_flop = [next(Card.parse(c)) for c in scenario['flop']]
        board_turn = [next(Card.parse(c)) for c in scenario['turn']]
        board_river = [next(Card.parse(c)) for c in scenario['river']]

        # Zbieramy wszystkie użyte karty, żeby nie użyć ich jako "Burn" ani w reszcie talii
        used_cards = set(p1_cards + p2_cards + board_flop + board_turn + board_river)

        # 2. Tworzymy pulę dostępnych kart "wypełniaczy" (do Burn i reszty talii)
        full_deck = list(Deck.STANDARD)
        filler_cards = [c for c in full_deck if c not in used_cards]
        random.shuffle(filler_cards)

        # 3. Budujemy stos rozdawania (Sequence of dealing)
        deal_sequence = []

        # Preflop (P1_1, P2_1, P1_2, P2_2)
        # Zakładamy 2 graczy. Seat 0 (P1), Seat 1 (P2).
        # Kolejność w PokerKit: Seat 0, Seat 1, Seat 0, Seat 1.
        deal_sequence.append(p1_cards[0])
        deal_sequence.append(p2_cards[0])
        deal_sequence.append(p1_cards[1])
        deal_sequence.append(p2_cards[1])

        # Flop (Burn + 3)
        deal_sequence.append(filler_cards.pop())  # Burn 1
        deal_sequence.extend(board_flop)

        # Turn (Burn + 1)
        deal_sequence.append(filler_cards.pop())  # Burn 2
        deal_sequence.extend(board_turn)

        # River (Burn + 1)
        deal_sequence.append(filler_cards.pop())  # Burn 3
        deal_sequence.extend(board_river)

        # 4. Tworzymy ostateczną talię (Lista)
        # Talia = [Reszta kart] + [Odwrócona sekwencja rozdawania]
        # Dzięki temu pop() zwróci najpierw deal_sequence[0], potem [1]...

        # Najpierw wrzucamy resztę nieużywanych kart na spód talii
        final_deck = filler_cards

        # Potem wrzucamy sekwencję w ODWRÓCONEJ kolejności na górę
        # (bo pop() bierze z końca, a chcemy by wzięło first dealt card)
        for card in reversed(deal_sequence):
            final_deck.append(card)

        return final_deck

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

            # Liczba rozdań zależy od pliku JSON, a nie stałej HANDS_PER_MATCH
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

        # Baza danych (Zakomentowane)
        # match_game_id = str(uuid.uuid4())
        # match_config = { ... }
        # db.create_new_game(...)
        match_game_id = "test_match_id"  # Placeholder

        automations = (
            Automation.ANTE_POSTING, Automation.BET_COLLECTION, Automation.BLIND_OR_STRADDLE_POSTING,
            Automation.CARD_BURNING, Automation.HOLE_DEALING, Automation.BOARD_DEALING,
            Automation.HOLE_CARDS_SHOWING_OR_MUCKING, Automation.HAND_KILLING,
            Automation.CHIPS_PUSHING, Automation.CHIPS_PULLING, Automation.RUNOUT_COUNT_SELECTION,
        )

        for i in range(hands_count):
            scenario = self.scenarios[i]

            # --- PHASE A: Normal ---
            # Budujemy talię: P1 dostaje player_hand, P2 dostaje opponent_hand
            rigged_deck_a = self.construct_rigged_deck(scenario, swap_players=False)

            print(f"  Hand {i + 1}/{hands_count} [Normal]...", end="\r")
            res_a = self._execute_safe_hand(match_game_id, (i * 2) + 1, [player_a, player_b],
                                            {0: player_a, 1: player_b}, rigged_deck_a, automations)
            if res_a:
                self._update_stats([p1_config['id'], p2_config['id']], res_a['hand_stats'])

            # --- PHASE B: Mirror ---
            # Budujemy talię: P1 dostaje opponent_hand, P2 dostaje player_hand
            # WAŻNE: Tutaj zamieniamy karty w talii, ale gracze przy stole (player_map) siedzą tak samo!
            # Seat 0 = P2 (Player B), Seat 1 = P1 (Player A)
            # Więc Seat 0 musi dostać "player_hand" (bo to teraz rola Bota B), a Seat 1 "opponent_hand".
            # Funkcja construct_rigged_deck z swap_players=True zamienia przypisanie kart do Seat 0 i Seat 1.

            rigged_deck_b = self.construct_rigged_deck(scenario, swap_players=True)

            # Seat 0: Player B, Seat 1: Player A
            res_b = self._execute_safe_hand(match_game_id, (i * 2) + 2, [player_b, player_a],
                                            {0: player_b, 1: player_a}, rigged_deck_b, automations)
            if res_b:
                self._update_stats([p2_config['id'], p1_config['id']], res_b['hand_stats'])

            if HAND_DELAY_SECONDS > 0: time.sleep(HAND_DELAY_SECONDS)

    def _execute_safe_hand(self, gid, h_num, p_list, p_map, deck, autos):
        MAX_RETRIES = 3
        # Deck musi być kopią, bo PokerKit go "zużywa"
        orig_deck = list(deck)

        for attempt in range(MAX_RETRIES):
            try:
                stacks = [INITIAL_STACK, INITIAL_STACK]
                res = play_single_hand(gid, p_map, stacks, BLINDS, autos, None, h_num,
                                       list(orig_deck), is_benchmark=True, structured_output=True)

                # self._save_hand_to_db(gid, h_num, res, p_map, stacks)
                return res

            except Exception as e:
                print(f"    [Warning] Hand failed (Attempt {attempt + 1}/{MAX_RETRIES}). Error: {e}")
                time.sleep(2)

        print(f"    [Error] Failed hand {h_num} after {MAX_RETRIES} attempts.")
        return None

    def _save_hand_to_db(self, game_id, hand_num, result, player_map, initial_stacks):
        # ... (Zakomentowana logika bazy danych - pozostawiona bez zmian) ...
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