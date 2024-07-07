from game_state import GameState
from view import View

class ViewMulti(View):
	def __init__(self, views: list[View]):
		super().__init__()
		self.views = views
		for view in self.views:
			view.enable_time_reminder_check = False
	def animate(self) -> bool:
		busy_animating = super().animate()
		for view in self.views:
			busy_animating = view.animate() or busy_animating
		return busy_animating
	def show_error(self, exception):
		for view in self.views:
			view.show_error(exception)
	def set_connection_progress_text(self, text):
		for view in self.views:
			view.set_connection_progress_text(text)
	def switch_to_playing(self, state: GameState, old_state: GameState):
		for view in self.views:
			view.switch_to_playing(state, old_state)
	def switch_to_simultaneous_turn(self, state: GameState, old_state: GameState):
		for view in self.views:
			view.switch_to_simultaneous_turn(state, old_state)
	def switch_to_admin_time(self, state: GameState, old_state: GameState):
		for view in self.views:
			view.switch_to_admin_time(state, old_state)
	def switch_to_paused(self, state: GameState, old_state: GameState):
		for view in self.views:
			view.switch_to_paused(state, old_state)
	def switch_to_sandtimer_running(self, state: GameState, old_state: GameState):
		for view in self.views:
			view.switch_to_sandtimer_running(state, old_state)
	def switch_to_sandtimer_not_running(self, state: GameState, old_state: GameState):
		for view in self.views:
			view.switch_to_sandtimer_not_running(state, old_state)
	def switch_to_start(self, state: GameState, old_state: GameState):
		for view in self.views:
			view.switch_to_start(state, old_state)
	def switch_to_end(self, state: GameState, old_state: GameState):
		for view in self.views:
			view.switch_to_end(state, old_state)
	def switch_to_no_game(self):
		for view in self.views:
			view.switch_to_no_game()
	def switch_to_not_connected(self):
		for view in self.views:
			view.switch_to_not_connected()
	def switch_to_error(self):
		for view in self.views:
			view.switch_to_error()
	def set_state(self, state: GameState):
		super().set_state(state)
		self.state = state
		for view in self.views:
			view.set_state(state)
	def on_time_reminder(self, time_reminder_count: int):
		for view in self.views:
			view.on_time_reminder(time_reminder_count)