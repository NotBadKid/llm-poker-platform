import sqlite3
import json
import pandas as pd
from datetime import datetime

DB_NAME = "poker_stats.db"


def init_db():
    """
    Creates tabel if not exist.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Tabela gier (Sesje) - Przechowuje ogólne informacje o uruchomionej grze
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS games
                   (
                       game_id
                       TEXT
                       PRIMARY
                       KEY,
                       start_time
                       DATETIME,
                       config
                       JSON,
                       players
                       JSON
                   )
                   ''')

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS game_logs
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       game_id
                       TEXT,
                       hand_number
                       INTEGER,
                       player_name
                       TEXT,
                       model_id
                       TEXT,
                       hole_cards
                       TEXT, -- Karty gracza w momencie decyzji (np. "['As', 'Kh']")
                       action
                       TEXT, -- np. "bet", "fold"
                       amount
                       INTEGER,
                       message
                       TEXT, -- komentarz (reasoning) modelu
                       prompt_sent
                       TEXT, -- pełny prompt JSON wysłany do modelu (dla debugowania)
                       timestamp
                       DATETIME,
                       FOREIGN
                       KEY
                   (
                       game_id
                   ) REFERENCES games
                   (
                       game_id
                   )
                       )
                   ''')

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS hand_results
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       timestamp
                       DATETIME,
                       game_id
                       TEXT,
                       hand_number
                       INTEGER,
                       player_name
                       TEXT,
                       model_id
                       TEXT,
                       temperature
                       REAL,
                       chips_before
                       INTEGER,
                       chips_after
                       INTEGER,
                       net_change
                       INTEGER,
                       is_winner
                       BOOLEAN,
                       FOREIGN
                       KEY
                   (
                       game_id
                   ) REFERENCES games
                   (
                       game_id
                   )
                       )
                   ''')

    conn.commit()
    conn.close()



def create_new_game(game_id, config, players):
    """
    Saves new game data.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
                   INSERT INTO games (game_id, start_time, config, players)
                   VALUES (?, ?, ?, ?)
                   ''', (
                       game_id,
                       datetime.now(),
                       json.dumps(config),
                       json.dumps(players)
                   ))

    conn.commit()
    conn.close()


def log_game_event(game_id, hand_num, player_name, model_id, hole_cards, action, amount, message, prompt_json):
    """
    Saves single player action log.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
                   INSERT INTO game_logs
                   (game_id, hand_number, player_name, model_id, hole_cards, action, amount, message, prompt_sent,
                    timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ''', (
                       game_id,
                       hand_num,
                       player_name,
                       model_id,
                       json.dumps(hole_cards),  # Serializacja listy kart do stringa
                       action,
                       amount,
                       message,
                       json.dumps(prompt_json),  # Serializacja promptu
                       datetime.now()
                   ))

    conn.commit()
    conn.close()


def save_hand_result(game_id, hand_num, player_stats):
    """
    Saves data about players after hand.
    player_stats is a list of dicts:
    [{'name': '...', 'model': '...', 'temp': 1.0, 'before': 1000, 'after': 1200}, ...]
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    timestamp = datetime.now()

    for p in player_stats:
        net_change = p['after'] - p['before']
        is_winner = net_change > 0

        cursor.execute('''
                       INSERT INTO hand_results
                       (timestamp, game_id, hand_number, player_name, model_id, temperature,
                        chips_before, chips_after, net_change, is_winner)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ''', (
                           timestamp, game_id, hand_num, p['name'], p['model'], p.get('temp', 1.0),
                           p['before'], p['after'], net_change, is_winner
                       ))

    conn.commit()
    conn.close()


# --- Funkcje Odczytu (Statystyki) ---

def get_aggregated_stats():
    """
    Gets model stats from the start (whole history).
    """
    conn = sqlite3.connect(DB_NAME)

    try:
        df = pd.read_sql_query("SELECT * FROM hand_results", conn)

        if df.empty:
            return {}

        # Group by model (can be changed to ['model_id', 'temperature'] for more detailed analysis)
        model_stats = df.groupby('model_id').agg({
            'hand_number': 'count',
            'net_change': 'sum',
            'is_winner': 'sum'
        }).rename(columns={
            'hand_number': 'hands_played',
            'net_change': 'total_profit',
            'is_winner': 'hands_won'
        })

        # Win Rate: % of all won hands
        model_stats['win_rate'] = (model_stats['hands_won'] / model_stats['hands_played']).round(2)

        # Avg Profit (for single hand)
        model_stats['avg_profit_per_hand'] = (model_stats['total_profit'] / model_stats['hands_played']).round(2)

        return model_stats.to_dict('index')

    except Exception as e:
        print(f"Data analysis error in get_aggregated_stats: {e}")
        return {}
    finally:
        conn.close()