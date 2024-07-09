from utils.settings import get_int, get_float, get_ease

# Easing function for color fades
FADE_EASE = get_ease('TABLE_FADE_EASE', 'LinearInOut')
# Duration of color fades
FADE_DURATION = get_float('TABLE_FADE_DURATION', 0.8)
# Easing function for moving the active player highlight.
HIGHLIGHT_MOVE_EASE = get_ease('TABLE_HIGHLIGHT_MOVE_EASE', 'BounceEaseOut')
# Speed of the active player highlight when moving from one player to another. (Pixels/Second)
HIGHLIGHT_MOVE_SPEED_PPS = get_int('TABLE_HIGHLIGHT_MOVE_SPEED_PPS', 36)
# Speed of comet animations, in Pixels/Second.
COMET_SPEED_PPS = get_int('TABLE_COMET_SPEED_PPS', 10)

# How long it takes to fade in and out of active state.
PAUSE_FADE_DURATION = get_float('TABLE_PAUSE_FADE_DURATION', 0.5)
# The duration of the active state, including the fade in/out
PAUSE_ACTIVE_DURATION = get_float('TABLE_PAUSE_ACTIVE_DURATION', 2.0)
# How long the table is dark for between activations.
PAUSE_INACTIVE_DURATION = get_float('TABLE_PAUSE_INACTIVE_DURATION', 1.0)
# The speed of the animation, in Pixels/Seconds
PAUSE_SPEED_PPS = get_float('TABLE_PAUSE_SPEED_PPS', 36)

# How big should the pulse be as a fraction of the edges.
ERROR_MAX_FRACTION_OF_EDGE_FOR_PULSE = get_float('TABLE_ERROR_MAX_FRACTION_OF_EDGE_FOR_PULSE', 1/3)
# Time in seconds for the pulse to go from 0 to max length, or vice versa.
ERROR_PULSE_DURATION = get_float('TABLE_ERROR_PULSE_DURATION', 1.0)
# How many pulses do we do?
ERROR_PULSE_COUNT = get_int('TABLE_ERROR_PULSE_COUNT', 2)
# The minimum time after the pules to stay black.
ERROR_PAUSE_TIME = get_float('TABLE_ERROR_PAUSE_TIME', 1.0)
# This is re-using the warn easing, but you can import anything you want from easing
ERROR_EASINGS = (get_ease('TABLE_ERROR_EASE_IN', 'CircularEaseIn'), get_ease('TABLE_ERROR_EASE_OUT', 'CircularEaseIn'))

# Easing functions to and from a warning highlight, mostly during time reminders.
TIME_REMINDER_EASINGS = (get_ease('TABLE_TIME_REMINDER_EASE_IN', 'CubicEaseInOut'), get_ease('TABLE_TIME_REMINDER_EASE_OUT', 'CubicEaseInOut'))
# The duration of a warning
TIME_REMINDER_PULSE_DURATION = get_float('TABLE_TIME_REMINDER_PULSE_DURATION', 0.5)
# Maximum times a warning is shown in series
TIME_REMINDER_MAX_PULSES = get_int('TABLE_TIME_REMINDER_MAX_PULSES', 5)

from view import View
from game_state import GameState, Player
from adafruit_pixelbuf import PixelBuf
from adafruit_led_animation.animation.rainbowcomet import RainbowComet
from adafruit_led_animation.animation.comet import Comet
from sgt_animation import SgtAnimation, SgtSolid
import time
from utils.find import find_thing
from utils.color import DisplayedColor, BLUE as BLUE_PC, RED as RED_PC, BLACK as BLACK_PC
from utils.transition import TransitionFunction, ParallellTransitionFunctions, ColorTransitionFunction, SerialTransitionFunctions
from math import ceil
import adafruit_logging as logging
log = logging.getLogger()

BLACK = BLACK_PC.base
BLUE = BLUE_PC.highlight
RED = RED_PC.highlight

