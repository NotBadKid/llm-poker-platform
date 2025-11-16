from .table_state import TableState
from .pokerkit_adapter import PokerEngine
from .llm_agent import LLMPlayer

class GameManager:
    def __init__(self):
        self.table = TableState()
        self.engine = PokerEngine(self.table)

        # przykładowo 4 LLM agentów
        self.players = [
            LLMPlayer("GPT-5"),
            LLMPlayer("Gemini"),
            LLMPlayer("DS"),
            LLMPlayer("Grok")
        ]

        self.table.init_players(self.players)

    def handle_action(self, player_id, action_data):
        self.engine.apply_action(player_id, action_data)

        # po każdym ruchu LLM-agent może coś powiedzieć
        for p in self.players:
            if p.id != player_id:
                message = p.generate_comment(self.table)
                print(f"[LLM:{p.name}] {message}")

    def export_state(self):
        return self.table.to_dict()


game_manager = GameManager()
