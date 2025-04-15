from utils.settings import get_int, get_float, get_ease
# How many times do we spin around
START_GAME_SPIN_MIN_ROTATIONS = get_int('TABLE_START_GAME_SPIN_MIN_ROTATIONS', 5)
START_GAME_SPIN_MAX_ROTATIONS = get_int('TABLE_START_GAME_SPIN_MAX_ROTATIONS', 7)
# How fast does the spinning go, once ramped up. In Pixels/Seconds
START_GAME_SPIN_SPEED_PPS = get_int('TABLE_START_GAME_SPIN_SPEED_PPS', 30)
# How does the spinning ramp up/down
START_GAME_SPIN_EASE_IN = get_ease('TABLE_START_GAME_SPIN_EASE_IN', 'CubicEaseIn')
START_GAME_SPIN_EASE_IN_DURATION = get_float('TABLE_START_GAME_SPIN_EASE_IN_DURATION', 1.0)
START_GAME_SPIN_EASE_OUT = get_ease('TABLE_START_GAME_SPIN_EASE_OUT', 'CubicEaseOut')
START_GAME_SPIN_EASE_OUT_DURATION = get_float('TABLE_START_GAME_SPIN_EASE_OUT_DURATION', 1.0)
# Controls how colors shift between the potential player colors
START_GAME_COLOR_EASING = get_ease('TABLE_START_GAME_COLOR_EASING', 'CubicEaseOut')
START_GAME_COLOR_DURATION = get_float('TABLE_START_GAME_COLOR_DURATION', 1.0)

from seated_animation.seated_animation import SgtSeatedAnimation, Line
from view_table_outline import ViewTableOutline, BLACK
from utils.transition import ColorTransitionFunction, RampUpDownTransitionFunction
from random import choice, randint, random
from game_state import Player
import time
import adafruit_logging as logging
log = logging.getLogger()

class SgtSeatedRandomStartAnimation(SgtSeatedAnimation):
	random_player: Player
	def __init__(self, parent_view: ViewTableOutline):
		super().__init__(parent_view)
		player_count = len(self.parent.state.players)
		selected_player_index = randint(0, player_count - 1)
		self.selected_player = self.parent.state.players[selected_player_index]
		selected_seat_definition = self.seat_definitions[self.selected_player.seat-1]
		selected_player_midpoint = selected_seat_definition[0]
		rotations_to_spin = randint(START_GAME_SPIN_MIN_ROTATIONS, START_GAME_SPIN_MAX_ROTATIONS)
		start_px = selected_player_midpoint + random() * self.length
		end_px = selected_player_midpoint + rotations_to_spin * self.length
		self.line = Line(midpoint=start_px, length=selected_seat_definition[1], color=BLACK)
		self.spin_transition = RampUpDownTransitionFunction(START_GAME_SPIN_SPEED_PPS, start_px, end_px, START_GAME_SPIN_EASE_IN, START_GAME_SPIN_EASE_IN_DURATION, START_GAME_SPIN_EASE_OUT, START_GAME_SPIN_EASE_OUT_DURATION)
		self.bg_color = BLACK.create_display_color()
		self.color_transition_fg = None
		self.color_transition_bg = None
		self.end_ts = time.monotonic() + self.spin_transition.duration
		self.random_player = None
		self.start_game_command_sent = False

	def animate(self):
		done = self.spin_transition.loop()
		self.line.midpoint = self.spin_transition.value
		if self.start_game_command_sent:
			pass
		elif done:
			self.line.sparkle = True
			self.line.color = self.selected_player.color.highlight.create_display_color()
			self.bg_color = self.selected_player.color.dim.create_display_color()
			self.parent.sgt_connection.enqueue_send_start_game(self.selected_player.seat)
			self.start_game_command_sent = True
		else:
			if self.color_transition_fg == None or self.color_transition_bg == None:
				time_left = self.end_ts - time.monotonic()
				if time_left < START_GAME_COLOR_DURATION*2:
					color = self.selected_player.color
					self.color_transition_fg = ColorTransitionFunction(self.line.color, color.highlight, START_GAME_COLOR_EASING(duration=time_left))
					self.color_transition_bg = ColorTransitionFunction(self.bg_color, color.dim, START_GAME_COLOR_EASING(duration=time_left))
				else:
					options = []
					for player in self.parent.state.players:
						if player != self.random_player:
							options.append(player)
					self.random_player = choice(options)
					random_color = self.random_player.color
					self.color_transition_fg = ColorTransitionFunction(self.line.color, random_color.highlight, START_GAME_COLOR_EASING(duration=START_GAME_COLOR_DURATION))
					self.color_transition_bg = ColorTransitionFunction(self.bg_color, random_color.dim, START_GAME_COLOR_EASING(duration=START_GAME_COLOR_DURATION))

			if self.color_transition_fg.loop():
				self.color_transition_fg = None
			if self.color_transition_bg.loop():
				self.color_transition_bg = None

		self.pixels.fill(self.bg_color.current_color)
		self.line.draw(self.pixels)
		self.pixels.show()

		if (done and len(self.parent.seats_with_pressed_keys) > 1):
			log.debug('Switch back to normal state!')
			self.parent.switch_to_start(self.parent.state, None)
			self.parent.set_state(self.parent.state)

		return True