class ViewTableOutline(View):
	def __init__(self,
			pixels: PixelBuf,
			seat_definitions: list[tuple[float, int]],
		):
		super().__init__()
		self.pixels = pixels
		self.seat_definitions = seat_definitions
		self.seat_count = len(seat_definitions)
		self.pixels.auto_write = False
		self.comet_refresh_rate = 1/COMET_SPEED_PPS
		self.animation = SgtAnimation(BLACK, (SgtSolid(self.pixels, 0x0), None, True))
		self.switch_to_not_connected()
	def animate(self) -> bool:
		shared_stuff_busy = super().animate()
		this_animation_busy = self.animation.animate()
		return this_animation_busy or shared_stuff_busy
	def set_connection_progress_text(self, text):
		pass
	def switch_to_playing(self, state: GameState, old_state: GameState):
		self._activate_singleplayer_animation()
	def switch_to_simultaneous_turn(self, state: GameState, old_state: GameState):
		self._activate_multiplayer_animation()
	def switch_to_admin_time(self, state: GameState, old_state: GameState):
		for player in state.players:
			if player.action == 'in':
				self._activate_multiplayer_animation()
				return
			elif player.action != None:
				self._activate_singleplayer_animation()
				return
		raise Exception('Weird admin state...')
	def switch_to_paused(self, state: GameState, old_state: GameState):
		if not isinstance(self.animation, SgtPauseAnimation):
			self.animation = SgtPauseAnimation(self)
	def switch_to_sandtimer_running(self, state: GameState, old_state: GameState):
		raise Exception('Not implemented yet')
	def switch_to_sandtimer_not_running(self, state: GameState, old_state: GameState):
		raise Exception('Not implemented yet')
	def switch_to_start(self, state: GameState, old_state: GameState):
		self._activate_multiplayer_animation()
	def switch_to_end(self, state: GameState, old_state: GameState):
		self._activate_multiplayer_animation()
	def switch_to_no_game(self):
		super().switch_to_no_game()
		self.pixels.fill(0x0)
		self.animation = SgtAnimation(
			BLACK,
			(RainbowComet(self.pixels, self.comet_refresh_rate, tail_length=round(len(self.pixels)/2), ring=True), None, True),
		)
	def switch_to_not_connected(self):
		self.pixels.fill(0x0)
		super().switch_to_not_connected()
		self.animation = SgtAnimation(
			BLUE,
			(Comet(self.pixels, self.comet_refresh_rate, 0x0, tail_length=round(len(self.pixels)/2), ring=True), None, True),
		)
	def switch_to_error(self):
		super().switch_to_error()
		if not isinstance(self.animation, SgtErrorAnimation):
			self.animation = SgtErrorAnimation(self)
	def on_state_update(self, state: GameState, old_state: GameState):
		if isinstance(self.animation, SgtSeatedAnimation):
			self.animation.on_state_update(state, old_state)
	def _activate_multiplayer_animation(self):
		if not isinstance(self.animation, SgtSeatedMultiplayerAnimation):
			self.animation = SgtSeatedMultiplayerAnimation(self)
	def _activate_singleplayer_animation(self):
		if not isinstance(self.animation, SgtSeatedSingleplayerAnimation):
			self.animation = SgtSeatedSingleplayerAnimation(self)
	def on_time_reminder(self, time_reminder_count: int):
		if isinstance(self.animation, SgtSeatedAnimation):
			self.animation.on_time_reminder(time_reminder_count)

class Line():
	def __init__(self, midpoint: float, length: float, color: DisplayedColor) -> None:
		self.midpoint = midpoint
		self.length = length
		self.color = color
	def __repr__(self):
		facts = []
		if (self.midpoint != None):
			facts.append(f'midpoint={self.midpoint}')
		if (self.length != None):
			facts.append(f'length={self.length}')
		if (self.color != None):
			facts.append(f'color={self.color}')
		return f"<Line: {', '.join(facts)}>"

class LineTransition():
	def __init__(self, line: Line, transitions: list[TransitionFunction]) -> None:
		self.line = line
		self.transitions = transitions
	def __repr__(self):
		facts = []
		if (self.line):
			facts.append(f'line={self.line}')
		if (self.transitions):
			facts.append(f'transitions={self.transitions}')
		return f"<LineTransition: {', '.join(facts)}>"

class SgtSeatedAnimation():
	def __init__(self, parent_view: ViewTableOutline, fade_to_black=True):
		self.parent = parent_view
		self.pixels=parent_view.pixels
		self.seat_definitions = parent_view.seat_definitions
		self.length = len(self.pixels)

		if fade_to_black:
			tranny = TransitionFunction(FADE_EASE(self.pixels.brightness, 0, FADE_DURATION), self.set_brightness)
			while not tranny.loop():
				self.pixels.show()
			self.pixels.fill(0x0)
			self.pixels.show()
			self.pixels.brightness = 1

	def set_brightness(self, brightness: float):
		self.pixels.brightness = brightness

	def on_state_update(self, state: GameState, old_state: GameState):
		pass

	def on_time_reminder(self, time_reminder_count: int):
		pass

	def draw_line(self, line:Line):
		lower_bound = ceil(line.midpoint - (line.length/2))
		upper_bound = ceil(line.midpoint + (line.length/2))
		for n in range (lower_bound, upper_bound):
			self.pixels[n%self.length] = line.color.current_color

