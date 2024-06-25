from view import View
from game_state import GameState
from neopixel import NeoPixel
from adafruit_led_animation.helper import PixelSubset
from easing import SineEaseIn
from sgt_animation import SgtAnimation, SgtAnimationGroup, SgtSolid
from utils import find
import adafruit_logging as logging
log = logging.getLogger()

BLACK = 0x000000
BLUE = 0x0000ff

class ViewTableOutline(View):
    def __init__(self,
                 pixels: NeoPixel,
                 seat_to_pixel_map = [(0,6),(6,12),(12,18),(18,24),(24,30)],
                 refresh_rate: float=0.001):
        super().__init__()
        self.pixels = pixels
        self.seat_count = len(seat_to_pixel_map)
        self.seat_pixels = [PixelSubset(pixels, range[0], range[1]) for range in seat_to_pixel_map]
        self.pixels.auto_write = False
        self.animation = SgtAnimation((SgtSolid(self.pixels, refresh_rate, BLACK), None, True))
        self.refresh_rate = refresh_rate
        self.switch_to_not_connected()
    def animate(self):
        return self.animation.animate()
    def show_error(self, exception):
        raise Exception('Not implemented yet')
    def set_connection_progress_text(self, text):
        pass
    def switch_to_playing(self, state: GameState, old_state: GameState):
        raise Exception('Not implemented yet')
    def switch_to_simultaneous_turn(self, state: GameState, old_state: GameState):
        raise Exception('Not implemented yet')
    def switch_to_admin_time(self, state: GameState, old_state: GameState):
        raise Exception('Not implemented yet')
    def switch_to_paused(self, state: GameState, old_state: GameState):
        raise Exception('Not implemented yet')
    def switch_to_sandtimer_running(self, state: GameState, old_state: GameState):
        raise Exception('Not implemented yet')
    def switch_to_sandtimer_not_running(self, state: GameState, old_state: GameState):
        raise Exception('Not implemented yet')
    def switch_to_start(self, state: GameState, old_state: GameState):
        self.pixels.fill(BLACK)
        self.animation = SgtAnimationGroup(*[SgtAnimation((SgtSolid(seat_pixels, self.refresh_rate, BLACK), None, True)) for seat_pixels in self.seat_pixels], parent_pixel_obj=self.pixels)
    def switch_to_end(self, state: GameState, old_state: GameState):
        raise Exception('Not implemented yet')
    def switch_to_no_game(self):
        raise Exception('Not implemented yet')
    def switch_to_not_connected(self):
        self.animation = SgtAnimation((SgtSolid(self.pixels, self.refresh_rate, BLUE), None, True))
    def switch_to_error(self):
        raise Exception('Not implemented yet')
    def on_state_update(self, state: GameState, old_state: GameState):
        if state.state == GameState.STATE_START:
            for seat in range(self.seat_count):
                old_color = find((p.color for p in old_state.players if p.seat == seat+1), BLACK)
                new_color = find((p.color for p in state.players if p.seat == seat+1), BLACK)
                if old_color != new_color and isinstance(self.animation, SgtAnimationGroup):
                    animation = self.animation.animations[seat]
                    animation.set_color(new_color, transition=SineEaseIn(duration=1))
            while not self.animation.animate():
                pass