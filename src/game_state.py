import adafruit_logging as logging
log = logging.getLogger()
import json
import time
from utils.find import find_thing
from utils.log import log_exception
from utils.color import PlayerColor, WHITE

def get_state_int(state, key, default=0):
	return int(state[key]) if key in state and state[key] != None and state[key] != "" else default

color_cache_old = dict()
color_cache_new = dict()
def get_state_color(state, keyRgb, keyHsv, default=WHITE) -> PlayerColor:
	key = keyHsv if keyHsv in state else keyRgb
	color_hex = get_state_string(state, key, '')
	if len(color_hex) != 6:
		return default
	if color_hex in color_cache_old:
		color = color_cache_old[color_hex]
	else:
		color = PlayerColor(color_hex, key == keyHsv)
		color_cache_old[color_hex] = color
	color_cache_new[color_hex] = color_cache_old[color_hex]
	return color

def get_state_string(state, key, default=""):
	return state[key] if key in state and state[key] != None and len(state[key].strip()) > 0 else default

def get_sub_state(state, key) -> dict:
	return state[key] if key in state and state[key] != None else {}

def get_action(state, key):
	return Action(state[key]) if key in state and state[key] != None else None

def get_players(state, key):
	return [Player(x) for x in state[key]] if key in state and state[key] != None else []

class Action():
	def __init__(self, actionState) -> None:
		self.action = get_state_string(actionState, 'action', default=None)
		self.label = get_state_string(actionState, 'label', default=None)

	def __repr__(self):
		return f'Action<{self.action} {self.label}>'

class Player():
	def __init__(self, playerState) -> None:
		self.name = get_state_string(playerState, 'name', default=None)
		self.seat = get_state_int(playerState, 'seat', default=None)
		self.action = get_state_string(playerState, 'action', default=None)
		self.color = get_state_color(playerState, 'color', 'colorHsv')

	def __repr__(self):
		if self.action == '':
			return f'Player<{self.seat}, {self.color} {self.name}>'
		else:
			return f'Player<{self.seat}, {self.color} {self.name} action={self.action}>'

class CurrentTimes():
	def __init__(self, ts: int, turn_time: float, player_time: float, total_play_time: float) -> None:
		self.ts = ts

		# Count-Up, time taken this turn or pause time or admin time
		# Count-Down, same as above, but negative values during Delay Time
		# Sand, time taken out of the sand timer
		self.turn_time = turn_time

		# Count-Up, total time taken, or blank for admin/pause/sim. tur
		# Count-Down, remaining time bank, or blank for admin/pause/sim. turn
		# Sand, size (in sec) of the sand timer (it's reset size)
		self.player_time = player_time

		# Count-Up/Down, total play time, not counting this turn and not admin/pause time
		self.total_play_time = total_play_time

	def __repr__(self):
		return f'CurrentTimes<turn={self.turn_time}, player={self.player_time}, total={self.total_play_time}>'

# Constants
STATE_PLAYING = 'pl'
STATE_ADMIN = 'ad'
STATE_PAUSE = 'pa'
STATE_START = 'st'
STATE_FINISHED = 'en'
STATE_NOT_CONNECTED = 'nc'
STATE_RUNNING = 'ru'
STATE_NOT_RUNNING = 'nr'
STATE_SIM_TURN = 'si'

STATE_TYPE_MID_TURN = 'mt'
STATE_TYPE_MID_SIM_TURN = 'ms'
STATE_TYPE_END_OF_TURN = 'et'
STATE_TYPE_END_OF_ROUND = 'er'
STATE_TYPE_BEFORE_GAME = 'bg'
STATE_TYPE_SETUP_ADMIN = 'se'

TIMER_MODE_COUNT_UP = 'cu'
TIMER_MODE_COUNT_DOWN = 'cd'
TIMER_MODE_SAND_TIMER = 'st'
TIMER_MODE_NO_TIMER = 'nt'

