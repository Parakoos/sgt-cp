from seated_animation.seated_animation import SgtSeatedAnimation, Line, LineTransition, TIME_REMINDER_EASINGS, TIME_REMINDER_MAX_PULSES, TIME_REMINDER_PULSE_DURATION
from view_table_outline import ViewTableOutline, BLACK, FADE_EASE, FADE_DURATION
from game_state import GameState, STATE_START, STATE_SIM_TURN, STATE_ADMIN, Player
from utils.transition import PropertyTransition, SerialTransitionFunctions, ColorTransitionFunction, ParallellTransitionFunctions
from utils.find import find_thing
from math import ceil
import time
import adafruit_logging as logging
log = logging.getLogger()

class SgtSeatedMultiplayerAnimation(SgtSeatedAnimation):
	def __init__(self, parent_view: ViewTableOutline):
		super().__init__(parent_view)
		self.seat_lines = list(LineTransition(Line(midpoint=s[0], length=0, color=BLACK.copy()), transitions=[]) for s in self.seat_definitions)
		self.blinks_left = 0
		self.blink_transition = None
		self.current_times = None
		self.state = None
		self.first_player_init_ts = None

	def animate(self):
		if self.blink_transition == None and self.blinks_left > 0:
			self.blinks_left = self.blinks_left - 1
			self.blink_transition = SerialTransitionFunctions([
				PropertyTransition(self.pixels, 'brightness', 0, TIME_REMINDER_EASINGS[0], TIME_REMINDER_PULSE_DURATION/2),
				PropertyTransition(self.pixels, 'brightness', 1, TIME_REMINDER_EASINGS[1], TIME_REMINDER_PULSE_DURATION/2),
			])
		if self.blink_transition != None and self.blink_transition.loop():
			self.blink_transition = None

		self.pixels.fill(0x0)
		has_more_transitions = False
		for seat_0, seat_line in enumerate(self.seat_lines):
			if len(seat_line.transitions) > 0:
				if(seat_line.transitions[0].loop()):
					seat_line.transitions = seat_line.transitions[1:]
			has_more_transitions = has_more_transitions or len(seat_line.transitions) > 0
			seat_line.line.sparkle = self.parent.state.state == STATE_START and (seat_0+1) in self.parent.seats_with_pressed_keys
			seat_line.line.draw(self.pixels)
		self.pixels.show()
		self.first_player_check()
		return has_more_transitions or self.blinks_left > 0 or self.blink_transition != None

	def on_state_update(self, state: GameState, old_state: GameState):
		for seat, line in enumerate(self.seat_definitions):
			seat_line = self.seat_lines[seat].line
			seat_color = seat_line.color
			old_line_length = seat_line.length
			new_color = None
			new_line_length = line[1]
			player = find_thing((p for p in state.players if p.seat == seat+1), None)
			if not isinstance(player, Player):
				new_color = None
			elif state.state == STATE_SIM_TURN:
				if (seat+1) in state.seat:
					# Player is involved.
					new_color = player.color.highlight
					if player.action != 'in':
						# Player has passed
						new_line_length = ceil(new_line_length / 4)
						new_color = player.color.dim
			elif state.state == STATE_ADMIN:
				if (seat+1) in state.seat:
					# Player is involved. Since it is an admin turn, all involved players gets a short line.
					new_color = player.color.dim
					new_line_length = ceil(new_line_length / 4)
			else:
				new_color = player.color.dim

			if seat_color == BLACK and new_color != None:
				seat_line.length = 0
				seat_line.color = new_color
				self.seat_lines[seat].transitions = [PropertyTransition(seat_line, 'length', new_line_length, FADE_EASE, FADE_DURATION)]
			elif seat_color != BLACK and new_color == None:
				self.seat_lines[seat].transitions = [PropertyTransition(seat_line, 'length', 0, FADE_EASE, FADE_DURATION)]
			elif seat_color != BLACK and (seat_color != new_color or old_line_length != new_line_length):
				trannies = []
				if seat_color != new_color:
					trannies.append(ColorTransitionFunction(seat_color, new_color, FADE_EASE(0, 1, FADE_DURATION)))
				if old_line_length != new_line_length:
					trannies.append(PropertyTransition(seat_line, 'length', new_line_length, FADE_EASE, FADE_DURATION))
				self.seat_lines[seat].transitions = [ParallellTransitionFunctions(*trannies)]

	def on_time_reminder(self, time_reminder_count: int):
		self.blinks_left = min(time_reminder_count, TIME_REMINDER_MAX_PULSES)
		self.blink_transition = None

	def first_player_check(self):
		# Temporarily start the first-player selection on first press. Later, wait for all buttons to be pressed.
		# all_pressed = len(self.parent.seats_with_pressed_keys) > 1
		all_pressed = len(self.parent.seats_with_pressed_keys) > 1 and len(self.parent.state.players) == len(self.parent.seats_with_pressed_keys)
		if not all_pressed:
			self.first_player_init_ts = None
		elif self.first_player_init_ts == None:
			self.first_player_init_ts = time.monotonic()
		elif time.monotonic() - self.first_player_init_ts > 1:
			self.parent.switch_to_random_start_animation()