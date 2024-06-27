from adafruit_pixelbuf import PixelBuf
from view import View
from game_state import GameState, Player
from neopixel import NeoPixel
from adafruit_led_animation.helper import PixelSubset
from easing import SineEaseIn
from sgt_animation import SgtAnimation, SgtAnimationGroup, SgtSolid
from utils import find_int, set_brightness
import adafruit_logging as logging
log = logging.getLogger()

BLACK = (0,0,0)
BLUE = (0,0,255)

class ViewTableOutline(View):
    def __init__(self,
            pixels: NeoPixel,
            seat_pixel_ranges: list[tuple[int, int]],
            brightness_normal: float,
            brightness_highlight: float,
            refresh_rate: float=0.001,
        ):
        super().__init__()
        self.pixels = pixels
        self.seat_count = len(seat_pixel_ranges)
        self.seat_pixels = [PixelSubset(pixels, range[0], range[1]) for range in seat_pixel_ranges]
        self.pixels.auto_write = False
        self.animation = SgtAnimation((SgtSolid(self.pixels, refresh_rate, BLACK), None, True))
        self.refresh_rate = refresh_rate
        self.brightness_normal = brightness_normal
        self.brightness_highlight = brightness_highlight
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
        if not isinstance(self.animation, SgtSeatedMultiplayerAnimation):
            self.animation = SgtSeatedMultiplayerAnimation(self.seat_pixels, self.refresh_rate, self.pixels, self.brightness_normal, self.brightness_highlight)
    def switch_to_end(self, state: GameState, old_state: GameState):
        raise Exception('Not implemented yet')
    def switch_to_no_game(self):
        raise Exception('Not implemented yet')
    def switch_to_not_connected(self):
        self.animation = SgtAnimation((SgtSolid(self.pixels, self.refresh_rate, set_brightness(BLUE, self.brightness_highlight)), None, True))
    def switch_to_error(self):
        raise Exception('Not implemented yet')
    def on_state_update(self, state: GameState, old_state: GameState):
        if isinstance(self.animation, SgtSeatedMultiplayerAnimation):
            self.animation.on_state_update(state, old_state)

class SgtSeatedMultiplayerAnimation(SgtAnimationGroup):
    def __init__(self, seat_pixels: list[PixelSubset], refresh_rate: float, parent_pixel_obj: PixelBuf, brightness_normal: float, brightness_highlight: float) -> None:
        super().__init__([SgtAnimation((SgtSolid(pixels, refresh_rate, BLACK), None, True)) for pixels in seat_pixels], parent_pixel_obj=parent_pixel_obj)
        self.brightness_normal = brightness_normal
        self.brightness_highlight = brightness_highlight

    def on_state_update(self, state: GameState, old_state: GameState):
        for seat in range(len(self.animations)):
            old_color = find_int((p.color for p in old_state.players if p.seat == seat+1), BLACK)
            new_color = find_int((p.color for p in state.players if p.seat == seat+1), BLACK)
            if old_color != new_color:
                animation = self.animations[seat]
                animation.set_color(set_brightness(new_color, self.brightness_normal), transition=SineEaseIn(duration=1))
        while not self.animate():
            pass
