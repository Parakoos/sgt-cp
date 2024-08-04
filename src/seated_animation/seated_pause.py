from utils.settings import get_float

# The speed of the animation, in Pixels/Seconds
PAUSE_SPEED_PPS = get_float('TABLE_PAUSE_SPEED_PPS', 36)

from seated_animation.seated_animation import SgtSeatedAnimation, Line
from view_table_outline import ViewTableOutline
from game_state import GameState
import time

import adafruit_logging as logging
log = logging.getLogger()

class SgtPauseAnimation(SgtSeatedAnimation):
	def __init__(self, parent_view: ViewTableOutline):
		super().__init__(parent_view)

	def animate(self):
		self.pixels.fill(self.bg_color.current_color)
		now = time.monotonic()
		time_passed = now - self.last_animation_ts
		pixels_moved = PAUSE_SPEED_PPS * time_passed
		for line in self.seat_lines:
			line.midpoint = (line.midpoint + pixels_moved) % self.length
			line.draw(self.pixels)
		self.pixels.show()
		self.last_animation_ts = now
		return False

	def on_state_update(self, state: GameState, old_state: GameState):
		active_player = state.get_active_player()
		sd = self.parent.seat_definitions[active_player.seat-1] if active_player else self.parent.seat_definitions[0]
		color = active_player.color if active_player else state.color
		self.fg_color = color.highlight
		self.bg_color = color.dim
		start_pixel = sd[0]
		mid_pixel = start_pixel + len(self.parent.pixels)/2
		line_1 = Line(midpoint=start_pixel, length=sd[1], color=self.fg_color)
		line_2 = Line(midpoint=mid_pixel, length=sd[1], color=self.fg_color)
		self.seat_lines = [line_1, line_2]
		self.start_ts = time.monotonic()
		self.last_animation_ts = time.monotonic()
