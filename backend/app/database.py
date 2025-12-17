import json
import pandas as pd
from datetime import datetime
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ----------------------------------------------------
# 1. DATABASE CONFIGURATION
# ----------------------------------------------------

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")

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
    config = db.Column(JSON)
    players = db.Column(JSON)

    # Relationships
    logs = db.relationship('GameLog', backref='game', lazy=True)
    results = db.relationship('HandResult', backref='game', lazy=True)


class GameLog(db.Model):
    __tablename__ = 'game_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    game_id = db.Column(db.String(50), db.ForeignKey('games.game_id'), nullable=False)
    hand_number = db.Column(db.Integer)
    player_name = db.Column(db.String(100))
    model_id = db.Column(db.String(100))
    hole_cards = db.Column(JSON)
    action = db.Column(db.String(50))
    amount = db.Column(db.Integer)
    message = db.Column(db.Text)
    prompt_sent = db.Column(JSON)
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


class ModelInfo(db.Model):
    __tablename__ = 'models_info'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    model_id = db.Column(db.String(100), unique=True, nullable=False)
    parameters = db.Column(db.BigInteger)
    input_price = db.Column(db.Float)
    output_price = db.Column(db.Float)
    structured_outputs = db.Column(db.Boolean)
    description = db.Column(db.Text)
    context = db.Column(db.BigInteger)
    open_router_url = db.Column(db.Text)

    def __repr__(self):
        return f"<ModelInfo {self.name} ({self.model_id})>"

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
            config=config,
            players=players
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
            hole_cards=hole_cards,
            action=action,
            amount=amount,
            message=message,
            prompt_sent=prompt_json,
            timestamp=datetime.utcnow()
        )

        try:
            db.session.add(new_log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error logging event: {e}")
            raise e


def save_hand_result(game_id, hand_num, player_stats):
    """
    Saves results for all players after a hand.

    Args:
        game_id (str): UUID of the game.
        hand_num (int): Current hand number.
        player_stats (list): List of dicts, e.g.:
            [{'name': '...', 'model': '...', 'temp': 1.0, 'before': 1000, 'after': 1200}, ...]
    """
    with app.app_context():
        timestamp = datetime.utcnow()

        try:
            for p in player_stats:
                # Calculate profit/loss
                net_change = p['after'] - p['before']
                is_winner = net_change > 0

                result = HandResult(
                    timestamp=timestamp,
                    game_id=game_id,
                    hand_number=hand_num,
                    player_name=p['name'],
                    model_id=p['model'],  # Mapping 'model' from dict to 'model_id' column
                    temperature=p.get('temp', 1.0),
                    chips_before=p['before'],
                    chips_after=p['after'],
                    net_change=net_change,
                    is_winner=is_winner
                )
                db.session.add(result)

            # Commit all results for this hand at once
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
            query = db.session.query(HandResult)

            # 2. Use the live session connection with pd.read_sql
            df = pd.read_sql(query.statement, db.session.connection())

            if df.empty:
                return []

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

            # Formatting results (Flattening structure)
            model_stats = model_stats.reset_index()
            model_stats = model_stats.rename(columns={'model_id': 'name'})

            # Return list of dicts (flat JSON array)
            return model_stats.to_dict('records')

        except Exception as e:
            print(f"Data analysis error in get_aggregated_stats: {e}")
            return []


def get_models_data(structured_output_only: bool = False):
    """
    Fetches models from the database.

    Args:
        structured_output_only (bool):
            If True, returns only models where structured_outputs is True.
            If False, returns ALL models.
    """
    try:
        # Start with a base query for all models
        stmt = db.select(ModelInfo)

        # Apply filter only if specifically requested
        if structured_output_only:
            stmt = stmt.where(ModelInfo.structured_outputs == True)

        # Execute
        results = db.session.execute(stmt).scalars().all()

        # Serialize
        return [{
            "id": m.id,
            "name": m.name,
            "provider": getattr(m, 'provider', 'Unknown'),
            "structured_outputs": m.structured_outputs
        } for m in results]

    except Exception as e:
        print(f"Error fetching models: {e}")
        return []


def save_models_info_list_into_database(models):
    """
    Saves or updates a list of model JSON objects into the database.
    """
    # Ensure we are in the app context so we can use 'db'
    with app.app_context():
        try:
            for m_data in models:
                # 1. Extract the unique ID (Handle both 'model_id' and 'id')
                uid = m_data.get('model_id') or m_data.get('id')

                if not uid:
                    print(f"Skipping item due to missing ID: {m_data.get('name', 'Unknown')}")
                    continue

                # 2. Check if model exists
                existing_model = db.session.execute(
                    db.select(ModelInfo).where(ModelInfo.model_id == uid)
                ).scalar_one_or_none()

                # 3. specific mapping logic (handling potential nested pricing)
                pricing = m_data.get('pricing', {})
                # Handle cases where pricing is a dict or flat keys
                if isinstance(pricing, dict):
                    inp_price = pricing.get('prompt')
                    out_price = pricing.get('completion')
                else:
                    inp_price = m_data.get('input_price')
                    out_price = m_data.get('output_price')

                # 4. Prepare values
                update_data = {
                    "name": m_data.get('name', 'Unknown Model'),
                    "parameters": m_data.get('parameters'),
                    "input_price": float(inp_price) if inp_price is not None else 0.0,
                    "output_price": float(out_price) if out_price is not None else 0.0,
                    "structured_outputs": m_data.get('structured_outputs', False),
                    "description": m_data.get('description'),
                    "context": m_data.get('context_length') or m_data.get('context'),
                    # Handle both naming conventions for the URL
                    "open_router_url": m_data.get('openrouter_url') or m_data.get('open_router_url')
                }

                if existing_model:
                    # --- UPDATE EXISTING ---
                    existing_model.name = update_data['name']
                    existing_model.parameters = update_data['parameters']
                    existing_model.input_price = update_data['input_price']
                    existing_model.output_price = update_data['output_price']
                    existing_model.structured_outputs = update_data['structured_outputs']
                    existing_model.description = update_data['description']
                    existing_model.context = update_data['context']
                    existing_model.open_router_url = update_data['open_router_url']
                else:
                    # --- CREATE NEW ---
                    new_model = ModelInfo(
                        model_id=uid,
                        **update_data
                    )
                    db.session.add(new_model)

            # 5. Commit all changes
            db.session.commit()
            print(f"Successfully synced {len(models)} models to database.")

        except Exception as e:
            db.session.rollback()
            print(f"Error saving models to database: {e}")
            raise e
# Example usage to ensure tables exist
if __name__ == "__main__":
    init_db()