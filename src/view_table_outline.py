from utils.settings import get_int
from sgt_connection import SgtConnection

# Speed of comet animations, in Pixels/Second.
COMET_SPEED_PPS = get_int('TABLE_COMET_SPEED_PPS', 10)

from view import View
from game_state import GameState
from adafruit_pixelbuf import PixelBuf
from adafruit_led_animation.animation.rainbowcomet import RainbowComet
from adafruit_led_animation.animation.comet import Comet
from sgt_animation import SgtAnimation, SgtSolid
from utils.color import BLUE as BLUE_PC, RED as RED_PC, BLACK as BLACK_PC
import adafruit_logging as logging
from gc import collect, mem_free
log = logging.getLogger()

BLACK = BLACK_PC.black
BLUE = BLUE_PC.highlight
RED = RED_PC.highlight

class ViewTableOutline(View):
	seats_with_pressed_keys: set[int]
	sgt_connection: SgtConnection
	def __init__(self,
			pixels: PixelBuf,
			seat_definitions: list[tuple[float, int]],
		):
		super().__init__()
		self.pixels = pixels
		self.seat_definitions = seat_definitions
		self.seat_count = len(seat_definitions)
		self.seats_with_pressed_keys = set()
		self.pixels.auto_write = False
		self.comet_refresh_rate = 1/COMET_SPEED_PPS
		self.animation = SgtAnimation(BLACK, (SgtSolid(self.pixels, 0x0), None, True))
		self.switch_to_not_connected()
	def set_connection(self, connection: SgtConnection):
		self.sgt_connection = connection
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
		log.debug(f'--> Free memory: {mem_free():,} @ switch_to_paused b4')
		collect()
		log.debug(f'--> Free memory: {mem_free():,} @ switch_to_paused after')
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
		from seated_animation.seated_error import SgtErrorAnimation
		if not isinstance(self.animation, SgtErrorAnimation):
			self.animation = SgtErrorAnimation(self)
	def switch_to_random_start_animation(self):
		log.debug(f'--> Free memory: {mem_free():,} @ switch_to_random_start_animation b4')
		collect()
		log.debug(f'--> Free memory: {mem_free():,} @ switch_to_random_start_animation after')
		self.animation = SgtSeatedRandomStartAnimation(self)
	def on_state_update(self, state: GameState|None, old_state: GameState|None):
		from seated_animation.seated_animation import SgtSeatedAnimation
		if isinstance(self.animation, SgtSeatedAnimation):
			self.animation.on_state_update(state, old_state)
	def _activate_multiplayer_animation(self):
		log.debug(f'--> Free memory: {mem_free():,} @ _activate_multiplayer_animation b4')
		collect()
		log.debug(f'--> Free memory: {mem_free():,} @ _activate_multiplayer_animation after')
		if not isinstance(self.animation, SgtSeatedMultiplayerAnimation):
			self.animation = SgtSeatedMultiplayerAnimation(self)
	def _activate_singleplayer_animation(self):
		log.debug(f'--> Free memory: {mem_free():,} @ _activate_singleplayer_animation')
		if not isinstance(self.animation, SgtSeatedSingleplayerAnimation):
			random_first_player = None if not isinstance(self.animation, SgtSeatedRandomStartAnimation) else self.animation.selected_player
			self.animation = SgtSeatedSingleplayerAnimation(self, random_first_player)
	def on_time_reminder(self, time_reminder_count: int):
		from seated_animation.seated_animation import SgtSeatedAnimation
		if isinstance(self.animation, SgtSeatedAnimation):
			self.animation.on_time_reminder(time_reminder_count)
	def on_pressed_seats_change(self, seats: set[int]):
		self.seats_with_pressed_keys = seats

from seated_animation.seated_multiplayer import SgtSeatedMultiplayerAnimation
from seated_animation.seated_singleplayer import SgtSeatedSingleplayerAnimation
from seated_animation.seated_random_start_animation import SgtSeatedRandomStartAnimation
from seated_animation.seated_pause import SgtPauseAnimation