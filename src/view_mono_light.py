from utils.settings import get_float

# 0-1. How bright do you want the LED?
MONO_COLOR_TRANSITION_DURATION = get_float('MONO_COLOR_TRANSITION_DURATION', 0.5)

from game_state import GameState, STATE_RUNNING
from sgt_animation import SgtAnimation, SgtSolid
from utils.transition import BoomerangEase
from view import View
from neopixel import NeoPixel
from adafruit_led_animation.animation import Animation
from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.animation.blink import Blink
from adafruit_led_animation.animation.rainbow import Rainbow
from utils.color import PlayerColor, RED, BLUE, BLACK, GREEN, ColorMix, LED_BRIGHTNESS_HIGHLIGHT, LED_BRIGHTNESS_NORMAL
from easing import LinearInOut, SineEaseIn
import adafruit_logging as logging
log = logging.getLogger()

class ViewMonoLight(View):
	def __init__(self, pixels: NeoPixel):
		super().__init__()
		self.pixels = pixels
		self.animation = SgtSolid(self.pixels, BLACK)

	def animate(self) -> bool:
		shared_stuff_busy = super().animate()
		this_animation_busy = self.animation.animate()
		return this_animation_busy or shared_stuff_busy

	def on_state_update(self, state: GameState|None, old_state: GameState|None):
		if state is None:
			return
		if isinstance(self.animation, Animation):
			self.animation.color = state.color_p.highlight.create_display_color().current_color
		elif isinstance(self.animation, SgtAnimation):
			self.animation.transition_color(state.color_p.highlight, LinearInOut(0, 1, MONO_COLOR_TRANSITION_DURATION))

	def set_connection_progress_text(self, text):
		self.set_button_led_to_solid(BLUE)
	def switch_to_playing(self, state: GameState, old_state: GameState):
		self.set_button_led_to_pulse(state.color_p, 1)
	def switch_to_simultaneous_turn(self, state: GameState, old_state: GameState):
		self.set_button_led_to_periodic_pulse(state.color_p, 1, 2)
	def switch_to_admin_time(self, state: GameState, old_state: GameState):
		self.set_button_led_to_periodic_pulse(state.color_p, 2, 2)
	def switch_to_paused(self, state: GameState, old_state: GameState):
		self.set_button_led_to_periodic_pulse(state.color_p, 1, 6)
	def switch_to_sandtimer_running(self, state: GameState, old_state: GameState):
		if not isinstance(self.animation, SandtimerAnimation):
			self.animation = SandtimerAnimation(self)
	def switch_to_sandtimer_not_running(self, state: GameState, old_state: GameState):
		if not isinstance(self.animation, SandtimerAnimation):
			self.animation = SandtimerAnimation(self)
	def switch_to_start(self, state: GameState, old_state: GameState):
		self.set_button_led_to_periodic_pulse(state.color_p, 1, 2)
	def switch_to_end(self, state: GameState, old_state: GameState):
		self.animation = Rainbow(self.pixels, speed=0.1)
	def switch_to_no_game(self):
		super().switch_to_no_game()
		self.animation = Rainbow(self.pixels, speed=0.1)
	def switch_to_not_connected(self):
		super().switch_to_not_connected()
		self.set_button_led_to_periodic_pulse(BLUE, 2, 2)
	def switch_to_error(self):
		super().switch_to_error()
		self.set_button_led_to_blink(RED, 0.2)

	# Helper methods
	def set_button_led_to_solid(self, color: PlayerColor):
		self.animation = SgtAnimation(color.highlight, (SgtSolid(self.pixels, color=0), None, False))
	def set_button_led_to_blink(self, color: PlayerColor, speed: float):
		self.animation = SgtAnimation(color.highlight, (Blink(self.pixels, speed=speed, color=0), None, False))
	def set_button_led_to_pulse(self, color: PlayerColor, pulse_time: float):
		self.animation = SgtAnimation(color.highlight, (Pulse(self.pixels, speed=0.01, color=0), None, False))
	def set_button_led_to_periodic_pulse(self, color: PlayerColor, pulse_time, pause_time):
		pause = SgtSolid(self.pixels, BLACK)
		pulse = Pulse(self.pixels, speed=0.001, color=0, period=pulse_time)
		self.animation = SgtAnimation(color.highlight, (pulse, 1, False), (pause, pause_time, True))

class SandtimerAnimation():
	def __init__(self, parent_view: ViewMonoLight):
		super().__init__()
		self.parent_view = parent_view
		self.mix = ColorMix(GREEN.highlight, BLUE.highlight)
		self.mixed_color = GREEN.highlight.create_display_color()
		self.runnning_ease = BoomerangEase(ease=SineEaseIn,start_position=LED_BRIGHTNESS_HIGHLIGHT,mid_position=0.1,duration=3,loop=True)

	def animate(self):
		state = self.parent_view.state
		current_times = state.get_current_timings()
		if current_times == None:
			self.parent_view.pixels.fill(0x0)
			self.parent_view.pixels.show()
			return
		remaining_time = max(current_times.player_time - current_times.turn_time, 0)
		new_fancy = None
		if (remaining_time == 0):
			new_fancy = RED.highlight.fancy_color
		else:
			new_fancy, _ = self.mix.mix(current_times.turn_time / current_times.player_time)
		new_brightness = LED_BRIGHTNESS_HIGHLIGHT if state.state != STATE_RUNNING else self.runnning_ease.func(current_times.turn_time)
		self.mixed_color.update(new_fancy, new_brightness)
		self.parent_view.pixels.fill(self.mixed_color.current_color)
		self.parent_view.pixels.show()