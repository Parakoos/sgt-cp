from utils.settings import get_int, get_float, get_ease

# Easing function for moving the active player highlight.
HIGHLIGHT_MOVE_EASE = get_ease('TABLE_HIGHLIGHT_MOVE_EASE', 'BounceEaseOut')
# Speed of the active player highlight when moving from one player to another. (Pixels/Second)
HIGHLIGHT_MOVE_SPEED_PPS = get_int('TABLE_HIGHLIGHT_MOVE_SPEED_PPS', 36)

from seated_animation.seated_animation import SgtSeatedAnimation, Line, LineTransition, FADE_EASE, FADE_DURATION, TIME_REMINDER_EASINGS, TIME_REMINDER_MAX_PULSES, TIME_REMINDER_PULSE_DURATION
from view_table_outline import ViewTableOutline, BLACK
from game_state import GameState
from utils.color import DisplayedColor
from utils.transition import PropertyTransition, SerialTransitionFunctions, ColorTransitionFunction, ParallellTransitionFunctions
import adafruit_logging as logging
log = logging.getLogger()

class SgtSeatedSingleplayerAnimation(SgtSeatedAnimation):
	seat_line: LineTransition
	color_background: DisplayedColor
	blink_transition: SerialTransitionFunctions | None

	def __init__(self, parent_view: ViewTableOutline):
		super().__init__(parent_view)
		self.color_background = BLACK.copy()
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
				self.seat_line.line.midpoint = self.seat_line.line.midpoint % self.length
		self.pixels.fill(self.color_background.current_color)
		self.seat_line.line.draw()
		self.pixels.show()
		return len(self.seat_line.transitions) > 0 or self.blinks_left > 0 or self.blink_transition != None

	def on_state_update(self, state: GameState, old_state: GameState):
		active_player = state.get_active_player()

		if active_player == None:
			raise Exception('No active player!')

		player_line_midpoint, player_line_length = self.seat_definitions[active_player.seat-1]

		if self.seat_line == None:
			self.seat_line = LineTransition(Line(self.parent.pixels, player_line_midpoint, 0, active_player.color.black), [])

		line_transitions = []

		self.player_bg_color = active_player.color.dim if state.state == 'pl' else None
		self.player_fg_color = active_player.color.highlight

		line = self.seat_line.line
		from_pixel = line.midpoint
		to_pixel = player_line_midpoint
		line_ease_duration = FADE_DURATION
		line_ease = FADE_EASE
		if from_pixel != to_pixel:
			steps_if_adding = (to_pixel-from_pixel) % self.length
			steps_if_subtracting = (from_pixel-to_pixel) % self.length
			line_ease_duration = min(steps_if_adding, steps_if_subtracting)/HIGHLIGHT_MOVE_SPEED_PPS
			line_ease = HIGHLIGHT_MOVE_EASE
			if (steps_if_adding <= steps_if_subtracting):
				line_transitions.append(PropertyTransition(line, 'midpoint', from_pixel+steps_if_adding, line_ease, line_ease_duration))
			else:
				line_transitions.append(PropertyTransition(line, 'midpoint', from_pixel-steps_if_subtracting, line_ease, line_ease_duration))
		if line.color != self.player_fg_color:
			line_transitions.append(ColorTransitionFunction(line.color, self.player_fg_color, line_ease(duration=line_ease_duration)))
		if line.length != player_line_length:
			line_transitions.append(PropertyTransition(line, 'length', player_line_length, line_ease, line_ease_duration))

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

	def on_time_reminder(self, time_reminder_count: int):
		self.blinks_left = min(time_reminder_count, TIME_REMINDER_MAX_PULSES)
		self.blink_transition = None