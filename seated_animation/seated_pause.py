from utils.settings import get_float

# How long it takes to fade in and out of active state.
PAUSE_FADE_DURATION = get_float('TABLE_PAUSE_FADE_DURATION', 0.5)
# The duration of the active state, including the fade in/out
PAUSE_ACTIVE_DURATION = get_float('TABLE_PAUSE_ACTIVE_DURATION', 2.0)
# How long the table is dark for between activations.
PAUSE_INACTIVE_DURATION = get_float('TABLE_PAUSE_INACTIVE_DURATION', 1.0)
# The speed of the animation, in Pixels/Seconds
PAUSE_SPEED_PPS = get_float('TABLE_PAUSE_SPEED_PPS', 36)

from seated_animation.seated_animation import SgtSeatedAnimation, Line, FADE_EASE
from view_table_outline import ViewTableOutline
from game_state import GameState
import time

from utils.transition import PropertyTransition, SerialTransitionFunctions, NoOpTransition
import adafruit_logging as logging
log = logging.getLogger()

class SgtPauseAnimation(SgtSeatedAnimation):
	def __init__(self, parent_view: ViewTableOutline):
		super().__init__(parent_view)

	def animate(self):
		if len(self.overall_transition.fns) == 0:
			fade_in = PropertyTransition(self.pixels, 'brightness', 1, FADE_EASE, PAUSE_FADE_DURATION)
			be_bright = NoOpTransition(max(0, PAUSE_ACTIVE_DURATION-(2*PAUSE_FADE_DURATION)))
			fade_out = PropertyTransition(self.pixels, 'brightness', 0, FADE_EASE, PAUSE_FADE_DURATION)
			be_dark = NoOpTransition(PAUSE_INACTIVE_DURATION)
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
			line.draw()
		self.pixels.show()
		self.last_animation_ts = now
		return len(self.overall_transition.fns) > 1

	def on_state_update(self, state: GameState, old_state: GameState):
		active_player = state.get_active_player()
		sd = self.parent.seat_definitions[active_player.seat-1] if active_player else self.parent.seat_definitions[0]
		color = active_player.color if active_player else state.color
		self.fg_color = color.highlight
		self.bg_color = color.dim
		start_pixel = sd[0]
		mid_pixel = start_pixel + len(self.parent.pixels)/2
		line_1 = Line(pixels=self.parent.pixels, midpoint=start_pixel, length=sd[1], color=self.fg_color)
		line_2 = Line(pixels=self.parent.pixels, midpoint=mid_pixel, length=sd[1], color=self.fg_color)
		self.seat_lines = [line_1, line_2]
		self.start_ts = time.monotonic()
		self.last_animation_ts = time.monotonic()
		self.overall_transition = SerialTransitionFunctions([])
