from utils.settings import get_float, get_int, get_ease

# How fast does the sparks move?
PAUSE_SPEED_PPS_MIN = get_int('TABLE_PAUSE_SPEED_PPS_MIN', 1)
PAUSE_SPEED_PPS_MAX = get_int('TABLE_PAUSE_SPEED_PPS_MAX', 5)
PAUSE_SPEED_PPS_DISTRIBUTION = get_ease('TABLE_PAUSE_SPEED_PPS_DISTRIBUTION', 'CubicEaseOutIn')
PAUSE_LOCATION_EASE = get_ease('TABLE_PAUSE_LOCATION_EASE', 'LinearInOut')

# How far do the pixels move? 0 to 0.5 (0.5 being all the way around the table)
PAUSE_DISTANCE_MIN = get_float('TABLE_PAUSE_DISTANCE_MIN', 0.2)
PAUSE_DISTANCE_MAX = get_float('TABLE_PAUSE_DISTANCE_MAX', 0.5)
PAUSE_DISTANCE_DISTRIBUTION = get_ease('TABLE_PAUSE_DISTANCE_DISTRIBUTION', 'CubicEaseOutIn')

# How bright are the pixels, and how fast do they fade out towards the end?
PAUSE_BRIGHTNESS_MIN = get_float('TABLE_PAUSE_BRIGHTNESS_MIN', 0.01)
PAUSE_BRIGHTNESS_MAX = get_float('TABLE_PAUSE_BRIGHTNESS_MAX', 0.4)
PAUSE_BRIGHTNESS_DISTRIBUTION = get_ease('TABLE_PAUSE_BRIGHTNESS_DISTRIBUTION', 'CubicEaseOutIn')
PAUSE_FADE_OUT_EASE = get_ease('TABLE_PAUSE_FADE_OUT_EASE', 'QuarticEaseIn')

# How frequent to we potentially spawn a new spark?
PAUSE_SPAWN_PAUSE_SEC = get_float('TABLE_PAUSE_SPAWN_PAUSE_SEC', 0.2)
# How probable is it that we spawn a new spark?
PAUSE_SPAWN_PROBABILITY = get_float('TABLE_PAUSE_SPAWN_PROBABILITY', 0.5)

from seated_animation.seated_animation import SgtSeatedAnimation
from view_table_outline import ViewTableOutline
from game_state import GameState
import time
from random import uniform, choice, random
import adafruit_fancyled.adafruit_fancyled as fancy

from utils.transition import PropertyTransition, ParallellTransitionFunctions
import adafruit_logging as logging
log = logging.getLogger()

speed_easing = PAUSE_SPEED_PPS_DISTRIBUTION(PAUSE_SPEED_PPS_MIN, PAUSE_SPEED_PPS_MAX)
brightness_easing = PAUSE_BRIGHTNESS_DISTRIBUTION(PAUSE_BRIGHTNESS_MIN, PAUSE_BRIGHTNESS_MAX)
distance_easing = PAUSE_DISTANCE_DISTRIBUTION(PAUSE_DISTANCE_MIN, PAUSE_DISTANCE_MAX)

class Spark():
	def __init__(self, start: float, end: float):
		self.location = start
		speed = speed_easing(random())
		self.brightness = brightness_easing(random())
		duration = (end-start)/speed if end > start else (start-end)/speed
		tranny_location = PropertyTransition(self, 'location', end, PAUSE_LOCATION_EASE, duration)
		tranny_fade_out = PropertyTransition(self, 'brightness', 0, PAUSE_FADE_OUT_EASE, duration)
		self.transition = ParallellTransitionFunctions(tranny_fade_out, tranny_location)


class SgtPauseAnimation(SgtSeatedAnimation):
	sparks: list[Spark]
	def __init__(self, parent_view: ViewTableOutline):
		super().__init__(parent_view)
		self.sparks = []
		self.last_spawn_ts = 0

	def animate(self):
		if not self.color:
			return

		arr = [0x0 for i in range(self.length)]
		self.pixels.fill(0x0)
		if time.monotonic() - self.last_spawn_ts > PAUSE_SPAWN_PAUSE_SEC:
			self.last_spawn_ts = time.monotonic()
			if random() < PAUSE_SPAWN_PROBABILITY:
				start = self.seat_definitions[self.active_player.seat-1][0] if self.active_player else uniform(0, len(self.pixels))
				end = start + choice([1, -1]) * len(self.pixels) * distance_easing(random())
				self.sparks.append(Spark(start, end))
		for spark in self.sparks:
			if spark.transition.loop():
				self.sparks.remove(spark)
			else:
				val = fancy.gamma_adjust(self.color, brightness=spark.brightness).pack()
				index = round(spark.location) % self.length
				arr[index] = max(val, arr[index])
		self.pixels[0:self.length] = arr
		self.pixels.show()

	def on_state_update(self, state: GameState, old_state: GameState):
		self.active_player = state.get_active_player()
		self.color = state.color.fancy
