class TableState:
    def __init__(self):
        self.players = []
        self.community_cards = []
        self.pot = 0
        self.current_player = None

    def init_players(self, players):
        self.players = players

    def to_dict(self):
        return {
            "players": [p.to_dict() for p in self.players],
            "community_cards": self.community_cards,
            "pot": self.pot,
            "current_player": self.current_player
        }
