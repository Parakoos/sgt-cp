from core.view.view import View
from core.game_state import STATE_PLAYING, STATE_ADMIN, STATE_PAUSE, STATE_START, STATE_FINISHED, STATE_RUNNING, STATE_NOT_RUNNING, STATE_SIM_TURN

def _success(action:str, on_success: callable[[], None] = None):
	if on_success:
		on_success()
	return action

def _failure(on_failure: callable[[], None] = None):
	if on_failure:
		on_failure()
	return None

class SgtConnection:
	def __init__(self, view: View):
		self.view = view

	def is_connected(self) -> bool:
		return False

	def connect(self):
		pass

	def poll_for_new_messages(self) -> None:
		return None

	def handle_new_messages(self) -> None:
		"Return true if any messages were dealt with"
		return False

	def restart(self) -> None:
		pass

	def send_command(self) -> bool:
		"Return true if a message was sent."
		return False

	def enqueue_send_primary(self, seat: int|None = None, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		if self.view.state == None:
			return _failure(on_failure)
		if self.view.state.state in (STATE_START, STATE_FINISHED):
			return _failure(on_failure)
		if seat == None:
			return _success('Primary', on_success)
		player = self.view.state.get_player_by_seat(seat)
		if player and player.action != None:
			return _success('Primary', on_success)
		else:
			return _failure(on_failure)
	def enqueue_send_secondary(self, seat: int|None = None, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		if self.view.state == None:
			return _failure(on_failure)
		if self.view.state.state != STATE_PLAYING:
			return _failure(on_failure)
		if seat == None:
			return _success('Secondary', on_success)
		player = self.view.state.get_player_by_seat(seat)
		if player and player.action == 'se':
			return _success('Secondary', on_success)
		else:
			return _failure(on_failure)
	def enqueue_send_toggle_admin(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		if self.view.state == None:
			return _failure(on_failure)
		if self.view.state.state in (STATE_PLAYING, STATE_ADMIN, STATE_SIM_TURN):
			return _success('ToggleAdmin', on_success)
		else:
			return _failure(on_failure)
	def enqueue_send_admin_on(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		if self.view.state == None:
			return _failure(on_failure)
		if self.view.state.state == STATE_PLAYING:
			return _success('TurnAdminOn', on_success)
		else:
			return _failure(on_failure)
	def enqueue_send_admin_off(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		if self.view.state == None:
			return _failure(on_failure)
		if self.view.state.state == STATE_ADMIN:
			return _success('TurnAdminOff', on_success)
		else:
			return _failure(on_failure)
	def enqueue_send_toggle_pause(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		if self.view.state == None:
			return _failure(on_failure)
		if self.view.state.state in (STATE_START, STATE_FINISHED):
			return _failure(on_failure)
		else:
			return _success('TogglePause', on_success)
	def enqueue_send_pause_on(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		if self.view.state == None:
			return _failure(on_failure)
		if self.view.state.state in (STATE_START, STATE_FINISHED, STATE_PAUSE):
			return _failure(on_failure)
		else:
			return _success('TurnPauseOn', on_success)
	def enqueue_send_pause_off(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		if self.view.state == None:
			return _failure(on_failure)
		if self.view.state.state == STATE_PAUSE:
			return _success('TurnPauseOff', on_success)
		else:
			return _failure(on_failure)
	def enqueue_send_undo(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		if self.view.state == None:
			return _failure(on_failure)
		if self.view.state.state in (STATE_START, STATE_FINISHED, STATE_RUNNING, STATE_NOT_RUNNING):
			return _failure(on_failure)
		else:
			return _success('Undo', on_success)
	def enqueue_send_start_game(self, seat: int|None = None, seats: list[int]|None = None, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		if self.view.state == None:
			return _failure(on_failure)
		if self.view.state.state != STATE_START:
			return _failure(on_failure)
		if seat == None and seats == None:
			return _success('StartGame', on_success)
		if seat != None and seats == None:
			player = self.view.state.get_player_by_seat(seat)
			if player:
				return _success('StartGame', on_success)
		if seat == None and seats != None and len(self.view.state.players) == len(seats):
			# Check if all players are in the list of seats.
			no_dupe_list = list( dict.fromkeys(seats) )
			if len(no_dupe_list) != len(seats):
				return _failure(on_failure)
			for seat in seats:
				player = self.view.state.get_player_by_seat(seat)
				if player == None:
					return _failure(on_failure)
			return _success('StartGame', on_success)
		return _failure(on_failure)

	def enqueue_send_start_sim_turn(self, seats: set[int]):
		if self.view.state != None and self.view.state.allow_sim_turn_start():
			return 'StartSimTurn'
		else:
			return None

	def enqueue_send_new_turn_order(self, turn_order_seats: list[int]):
		if self.view.state != None and self.view.state.allow_reorder():
			return "Reorder"
		else:
			return None

	def enqueue_send_join_game_or_cycle_colors(self, seat: int, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		if self.view.state.state == STATE_START:
			player = self.view.state.get_player_by_seat(seat)
			if player == None:
				return _success('AddHotseatPlayer', on_success)
			else:
				return _success('CyclePlayerColor', on_success)
		else:
			return _failure(on_failure)

	def enqueue_send_leave_game(self, seat: int, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		if self.view.state.state == STATE_START:
			player = self.view.state.get_player_by_seat(seat)
			if player != None:
				return _success('RemovePlayer', on_success)
		return _failure(on_failure)