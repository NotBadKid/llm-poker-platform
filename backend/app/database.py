import json
import pandas as pd
from datetime import datetime
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON

# ----------------------------------------------------
# 1. DATABASE CONFIGURATION
# ----------------------------------------------------

#urls goes here
DB_USER = ""
DB_PASSWORD = ""
DB_HOST = ""
DB_NAME = ""
DB_PORT = ""

# Full Connection URI
DATABASE_URI = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
)

# Initialize the SQLAlchemy object (unbound initially)
db = SQLAlchemy()


class Config:
    SQLALCHEMY_DATABASE_URI = DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "super_tajny_klucz_lokalny")


# We create a simple Flask app context to allow SQLAlchemy to function without a full web server setup
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


# ----------------------------------------------------
# 2. DATABASE MODELS (ORM)
# ----------------------------------------------------

class Game(db.Model):
    __tablename__ = 'games'

    game_id = db.Column(db.String(50), primary_key=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    config = db.Column(JSON)  # Using JSON type for PostgreSQL
    players = db.Column(JSON)  # Using JSON type for PostgreSQL

    # Relationships (Optional, for easier navigation)
    logs = db.relationship('GameLog', backref='game', lazy=True)
    results = db.relationship('HandResult', backref='game', lazy=True)


class GameLog(db.Model):
    __tablename__ = 'game_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    game_id = db.Column(db.String(50), db.ForeignKey('games.game_id'), nullable=False)
    hand_number = db.Column(db.Integer)
    player_name = db.Column(db.String(100))
    model_id = db.Column(db.String(100))
    hole_cards = db.Column(JSON)  # Stored as JSON array
    action = db.Column(db.String(50))
    amount = db.Column(db.Integer)
    message = db.Column(db.Text)
    prompt_sent = db.Column(JSON)  # Stored as JSON
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class HandResult(db.Model):
    __tablename__ = 'hand_results'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    game_id = db.Column(db.String(50), db.ForeignKey('games.game_id'), nullable=False)
    hand_number = db.Column(db.Integer, nullable=False)
    player_name = db.Column(db.String(100), nullable=False)
    model_id = db.Column(db.String(100), nullable=False)
    temperature = db.Column(db.Float)
    chips_before = db.Column(db.Integer, nullable=False)
    chips_after = db.Column(db.Integer, nullable=False)
    net_change = db.Column(db.Integer, nullable=False)
    is_winner = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return f"<HandResult {self.player_name} ({self.game_id}-{self.hand_number})>"


# ----------------------------------------------------
# 3. BUSINESS LOGIC FUNCTIONS
# ----------------------------------------------------

def init_db():
    """
    Creates tables if they do not exist using SQLAlchemy.
    """
    with app.app_context():
        try:
            db.create_all()
            print("Database initialized successfully.")
        except Exception as e:
            print(f"Error initializing database: {e}")


def create_new_game(game_id, config, players):
    """
    Saves new game data using ORM.
    """
    with app.app_context():
        new_game = Game(
            game_id=game_id,
            start_time=datetime.utcnow(),
            config=config,  # SQLAlchemy handles JSON serialization automatically
            players=players  # SQLAlchemy handles JSON serialization automatically
        )

        try:
            db.session.add(new_game)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error creating game: {e}")
            raise e


def log_game_event(game_id, hand_num, player_name, model_id, hole_cards, action, amount, message, prompt_json):
    """
    Saves single player action log using ORM.
    """
    with app.app_context():
        new_log = GameLog(
            game_id=game_id,
            hand_number=hand_num,
            player_name=player_name,
            model_id=model_id,
            hole_cards=hole_cards,  # Pass list/dict directly, ORM handles JSON
            action=action,
            amount=amount,
            message=message,
            prompt_sent=prompt_json,  # Pass dict directly
            timestamp=datetime.utcnow()
        )

        try:
            db.session.add(new_log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error logging event: {e}")
            raise e


def save_hand_result(data):
    """
    Saves a single hand result.
    Accepts the exact JSON structure provided by the user.
    """
    with app.app_context():
        c_before = data['chips_before']
        c_after = data['chips_after']

        # Use provided net_change/is_winner OR calculate if missing
        net_change = data.get('net_change', c_after - c_before)
        is_winner = data.get('is_winner', net_change > 0)

        result = HandResult(
            timestamp=datetime.utcnow(),
            game_id=data['game_id'],
            hand_number=data['hand_number'],
            player_name=data['player_name'],
            model_id=data['model_id'],
            temperature=data.get('temperature', 1.0),
            chips_before=c_before,
            chips_after=c_after,
            net_change=net_change,
            is_winner=is_winner
        )

        try:
            db.session.add(result)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error saving hand result: {e}")
            raise e


def get_aggregated_stats():
    """
    Gets model stats from the start (whole history) as a flat list
    using pandas and SQLAlchemy engine.
    """
    with app.app_context():
        try:
            # Use SQLAlchemy engine for pandas connection
            stmt = db.session.query(HandResult).statement
            df = pd.read_sql(stmt, db.session.bind)

            if df.empty:
                return []

            # Group by model
            model_stats = df.groupby('model_id').agg({
                'hand_number': 'count',
                'net_change': 'sum',
                'is_winner': 'sum'
            }).rename(columns={
                'hand_number': 'hands_played',
                'net_change': 'total_profit',
                'is_winner': 'hands_won'
            })

            # Calculations
            model_stats['win_rate'] = (model_stats['hands_won'] / model_stats['hands_played']).round(2)
            model_stats['avg_profit_per_hand'] = (model_stats['total_profit'] / model_stats['hands_played']).round(2)

            # Formatting results
            model_stats = model_stats.reset_index()
            model_stats = model_stats.rename(columns={'model_id': 'name'})

            return model_stats.to_dict('records')

        except Exception as e:
            print(f"Data analysis error in get_aggregated_stats: {e}")
            return []


# Example usage to ensure tables exist
if __name__ == "__main__":
    init_db()