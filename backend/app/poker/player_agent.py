import uuid

class PlayerAgent:
    def __init__(self, name, stack=10000):
        self.id = str(uuid.uuid4())
        self.name = name
        self.stack = stack
        self.hole_cards = []

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "stack": self.stack,
            "hole_cards": self.hole_cards,
        }
