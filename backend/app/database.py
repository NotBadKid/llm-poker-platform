import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "poker_stats.db"


def init_db():
    """Init if not exists and creates the hand_results table."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS games
                   (
                       game_id
                       TEXT
                       PRIMARY
                       KEY,
                       start_time
                       DATETIME,
                       end_time
                       DATETIME,
                       config
                       JSON,
                       players
                       JSON,
                       winner
                       TEXT
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
                       round_stage
                       player_name
                       TEXT,
                       model_id
                       TEXT,
                       hole_cards
                       TEXT, -- e.g. "['As', 'Kh']"
                       action
                       TEXT, -- "bet", "fold"
                       amount
                       INTEGER,
                       message
                       TEXT, -- model comment
                       prompt_sent
                       TEXT, -- full JSON prompt sent to LLM
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
                       BOOLEAN
                   )
                   ''')

    conn.commit()
    conn.close()


def save_hand_result(game_id, hand_num, player_stats):
    """
    Saves hand results.
    player_stats is a dict list like:
    [{'name': 'GPT-5', 'model': '...', 'temp': 0.7, 'before': 1000, 'after': 1200}, ...]
    """

def create_new_game(game_id, config, players):
    """Create a new game entry."""
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


def get_aggregated_stats():
    """Returns stats grouped by model and temperature."""
    conn = sqlite3.connect(DB_NAME)

    try:
        df = pd.read_sql_query("SELECT * FROM hand_results", conn)
        if df.empty:
            return {}

        # Group by model
        model_stats = df.groupby('model_id').agg({
            'hand_number': 'count',
            'net_change': 'sum',
            'is_winner': 'sum'
        }).rename(columns={'hand_number': 'hands_played', 'net_change': 'total_profit', 'is_winner': 'hands_won'})

        model_stats['win_rate'] = (model_stats['hands_won'] / model_stats['hands_played']).round(2)
        model_stats['avg_profit_per_hand'] = (model_stats['total_profit'] / model_stats['hands_played']).round(2)

        return model_stats.to_dict('index')

    except Exception as e:
        print(f"Data analysis error: {e}")
        return {}
    finally:
        conn.close()