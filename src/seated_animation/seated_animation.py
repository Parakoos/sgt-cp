from utils.settings import get_int, get_float, get_ease

# Easing function for color fades
FADE_EASE = get_ease('TABLE_FADE_EASE', 'LinearInOut')
# Duration of color fades
FADE_DURATION = get_float('TABLE_FADE_DURATION', 0.8)

# Easing functions to and from a warning highlight, mostly during time reminders.
TIME_REMINDER_EASINGS = (get_ease('TABLE_TIME_REMINDER_EASE_IN', 'CubicEaseInOut'), get_ease('TABLE_TIME_REMINDER_EASE_OUT', 'CubicEaseInOut'))
# The duration of a warning
TIME_REMINDER_PULSE_DURATION = get_float('TABLE_TIME_REMINDER_PULSE_DURATION', 0.5)
# Maximum times a warning is shown in series
TIME_REMINDER_MAX_PULSES = get_int('TABLE_TIME_REMINDER_MAX_PULSES', 5)

# Easing functions for a sparkle
SPARKLE_EASINGS = (get_ease('TABLE_SPARKLE_EASE_IN', 'CubicEaseInOut'), get_ease('TABLE_SPARKLE_EASE_OUT', 'CubicEaseInOut'))
# How much of a side should be covered by sparkles? Between 0 and 1
SPARKLE_COVER = get_float('TABLE_SPARKLE_COVER', 1.0)
# The range of duration of a given sparkle.
SPARKLE_DURATION_MIN = get_float('TABLE_SPARKLE_DURATION_MIN', 0.1)
SPARKLE_DURATION_MAX = get_float('TABLE_SPARKLE_DURATION_MAX', 0.5)

from game_state import GameState
from adafruit_pixelbuf import PixelBuf
from view_table_outline import ViewTableOutline
from utils.color import DisplayedColor
from utils.transition import TransitionFunction, SerialTransitionFunctions, PropertyTransition
from random import uniform, choice
import adafruit_fancyled.adafruit_fancyled as fancy
import adafruit_logging as logging
log = logging.getLogger()

class Line():
	sparkles: list[tuple[int, SerialTransitionFunctions]]
	def __init__(self, pixels: PixelBuf, midpoint: float, length: float, color: DisplayedColor) -> None:
		self.pixels = pixels
		self.midpoint = midpoint % len(pixels)
		self.length = length
		self.color = color
		self.sparkle = False
		self.sparkles = list()
	def draw(self):
		lower_bound = round(self.midpoint - (self.length/2))
		upper_bound = round(self.midpoint + (self.length/2))
		diff = upper_bound - lower_bound
		for n in range(lower_bound, upper_bound):
			self.pixels[n % len(self.pixels)] = self.color.current_color
		if self.sparkle:
			if len(self.sparkles) < round(self.length * SPARKLE_COVER):
				unused_indices = [i for i in range(diff)]
				for spark in self.sparkles:
					unused_indices.remove(spark[0])
				if len(unused_indices) > 0:
					spark_index = choice(unused_indices)
					duration = uniform(SPARKLE_DURATION_MIN, SPARKLE_DURATION_MAX)
					sparkle_transition = SerialTransitionFunctions([
						TransitionFunction(SPARKLE_EASINGS[0](start=0, end=1, duration=duration/2)),
						TransitionFunction(SPARKLE_EASINGS[1](start=1, end=0, duration=duration/2)),
					])
					self.sparkles.append((spark_index, sparkle_transition))
		for spark in self.sparkles:
			tranny = spark[1].fns[0]
			done = spark[1].loop()
			if done:
				self.sparkles.remove(spark)
			else:
				progress = tranny.value
				brightness = self.color.brightness * (1-progress) + progress
				self.pixels[(lower_bound + spark[0]) % len(self.pixels)] = fancy.gamma_adjust(self.color.fancy_color, brightness=brightness).pack()

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
			tranny = PropertyTransition(self.pixels, 'brightness', 0, FADE_EASE, FADE_DURATION)
			while not tranny.loop():
				self.pixels.show()
			self.pixels.fill(0x0)
			self.pixels.show()
			self.pixels.brightness = 1

	def on_state_update(self, state: GameState, old_state: GameState):
		pass

	def on_time_reminder(self, time_reminder_count: int):
		pass
