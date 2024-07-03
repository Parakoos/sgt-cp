from game_state import GameState
import adafruit_logging as logging
log = logging.getLogger()
import time
from view import View

class ViewConsole(View):
    def __init__(self):
        super().__init__()

    def show_error(self, exception):
        log.info(f"ERROR: {exception}")
    def set_connection_progress_text(self, text):
        log.info(f"Connection Progress: {text}")
    def switch_to_playing(self, state: GameState, old_state: GameState):
        log.info(f"-> Playing")
    def switch_to_simultaneous_turn(self, state: GameState, old_state: GameState):
        log.info(f"-> Simultaneous Turn")
    def switch_to_admin_time(self, state: GameState, old_state: GameState):
        log.info(f"-> Admin Time")
    def switch_to_paused(self, state: GameState, old_state: GameState):
        log.info(f"-> Paused")
    def switch_to_sandtimer_running(self, state: GameState, old_state: GameState):
        log.info(f"-> Sand Timer (Running)")
    def switch_to_sandtimer_not_running(self, state: GameState, old_state: GameState):
        log.info(f"-> Sand Timer (Stopped)")
    def switch_to_start(self, state: GameState, old_state: GameState):
        log.info(f"-> Setup")
    def switch_to_end(self, state: GameState, old_state: GameState):
        log.info(f"-> Game Over")
    def switch_to_no_game(self):
        log.info(f"-> No Game In Progress")
    def switch_to_not_connected(self):
        log.info(f"-> Not Connecting")
    def switch_to_error(self):
        log.info(f"-> Error")
    def on_state_update(self, state: GameState, old_state: GameState):
        log.info("State: %s\nTimings: %s", state, state.get_current_timings())
    def on_time_reminder(self, time_reminder_count: int):
        log.info(f"-> Time Reminder Triggered. Count: {time_reminder_count}")