class SgtErrorAnimation(SgtSeatedAnimation):
	seat_lines: list[Line]
	def __init__(self, parent_view: ViewTableOutline):
		super().__init__(parent_view)
		self.seat_lines = []
		self.seat_line_max_lengths = []
		seat_count = len(self.parent.seat_definitions)
		self.bg_color = BLACK
		self.overall_transition = SerialTransitionFunctions([])
		for i in range(seat_count):
			s1 = self.parent.seat_definitions[i]
			s2 = self.parent.seat_definitions[(i+1)%seat_count]
			self.seat_lines.append(Line(midpoint=s1[0]+s1[1]/2, length=0, color=RED))
			self.seat_line_max_lengths.append(round(min(s1[1], s2[1])*ERROR_MAX_FRACTION_OF_EDGE_FOR_PULSE))

	def set_lengths(self, progress: float):
		for i in range(len(self.parent.seat_definitions)):
			self.seat_lines[i].length = progress * self.seat_line_max_lengths[i]

	def animate(self):
		if len(self.overall_transition.fns) == 0:
			for _n in range(ERROR_PULSE_COUNT):
				fade_in = TransitionFunction(ERROR_EASINGS[0](0, 1, ERROR_PULSE_DURATION/2), callback=self.set_lengths)
				fade_out = TransitionFunction(ERROR_EASINGS[1](1, 0, ERROR_PULSE_DURATION/2), callback=self.set_lengths)
				self.overall_transition.fns.append(fade_in)
				self.overall_transition.fns.append(fade_out)
			pause = TransitionFunction(FADE_EASE(0, 0, ERROR_PAUSE_TIME), callback=lambda p: p)
			self.overall_transition.fns.append(pause)

		self.overall_transition.loop()
		self.pixels.fill(self.bg_color.current_color)
		for line in self.seat_lines:
			self.draw_line(line)
		self.pixels.show()
		return len(self.overall_transition.fns) > 1

class SgtPauseAnimation(SgtSeatedAnimation):
	def __init__(self, parent_view: ViewTableOutline):
		super().__init__(parent_view)

	def animate(self):
		if len(self.overall_transition.fns) == 0:
			fade_in = TransitionFunction(FADE_EASE(0, 1, PAUSE_FADE_DURATION), callback=self.set_brightness)
			be_bright = TransitionFunction(FADE_EASE(1, 1, max(0, PAUSE_ACTIVE_DURATION-(2*PAUSE_FADE_DURATION))), callback=self.set_brightness)
			fade_out = TransitionFunction(FADE_EASE(1, 0, PAUSE_FADE_DURATION), callback=self.set_brightness)
			be_dark = TransitionFunction(FADE_EASE(0, 0, PAUSE_INACTIVE_DURATION), callback=self.set_brightness)
			self.overall_transition.fns.append(fade_in)
			self.overall_transition.fns.append(be_bright)
			self.overall_transition.fns.append(fade_out)
			self.overall_transition.fns.append(be_dark)

		self.overall_transition.loop()
		self.pixels.fill(self.bg_color.current_color)
		now = time.monotonic()
		time_passed = now - self.last_animation_ts
		pixels_moved = PAUSE_SPEED_PPS * time_passed
		for line in self.seat_lines:
			line.midpoint = (line.midpoint + pixels_moved) % self.length
			self.draw_line(line)
		self.pixels.show()
		self.last_animation_ts = now
		return len(self.overall_transition.fns) > 1

	def on_state_update(self, state: GameState, old_state: GameState):
		active_player = state.get_active_player()
		sd = self.parent.seat_definitions[active_player.seat-1] if active_player else self.parent.seat_definitions[0]
		color = active_player.color if active_player else state.color
		self.fg_color = color.highlight
		self.bg_color = color.dim
		length = len(self.parent.pixels)
		start_pixel = sd[0]
		mid_pixel = (start_pixel + round(length/2)) % length
		line_1 = Line(midpoint=start_pixel, length=sd[1], color=self.fg_color)
		line_2 = Line(midpoint=mid_pixel, length=sd[1], color=self.fg_color)
		self.seat_lines = [line_1, line_2]
		self.start_ts = time.monotonic()
		self.last_animation_ts = time.monotonic()
		self.overall_transition = SerialTransitionFunctions([])

	def set_line_midpoint(self, midpoint: float, line: Line):
		line.midpoint = midpoint % self.length

