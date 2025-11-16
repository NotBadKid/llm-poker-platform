from pokerkit import NoLimitHoldem

class PokerEngine:
    def __init__(self, table_state):
        self.state = table_state
        self.game = NoLimitHoldem.create()

    def apply_action(self, player_id, action_data):
        # TODO: integracja z pokerkit
        pass
