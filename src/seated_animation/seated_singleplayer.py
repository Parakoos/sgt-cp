from utils.settings import get_int, get_ease, get_float

# Easing function for moving the active player highlight.
HIGHLIGHT_MOVE_EASE = get_ease('TABLE_HIGHLIGHT_MOVE_EASE', 'BounceEaseOut')
# Speed of the active player highlight when moving from one player to another. (Pixels/Second)
HIGHLIGHT_MOVE_SPEED_PPS = get_int('TABLE_HIGHLIGHT_MOVE_SPEED_PPS', 36)

# How many pixels wide should each time dot be?
DOTS_WIDTH = get_float('TABLE_DOTS_WIDTH', 2.0)
# How many pixels is it between each dot?
DOTS_SEPARATION = get_float('TABLE_DOTS_SEPARATION', 3.0)
# How bright are the dots?
DOTS_BRIGHTNESS = get_float('TABLE_DOTS_BRIGHTNESS', 1.0)

# How fast does the sparks move?
SPARK_SPEED_PPS_MIN = get_int('TABLE_SPARK_SPEED_PPS_MIN', 1)
SPARK_SPEED_PPS_MAX = get_int('TABLE_SPARK_SPEED_PPS_MAX', 5)
SPARK_SPEED_PPS_DISTRIBUTION = get_ease('TABLE_SPARK_SPEED_PPS_DISTRIBUTION', 'CubicEaseOutIn')
SPARK_LOCATION_EASE = get_ease('TABLE_SPARK_LOCATION_EASE', 'LinearInOut')

# How far do the pixels move? 0 to 0.5 (0.5 being all the way around the table)
SPARK_DISTANCE_MIN = get_float('TABLE_SPARK_DISTANCE_MIN', 0.3)
SPARK_DISTANCE_MAX = get_float('TABLE_SPARK_DISTANCE_MAX', 0.5)
SPARK_DISTANCE_DISTRIBUTION = get_ease('TABLE_SPARK_DISTANCE_DISTRIBUTION', 'QuadEaseOutIn')

# How bright are the pixels, and how fast do they fade out towards the end?
SPARK_BRIGHTNESS_MIN = get_float('TABLE_SPARK_BRIGHTNESS_MIN', 0.01)
SPARK_BRIGHTNESS_MAX = get_float('TABLE_SPARK_BRIGHTNESS_MAX', 0.4)
SPARK_BRIGHTNESS_LINE = get_float('TABLE_SPARK_BRIGHTNESS_LINE', 0.2)
SPARK_BRIGHTNESS_DISTRIBUTION = get_ease('TABLE_SPARK_BRIGHTNESS_DISTRIBUTION', 'QuadEaseOutIn')
SPARK_FADE_OUT_EASE = get_ease('TABLE_SPARK_FADE_OUT_EASE', 'QuarticEaseIn')

# How frequent to we potentially spawn a new spark?
SPARK_SPAWN_PAUSE_SEC = get_float('TABLE_SPARK_SPAWN_PAUSE_SEC', 0.2)
# How probable is it that we spawn a new spark?
SPARK_SPAWN_PROBABILITY = get_float('TABLE_SPARK_SPAWN_PROBABILITY', 0.5)
# How many pixels wide should each spark be?
SPARK_SPARK_WIDTH = get_float('TABLE_SPARK_WIDTH', 1)

from seated_animation.seated_animation import SgtSeatedAnimation, Line, LineTransition, TIME_REMINDER_EASINGS, TIME_REMINDER_MAX_PULSES, TIME_REMINDER_PULSE_DURATION
from view_table_outline import ViewTableOutline, BLACK, FADE_EASE, FADE_DURATION
from game_state import GameState, Player, STATE_PLAYING, STATE_ADMIN
from utils.color import DisplayedColor
from utils.transition import PropertyTransition, SerialTransitionFunctions, ColorTransitionFunction, ParallellTransitionFunctions, CallbackTransitionFunction
import adafruit_fancyled.adafruit_fancyled as fancy
from random import uniform, choice, random
from time import monotonic
from math import modf
import adafruit_logging as logging
log = logging.getLogger()