class GameState():

	def __init__(self,
				ble_state_string: str|None = None, ble_field_order: list[str]|None = None, ble_field_divider: str|None = None,
				json_state_string: str|None = None,
				timestamp_offset = 0):
		global color_cache_old, color_cache_new
		color_cache_new = dict()
		state = {}
		if (json_state_string != None):
			try:
				state = json.loads(json_state_string)
			except Exception as e:
				print(json_state_string)
				log_exception(e)
		elif ble_state_string != None and ble_field_order != None and ble_field_divider != None:
			values = ble_state_string.split(ble_field_divider)
			if len(values) != len(ble_field_order):
				raise Exception(f"Different number of values from the keys. ({len(values)} != {len(ble_field_order)})")
			state["ts"]=time.monotonic()

			simple_mappings = [
				('sgtTimerMode', 'timerMode'),
				('sgtColor', 'color'),
				('sgtColorHsv', 'colorHsv'),
				('sgtTurnTime', 'turnTime'),
				('sgtState', 'state'),
				('sgtStateType', 'stateType'),
				('sgtName', 'name'),
				('sgtPlayerTime', 'playerTime'),
				('sgtTotalPlayTime', 'totalPlayTime'),
				('sgtActionAdmin', 'actionAdmin'),
				('sgtActionInactive', 'actionInactive'),
				('sgtActionPause', 'actionPause'),
				('sgtActionPrimary', 'actionPrimary'),
				('sgtActionSecondary', 'actionSecondary'),
				('sgtActionUndo', 'actionUndo'),
				('sgtGameStateVersion', 'gameStateVersion'),
				('sgtPlayerActions', 'playerActions'),
				('sgtPlayerColors', 'playerColors'),
				('sgtPlayerColorsHsv', 'playerColorsHsv'),
				('sgtPlayerNames', 'playerNames'),
				('sgtPlayerSeats', 'playerSeats'),
			]
			for (sgt_name, state_name) in simple_mappings:
				if sgt_name in ble_field_order:
					state[state_name] = values[ble_field_order.index(sgt_name)]

			if 'sgtSeat' in ble_field_order:
				val = values[ble_field_order.index('sgtSeat')]
				state['seat'] = json.loads(f"[{val}]")

			if 'sgtTimeReminders' in ble_field_order:
				val = values[ble_field_order.index('sgtTimeReminders')]
				if len(val) > 0:
					state['timeReminders'] = json.loads(f"[{val}]")

			players = None
			sgtPlayerActions = values[ble_field_order.index('sgtPlayerActions')].split(',') if 'sgtPlayerActions' in ble_field_order else None
			sgtPlayerColors = values[ble_field_order.index('sgtPlayerColors')].split(',') if 'sgtPlayerColors' in ble_field_order else None
			sgtPlayerColorsHsv = values[ble_field_order.index('sgtPlayerColorsHsv')].split(',') if 'sgtPlayerColorsHsv' in ble_field_order else None
			sgtPlayerNames = values[ble_field_order.index('sgtPlayerNames')].split(',') if 'sgtPlayerNames' in ble_field_order else None
			sgtPlayerSeats = values[ble_field_order.index('sgtPlayerSeats')].split(',') if 'sgtPlayerSeats' in ble_field_order else None
			nonNullPlayerArr = sgtPlayerActions or sgtPlayerColors or sgtPlayerNames or sgtPlayerSeats or None
			if (nonNullPlayerArr != None):
				players = [{} for _item in nonNullPlayerArr]
				if sgtPlayerActions:
					for index, val in enumerate(sgtPlayerActions):
						players[index]['action'] = val
				if sgtPlayerColors:
					for index, val in enumerate(sgtPlayerColors):
						players[index]['color'] = val
				if sgtPlayerColorsHsv:
					for index, val in enumerate(sgtPlayerColorsHsv):
						players[index]['colorHsv'] = val
				if sgtPlayerNames:
					for index, val in enumerate(sgtPlayerNames):
						players[index]['name'] = val
				if sgtPlayerSeats:
					for index, val in enumerate(sgtPlayerSeats):
						players[index]['seat'] = val
				state['players'] = players
		# When was this state sent? (in monotonic space)
		ts = get_state_int(state, 'ts', 0)
		self.timestamp = ts + timestamp_offset

		# The last version of the state, used to prevent doing actions against old states. Must be sent with each command.
		self.game_state_version = get_state_int(state, 'gameStateVersion', -1)

		# Current timer-mode (cd/cu/st/nt for Count-Down/Up, SandTimer, No Timer)
		self.timer_mode = get_state_string(state, 'timerMode', TIMER_MODE_COUNT_UP)

		# The current state.
		# Sand, ru/nr/pa/en for running, not running, paused or end
		# Not Sand, st/en/pa/ad/pl for start, end, pause, admin or playing
		self.state = get_state_string(state, 'state', STATE_NOT_CONNECTED)

		# mt/ms/et/er/bg/se for Mid-Turn, Mid-Sim-Turn, End-of-Turn, End-of-Round, Before-Game, Setup if in Admin Time
		self.stateType = get_state_string(state, 'stateType')

		# Count-Up, time taken this turn or pause time or admin time
		# Count-Down, same as above, but negative values during Delay Time
		# Sand, time taken out of the sand timer
		self.turn_time_sec = get_state_int(state, 'turnTime')

		self.player_time_sec = get_state_int(state, 'playerTime')

		# Count-Up/Down, total play time, not counting this turn and not admin/pause time
		self.total_play_time_sec = get_state_int(state, 'totalPlayTime')

		# (not sand) The current or next-up player name
		self.name = get_state_string(state, 'name', "(no name)")

		# (not sand) The current or next-up player color
		self.color = get_state_color(state, 'color', 'colorHsv')

		# Different actions. Either None or a string starting with 'game/{action}' that
		# can be sent to the MQTT commands queue to issue commands
		actions = get_sub_state(state, 'actions')
		self.action_primary = get_action(actions, 'primary')
		self.action_secondary = get_action(actions, 'secondary')
		self.action_admin = get_action(actions, 'admin')
		self.action_pause = get_action(actions, 'pause')

		self.players = get_players(state, 'players')

		state_var = state['seat'] if 'seat' in state and state['seat'] != None else None
		if isinstance(state_var, int):
			self.seat = [state_var]
		elif isinstance(state_var, list):
			self.seat = [int(seat) for seat in state_var]
		else:
			self.seat = []

		time_reminders_var = state['timeReminders'] if 'timeReminders' in state and state['timeReminders'] != None else None
		if isinstance(time_reminders_var, list):
			self.time_reminders = [int(tr) for tr in time_reminders_var]
		else:
			self.time_reminders = None

		self.current_times = None
		color_cache_old = color_cache_new

	def has_action(self, action):
		return self.action_admin == action or self.action_pause == action or self.action_primary == action or self.action_secondary == action

	def allow_sim_turn_start(self):
		if self.state == STATE_PLAYING:
			return True
		if self.state != STATE_ADMIN:
			return False
		if self.action_primary == None:
			# We cannot know for sure what kind of admin state we are in...
			return True
		return "resumeTurn" in self.action_primary.action

	def get_active_player(self) -> Player | None:
		if len(self.seat) == 1:
			return find_thing((p for p in self.players if p.seat == self.seat[0]), None)
		elif len(self.seat) == 0:
			return find_thing((p for p in self.players if p.action == 'pr' or p.action == 'se'), None)
		else:
			return None

	def get_player_by_seat(self, seat: int) -> Player | None:
		return find_thing((p for p in self.players if p.seat == seat), None)

	def get_current_timings(self):
		now = time.monotonic()

		if self.timer_mode == None:
			raise Exception(f'Unkown timer mode: {self.timer_mode}')

		# Count-Up, time taken this turn or pause time or admin time
		# Count-Down, same as above, but negative values during Delay Time
		# Sand, time taken out of the sand timer
		turn_time = self.turn_time_sec

		# Count-Up, total time taken, or blank for admin/pause/sim. tur
		# Count-Down, remaining time bank, or blank for admin/pause/sim. turn
		# Sand, size (in sec) of the sand timer (it's reset size)
		player_time = self.player_time_sec

		# Count-Up/Down, total play time, not counting this turn and not admin/pause time
		total_play_time = self.total_play_time_sec

		time_added_by_monotonic = now - self.timestamp
		if self.timer_mode == TIMER_MODE_COUNT_UP or self.timer_mode == TIMER_MODE_NO_TIMER:
			if self.state in [STATE_PLAYING, STATE_ADMIN, STATE_PAUSE, STATE_SIM_TURN]:
				turn_time = self.turn_time_sec + time_added_by_monotonic
				if self.state == STATE_PLAYING:
					player_time = time_added_by_monotonic + self.player_time_sec
					total_play_time = (time_added_by_monotonic + self.total_play_time_sec)
			elif self.state in [STATE_START, STATE_FINISHED, STATE_NOT_CONNECTED]:
				pass
			else:
				raise Exception(f'Unknown state: {self.state}')

		elif self.timer_mode == TIMER_MODE_COUNT_DOWN:
			if self.state in [STATE_PLAYING, STATE_ADMIN, STATE_PAUSE, STATE_SIM_TURN]:
				turn_time = self.turn_time_sec + time_added_by_monotonic
				if self.state == STATE_PLAYING:
					player_time = self.player_time_sec
					if (self.turn_time_sec < 0):
						player_time -= max(0, time_added_by_monotonic + self.turn_time_sec)
					else:
						player_time -= time_added_by_monotonic
			elif self.state in [STATE_START, STATE_FINISHED, STATE_NOT_CONNECTED]:
				pass
			else:
				raise Exception(f"Unknown state: {self.state}")

		elif self.timer_mode == TIMER_MODE_SAND_TIMER:
			if self.state == STATE_RUNNING:
				turn_time = self.turn_time_sec + time_added_by_monotonic
			elif self.state == STATE_PAUSE:
				turn_time = self.turn_time_sec + time_added_by_monotonic
			elif self.state in [self.state == STATE_NOT_RUNNING, STATE_FINISHED, STATE_NOT_CONNECTED]:
				pass
			else:
				raise Exception(f'Unkown state: {self.state}')
		else:
			raise Exception(f'Unkown timer mode: {self.timer_mode}')

		self.current_times = CurrentTimes(now, turn_time, player_time, total_play_time)
		return self.current_times

	def __repr__(self):
		facts = []
		if (self.timestamp):
			facts.append(f'ts={self.timestamp}')
		if (self.game_state_version):
			facts.append(f'v={self.game_state_version}')
		if (self.timer_mode):
			facts.append(f'mode={self.timer_mode}')
		if (self.stateType):
			facts.append(f'state={self.state}/{self.stateType}')
		else:
			facts.append(f'state={self.state}')
		if (self.turn_time_sec):
			facts.append(f'turn_time={self.turn_time_sec}')
		if (self.player_time_sec):
			facts.append(f'player_time={self.player_time_sec}')
		if (self.total_play_time_sec):
			facts.append(f'total_time={self.total_play_time_sec}')
		if (self.time_reminders):
			facts.append(f'time_reminders={self.time_reminders}')
		if (self.name):
			facts.append(f'name={self.name}')
		if (self.color):
			facts.append(f'color={self.color}')
		if (self.seat):
			facts.append(f'seat={self.seat}')
		if (self.action_primary):
			facts.append(f'a_primary={self.action_primary}')
		if (self.action_secondary):
			facts.append(f'a_secondary={self.action_secondary}')
		if (self.action_admin):
			facts.append(f'a_admin={self.action_admin}')
		if (self.action_pause):
			facts.append(f'a_pause={self.action_pause}')
		if (self.players):
			facts.append(f'players={self.players}')
		return f"<SGT State: {', '.join(facts)}>"

	def make_copy(self, state_override: str|None = None):
		copy = GameState()
		copy.timestamp = self.timestamp
		copy.game_state_version = self.game_state_version
		copy.timer_mode = self.timer_mode
		copy.state = self.state if state_override == None else state_override
		copy.turn_time_sec = self.turn_time_sec
		copy.player_time_sec = self.player_time_sec
		copy.total_play_time_sec = self.total_play_time_sec
		copy.name = self.name
		copy.color = self.color
		copy.action_primary = self.action_primary
		copy.action_secondary = self.action_secondary
		copy.action_admin = self.action_admin
		copy.action_pause = self.action_pause
		copy.players = self.players
		copy.seat = self.seat
		return copy