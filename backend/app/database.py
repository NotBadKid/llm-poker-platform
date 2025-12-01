import sqlite3
import json
from datetime import datetime

DB_NAME = "poker_stats.db"


def init_db():
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



def create_new_game(game_id, config, players):
    """Create a new game entry."""
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
    """Saves single player action."""
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
                       json.dumps(hole_cards),
                       action,
                       amount,
                       message,
                       json.dumps(prompt_json),
                       datetime.now()
                   ))

    conn.commit()
    conn.close()
