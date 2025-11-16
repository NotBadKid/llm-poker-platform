from .player_agent import PlayerAgent

class LLMPlayer(PlayerAgent):

    def generate_comment(self, state):
        # tu będzie API do LLM
        return f"{self.name} thinking..."
