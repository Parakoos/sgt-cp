from game_state import GameState
import adafruit_logging as logging
log = logging.getLogger()
import time
from view import View

class ViewConsole(View):
    def __init__(self):
        super().__init__()

    def show_error(self, exception):
        print(f"ERROR: {exception}")
    def set_connection_progress_text(self, text):
        print(f"Connection Progress: {text}")
    def switch_to_playing(self, state: GameState, old_state: GameState):
        print(f"-> Playing")
    def switch_to_simultaneous_turn(self, state: GameState, old_state: GameState):
        print(f"-> Simultaneous Turn")
    def switch_to_admin_time(self, state: GameState, old_state: GameState):
        print(f"-> Admin Time")
    def switch_to_paused(self, state: GameState, old_state: GameState):
        print(f"-> Paused")
    def switch_to_sandtimer_running(self, state: GameState, old_state: GameState):
        print(f"-> Sand Timer (Running)")
    def switch_to_sandtimer_not_running(self, state: GameState, old_state: GameState):
        print(f"-> Sand Timer (Stopped)")
    def switch_to_start(self, state: GameState, old_state: GameState):
        print(f"-> Setup")
    def switch_to_end(self, state: GameState, old_state: GameState):
        print(f"-> Game Over")
    def switch_to_no_game(self):
        print(f"-> No Game In Progress")
    def switch_to_not_connected(self):
        print(f"-> Not Connecting")
    def switch_to_error(self):
        print(f"-> Error")
    def on_state_update(self, state: GameState, old_state: GameState):
        print(state, state.get_current_timings())