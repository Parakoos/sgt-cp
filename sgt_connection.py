from view import View
from game_state import GameState

class SgtConnection:
    def __init__(self, view: View):
        self.view = view

    def is_connected(self) -> bool:
        return False

    def connect(self):
        pass

    def poll(self) -> None:
        return None