class Spark():
	speed_easing = SPARK_SPEED_PPS_DISTRIBUTION(SPARK_SPEED_PPS_MIN, SPARK_SPEED_PPS_MAX)
	brightness_easing = SPARK_BRIGHTNESS_DISTRIBUTION(SPARK_BRIGHTNESS_MIN, SPARK_BRIGHTNESS_MAX)
	distance_easing = SPARK_DISTANCE_DISTRIBUTION(SPARK_DISTANCE_MIN, SPARK_DISTANCE_MAX)

	def __init__(self, start: float, end: float):
		self.location = end
		speed = Spark.speed_easing(random())
		self.brightness = 0
		duration = (end-start)/speed if end > start else (start-end)/speed
		tranny_location = PropertyTransition(self, 'location', start, SPARK_LOCATION_EASE, duration)
		tranny_fade_out = PropertyTransition(self, 'brightness', Spark.brightness_easing(random()), FADE_EASE, FADE_DURATION)
		self.transition = ParallellTransitionFunctions(tranny_fade_out, tranny_location)

class SgtSeatedSingleplayerAnimation(SgtSeatedAnimation):
	seat_line: LineTransition
	color_background: DisplayedColor
	blink_transition: SerialTransitionFunctions | None
	sparks: list[Spark]

	def __init__(self, parent_view: ViewTableOutline, random_first_player: Player|None = None):
		super().__init__(parent_view)
		self.color_background = BLACK.copy()
		self.dot_brightness = DOTS_BRIGHTNESS
		self.seat_line = None
		self.blinks_left = 0
		self.blink_transition = None
		self.current_times = None
		self.sparks = []
		self.last_spawn_ts = 0
		if random_first_player:
			player_line_midpoint, player_line_length = self.seat_definitions[random_first_player.seat-1]
			self.seat_line = LineTransition(Line(player_line_midpoint, player_line_length, random_first_player.color.highlight), [])
			self.color_background = random_first_player.color.dim
			self.seat_line.line.sparkle = True

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

		# Set BG color
		arr = [self.color_background.current_color for i in range(self.length)]

		# Show minute counter
		if self.parent.state.state == STATE_PLAYING:
			non_player_line_length = self.length - self.seat_line.line.length
			player_line_edge = self.seat_line.line.midpoint + self.seat_line.line.length/2
			min_fraction, mins = modf(self.parent.state.get_current_timings().turn_time/60)
			dot_count = mins + 1
			dots_travel_length = non_player_line_length + mins*(DOTS_WIDTH+DOTS_SEPARATION)
			time_dots_location_progress = 1 - 2 * (min_fraction if min_fraction < 0.5 else 1-min_fraction)
			time_dots_location = dots_travel_length * time_dots_location_progress

			for i in range(dot_count):
				pixel_location = player_line_edge + time_dots_location-i*(DOTS_SEPARATION+DOTS_WIDTH)
				if player_line_edge <= pixel_location and pixel_location <= (non_player_line_length + player_line_edge):
					i_low, b_low, i_high, b_high, mids = self.calc_dot(pixel_location, DOTS_WIDTH, self.dot_brightness, self.color_background.brightness)
					arr[i_low] = fancy.gamma_adjust(self.color_background.fancy_color, brightness=b_low).pack()
					arr[i_high] = fancy.gamma_adjust(self.color_background.fancy_color, brightness=b_high).pack()
					for i_mid in mids:
						arr[int(i_mid) % self.length] = fancy.gamma_adjust(self.color_background.fancy_color, brightness=self.dot_brightness).pack()
		elif self.parent.state.state == STATE_ADMIN:
			# Spawn Sparks
			if monotonic() - self.last_spawn_ts > SPARK_SPAWN_PAUSE_SEC:
				self.last_spawn_ts = monotonic()
				if random() < SPARK_SPAWN_PROBABILITY:
					start = self.seat_definitions[self.active_player.seat-1][0] if self.active_player else uniform(0, self.length)
					end = start + choice([1, -1]) * self.length * Spark.distance_easing(random())
					self.sparks.append(Spark(start, end))
			# Draw Sparks
			for spark in self.sparks:
				if spark.transition.loop():
					self.sparks.remove(spark)
				else:
					i_low, b_low, i_high, b_high, mids = self.calc_dot(spark.location, SPARK_SPARK_WIDTH, spark.brightness)
					arr[i_low] = max(arr[i_low], fancy.gamma_adjust(self.parent.state.color.fancy, brightness=b_low).pack())
					arr[i_high] = max(arr[i_high], fancy.gamma_adjust(self.parent.state.color.fancy, brightness=b_high).pack())
					for i_mid in mids:
						arr[int(i_mid) % self.length] = max(arr[int(i_mid) % self.length], fancy.gamma_adjust(self.parent.state.color.fancy, brightness=spark.brightness).pack())

		# Draw the player line and show result
		self.seat_line.line.draw(arr)
		self.pixels[0:self.length] = arr
		self.pixels.show()
		return len(self.seat_line.transitions) > 0 or self.blinks_left > 0 or self.blink_transition != None

	def on_state_update(self, state: GameState, old_state: GameState):
		active_player = state.get_active_player()

		if active_player == None:
			raise Exception('No active player!')
		self.active_player = active_player

		player_line_midpoint, player_line_length = self.seat_definitions[active_player.seat-1]

		if self.seat_line == None:
			self.seat_line = LineTransition(Line(player_line_midpoint, 0, active_player.color.black), [])

		line_transitions = []

		about_to_start = state.get_current_timings().total_play_time == 0

		self.player_bg_color = active_player.color.dim if state.state == STATE_PLAYING or about_to_start else None
		self.player_fg_color = active_player.color.highlight

		line = self.seat_line.line
		line.sparkle = about_to_start
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
			trans_fade_out = ParallellTransitionFunctions(
				CallbackTransitionFunction(FADE_EASE(self.color_background.brightness, 0, FADE_DURATION), lambda b: self.color_background.update(self.color_background.fancy_color, b)),
				PropertyTransition(self, 'dot_brightness', 0.0, FADE_EASE, FADE_DURATION),
			)
			self.seat_line.transitions = [
				trans_fade_out,
				ParallellTransitionFunctions(*line_transitions),
			]
			if state.stateType != 'et':
				trans_fade_in = ParallellTransitionFunctions(
					CallbackTransitionFunction(FADE_EASE(0, active_player.color.dim.brightness, FADE_DURATION), lambda b: self.color_background.update(active_player.color.fancy, b)),
					PropertyTransition(self, 'dot_brightness', DOTS_BRIGHTNESS, FADE_EASE, FADE_DURATION),
				)
				self.seat_line.transitions.append(trans_fade_in)
		else:
			self.seat_line.transitions = []
			if len(line_transitions) > 0:
				self.seat_line.transitions.append(ParallellTransitionFunctions(*line_transitions))
			if self.color_background != self.player_bg_color:
				self.seat_line.transitions.append(ParallellTransitionFunctions(
					ColorTransitionFunction(self.color_background, self.player_bg_color, easing=FADE_EASE(0, 1, FADE_DURATION)),
					PropertyTransition(self, 'dot_brightness', DOTS_BRIGHTNESS, FADE_EASE, FADE_DURATION),
				))

	def on_time_reminder(self, time_reminder_count: int):
		self.blinks_left = min(time_reminder_count, TIME_REMINDER_MAX_PULSES)
		self.blink_transition = None