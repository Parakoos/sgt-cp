import adafruit_logging as logging
log = logging.getLogger()

from core.game_state import GameState
from core.view.view import View

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
		super().switch_to_no_game()
		log.info(f"-> No Game In Progress")
	def switch_to_not_connected(self):
		super().switch_to_not_connected()
		log.info(f"-> Not Connected")
	def switch_to_error(self):
		super().switch_to_error()
		log.info(f"-> Error")
	def on_state_update(self, state: GameState|None, old_state: GameState|None):
		pass
		log.info("State: %s", state)
	def on_time_reminder(self, time_reminder_count: int):
		log.info(f"-> Time Reminder Triggered. Count: {time_reminder_count}")