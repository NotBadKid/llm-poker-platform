import threading

# Globalny rejestr przechowujący kontrolery dla aktywnych gier
# Klucz: game_id (str), Wartość: instancja GameController
active_games_controllers = {}

class GameController:
    def __init__(self):
        # Event: set() = gra działa, clear() = gra stoi
        self.execution_event = threading.Event()
        self.execution_event.set()  # Domyślnie gra rusza od razu
        self.is_paused_flag = False # Logiczna flaga trybu pauzy

    def pause(self):
        """Zatrzymuje grę (czerwone światło)."""
        self.is_paused_flag = True
        self.execution_event.clear()

    def play(self):
        """Wznawia ciągłą grę (zielone światło)."""
        self.is_paused_flag = False
        self.execution_event.set()

    def step(self):
        """
        Puszcza grę o jeden ruch (step-forward).
        Otwiera bramkę na chwilę, ale zostawia flagę is_paused_flag=True,
        co spowoduje zatrzymanie przy następnym sprawdzeniu w wait_for_turn.
        """
        self.is_paused_flag = True
        self.execution_event.set()

    def wait_for_turn(self):
        """
        Ta metoda jest wywoływana przez silnik gry.
        Blokuje wątek, jeśli gra jest zapauzowana.
        """
        self.execution_event.wait() # Tu wątek wisi, jeśli event jest clear()

        # Jeśli jesteśmy w trybie pauzy (np. po wykonaniu stepa),
        # natychmiast zamykamy bramkę dla następnego obrotu.
        if self.is_paused_flag:
            self.execution_event.clear()

# --- Funkcje pomocnicze do zarządzania rejestrem ---

def get_controller(game_id: str):
    return active_games_controllers.get(game_id)

def register_controller(game_id: str) -> GameController:
    controller = GameController()
    active_games_controllers[game_id] = controller
    return controller

def remove_controller(game_id: str):
    if game_id in active_games_controllers:
        del active_games_controllers[game_id]