class SgtSeatedMultiplayerAnimation(SgtSeatedAnimation):
	def __init__(self, parent_view: ViewTableOutline):
		super().__init__(parent_view)
		self.seat_lines = list(LineTransition(Line(midpoint=s[0], length=0, color=BLACK), transitions=[]) for s in self.seat_definitions)
		self.blinks_left = 0
		self.blink_transition = None
		self.current_times = None
		self.state = None

	def animate(self):
		if self.blink_transition == None and self.blinks_left > 0:
			self.blinks_left = self.blinks_left - 1
			self.blink_transition = SerialTransitionFunctions([
				TransitionFunction(TIME_REMINDER_EASINGS[0](self.pixels.brightness, 0, TIME_REMINDER_PULSE_DURATION/2), self.set_overall_brightness),
				TransitionFunction(TIME_REMINDER_EASINGS[1](0, self.pixels.brightness, TIME_REMINDER_PULSE_DURATION/2), self.set_overall_brightness),
			])
		if self.blink_transition != None and self.blink_transition.loop():
			self.blink_transition = None

		self.pixels.fill(0x0)
		has_more_transitions = False
		for seat_line in self.seat_lines:
			if len(seat_line.transitions) > 0:
				if(seat_line.transitions[0].loop()):
					seat_line.transitions = seat_line.transitions[1:]
			has_more_transitions = has_more_transitions or len(seat_line.transitions) > 0
			self.draw_line(seat_line.line)
		self.pixels.show()
		return has_more_transitions or self.blinks_left > 0 or self.blink_transition != None

	def set_overall_brightness(self, brightness):
		self.pixels.brightness = brightness
	def set_line_length(self, line_length: float, seat: int):
		self.seat_lines[seat].line.length = line_length

	def on_state_update(self, state: GameState, old_state: GameState):
		for seat, line in enumerate(self.seat_definitions):
			seat_color = self.seat_lines[seat].line.color
			old_line_length = self.seat_lines[seat].line.length
			new_color = None
			new_line_length = line[1]
			player = find_thing((p for p in state.players if p.seat == seat+1), None)
			if not isinstance(player, Player):
				new_color = None
			elif state.state == 'si':
				if (seat+1) in state.seat:
					# Player is involved.
					new_color = player.color.highlight
					if player.action != 'in':
						# Player has passed
						new_line_length = ceil(new_line_length / 4)
						new_color = player.color.dim
			elif state.state == 'ad':
				if (seat+1) in state.seat:
					# Player is involved. Since it is an admin turn, all involved players gets a short line.
					new_color = player.color.dim
					new_line_length = ceil(new_line_length / 4)
			else:
				new_color = player.color.highlight

			if seat_color == BLACK and new_color != None:
				self.seat_lines[seat].line.length = 0
				self.seat_lines[seat].line.color = new_color
				self.seat_lines[seat].transitions = [TransitionFunction(FADE_EASE(0, new_line_length, FADE_DURATION), self.set_line_length, seat)]
			elif seat_color != BLACK and new_color == None:
				self.seat_lines[seat].transitions = [TransitionFunction(FADE_EASE(old_line_length, 0, FADE_DURATION), self.set_line_length, seat)]
			elif seat_color != BLACK and (seat_color != new_color or old_line_length != new_line_length):
				trannies = []
				if seat_color != new_color:
					trannies.append(ColorTransitionFunction(seat_color, new_color, FADE_EASE(0, 1, FADE_DURATION)))
				if old_line_length != new_line_length:
					trannies.append(TransitionFunction(FADE_EASE(old_line_length, new_line_length, FADE_DURATION), self.set_line_length, seat))
				self.seat_lines[seat].transitions = [ParallellTransitionFunctions(*trannies)]
		while self.animate():
			pass

	def on_time_reminder(self, time_reminder_count: int):
		self.blinks_left = min(time_reminder_count, TIME_REMINDER_MAX_PULSES)
		self.blink_transition = None

