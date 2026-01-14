import threading

active_games_controllers = {}

class GameController:
    def __init__(self):
        # Event: set() = game plays, clear() = game paused
        self.execution_event = threading.Event()
        self.execution_event.set()  #Game starts with playing mode
        self.is_paused_flag = False
        self.is_aborted_flag = False

    def pause(self):
        self.is_paused_flag = True
        self.execution_event.clear()

    def play(self):
        self.is_paused_flag = False
        self.execution_event.set()

    def step(self):
        """
        Opens the gate for a moment but leaves flag is_paused_flag=True,
        what results in a pause in the next check w wait_for_turn.
        """
        self.is_paused_flag = True
        self.execution_event.set()

    def abort(self):
        self.is_aborted_flag = True
        self.is_paused_flag = False
        self.execution_event.set()

    def wait_for_turn(self):
        """
        Run by game engine, blocks the thread if game is paused.
        """
        self.execution_event.wait()

        if self.is_paused_flag:
            self.execution_event.clear()


def get_controller(game_id: str):
    return active_games_controllers.get(game_id)

def register_controller(game_id: str) -> GameController:
    controller = GameController()
    active_games_controllers[game_id] = controller
    return controller

def remove_controller(game_id: str):
    if game_id in active_games_controllers:
        del active_games_controllers[game_id]