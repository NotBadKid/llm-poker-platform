import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "poker_stats.db"


def init_db():
    """Inicjalizuje tabelę statystyk, jeśli nie istnieje."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabela przechowująca wynik każdego gracza w każdym rozdaniu
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
    Zapisuje listę wyników dla jednego rozdania.
    player_stats to lista słowników:
    [{'name': 'GPT-5', 'model': '...', 'temp': 0.7, 'before': 1000, 'after': 1200}, ...]
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


def get_aggregated_stats():
    """Zwraca statystyki zgrupowane po modelu i temperaturze."""
    conn = sqlite3.connect(DB_NAME)

    # Używamy pandas dla łatwiejszej agregacji (SQL też by dał radę, ale Pandas jest wygodniejszy)
    try:
        df = pd.read_sql_query("SELECT * FROM hand_results", conn)
        if df.empty:
            return {}

        # Grupowanie po Modelu
        model_stats = df.groupby('model_id').agg({
            'hand_number': 'count',  # Liczba rozegranych rozdań
            'net_change': 'sum',  # Całkowity zysk/strata żetonów
            'is_winner': 'sum'  # Ile razy wygrali rozdanie
        }).rename(columns={'hand_number': 'hands_played', 'net_change': 'total_profit', 'is_winner': 'hands_won'})

        # Obliczanie win-rate i średniego zysku na rękę
        model_stats['win_rate'] = (model_stats['hands_won'] / model_stats['hands_played']).round(2)
        model_stats['avg_profit_per_hand'] = (model_stats['total_profit'] / model_stats['hands_played']).round(2)

        return model_stats.to_dict('index')

    except Exception as e:
        print(f"Błąd analizy danych: {e}")
        return {}
    finally:
        conn.close()