class SgtSeatedSingleplayerAnimation(SgtSeatedAnimation):
	seat_line: LineTransition
	color_background: DisplayedColor
	blink_transition: SerialTransitionFunctions | None

	def __init__(self, parent_view: ViewTableOutline):
		super().__init__(parent_view)
		self.color_background = BLACK
		self.seat_line = None
		self.blinks_left = 0
		self.blink_transition = None
		self.current_times = None

	def animate(self):
		if self.seat_line == None:
			self.pixels.fill(0x0)
			self.pixels.show()
			return False

		if self.blink_transition == None and self.blinks_left > 0:
			self.blinks_left = self.blinks_left - 1
			self.blink_transition = SerialTransitionFunctions([
				ColorTransitionFunction(self.color_background, self.player_fg_color, TIME_REMINDER_EASINGS[0](0, 1, TIME_REMINDER_PULSE_DURATION/2)),
				ColorTransitionFunction(self.color_background, self.player_bg_color, TIME_REMINDER_EASINGS[1](0, 1, TIME_REMINDER_PULSE_DURATION/2)),
			])
		if self.blink_transition != None and self.blink_transition.loop():
			self.blink_transition = None
		if len(self.seat_line.transitions) > 0:
			if(self.seat_line.transitions[0].loop()):
				self.seat_line.transitions = self.seat_line.transitions[1:]
		self.pixels.fill(self.color_background.current_color)
		self.draw_line(self.seat_line.line)
		self.pixels.show()
		return len(self.seat_line.transitions) > 0 or self.blinks_left > 0 or self.blink_transition != None

	def set_line_midpoint(self, midpoint: float):
		self.seat_line.line.midpoint = midpoint % self.length
	def set_line_length(self, length: float):
		self.seat_line.line.length = length

	def on_state_update(self, state: GameState, old_state: GameState):
		active_player = state.get_active_player()

		if active_player == None:
			raise Exception('No active player!')

		player_line_midpoint, player_line_length = self.seat_definitions[active_player.seat-1]

		if self.seat_line == None:
			self.seat_line = LineTransition(Line(player_line_midpoint, 0, active_player.color.black), [])

		line_transitions = []

		self.player_bg_color = active_player.color.dim if state.state == 'pl' else None
		self.player_fg_color = active_player.color.highlight

		from_pixel = self.seat_line.line.midpoint
		to_pixel = player_line_midpoint
		line_ease_duration = FADE_DURATION
		line_ease = FADE_EASE
		if from_pixel != to_pixel:
			steps_if_adding = (to_pixel-from_pixel) % self.length
			steps_if_subtracting = (from_pixel-to_pixel) % self.length
			line_ease_duration = min(steps_if_adding, steps_if_subtracting)/HIGHLIGHT_MOVE_SPEED_PPS
			line_ease = HIGHLIGHT_MOVE_EASE
			if (steps_if_adding <= steps_if_subtracting):
				line_transitions.append(TransitionFunction(line_ease(start=from_pixel, end=from_pixel+steps_if_adding, duration=line_ease_duration), callback=self.set_line_midpoint))
			else:
				line_transitions.append(TransitionFunction(line_ease(start=from_pixel, end=from_pixel-steps_if_subtracting, duration=line_ease_duration), callback=self.set_line_midpoint))
		if self.seat_line.line.color != self.player_fg_color:
			line_transitions.append(ColorTransitionFunction(self.seat_line.line.color, self.player_fg_color, line_ease(duration=line_ease_duration)))
		if self.seat_line.line.length != player_line_length:
			line_transitions.append(TransitionFunction(line_ease(start=self.seat_line.line.length, end=player_line_length, duration=line_ease_duration), callback=self.set_line_length))

		if from_pixel != to_pixel:
			# We want to first fade out the current background color to black,
			# Then move the player line to the new position, changing its color while doing so,
			# and finally fade in the background to the new color.
			trans_fade_out = ColorTransitionFunction(self.color_background, BLACK, FADE_EASE(0, 1, FADE_DURATION))
			trans_fade_in = ColorTransitionFunction(self.color_background, self.player_bg_color, FADE_EASE(0, 1, FADE_DURATION))
			self.seat_line.transitions = [
				trans_fade_out,
				ParallellTransitionFunctions(*line_transitions),
				trans_fade_in,
			]
		else:
			self.seat_line.transitions = []
			if len(line_transitions) > 0:
				self.seat_line.transitions.append(ParallellTransitionFunctions(*line_transitions))
			if self.color_background != self.player_bg_color:
				self.seat_line.transitions.append(ColorTransitionFunction(self.color_background, self.player_bg_color, easing=FADE_EASE(0, 1, FADE_DURATION)))

		while self.animate():
			pass

	def on_time_reminder(self, time_reminder_count: int):
		self.blinks_left = min(time_reminder_count, TIME_REMINDER_MAX_PULSES)
		self.blink_transition = None