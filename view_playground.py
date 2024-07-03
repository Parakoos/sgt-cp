from game_state import TIMER_MODE_NO_TIMER, STATE_NOT_RUNNING, STATE_RUNNING
from view import View
from adafruit_circuitplayground import cp
from neopixel import NeoPixel
from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.animation.solid import Solid
from adafruit_led_animation.animation.comet import Comet
from adafruit_led_animation.color import RED, BLUE, BLACK
from time import monotonic, sleep
from math import floor
from adafruit_circuitplayground import cp

SEC_PER_LIGHT = 60                  # How many seconds does each lit light represent?

SAND_COLOR_OUT_OF_TIME = (255, 0, 0)
SAND_COLOR_TIME_LEFT = (0, 255, 0)
SAND_COLOR_TIME_USED = (0, 0, 160)

class ViewPlayground(View):
    def __init__(self, pixels: NeoPixel):
        super().__init__()
        self.pixels = pixels
        self.pixels.auto_write = False
        self.animation = Solid(self.pixels, BLACK)

    def animate(self):
        return self.animation.animate()

    def set_connection_progress_text(self, text):
        self.switch_to_trying_to_connect()

    def switch_to_playing(self):
        if self.state.timer_mode == TIMER_MODE_NO_TIMER:
            self.animation = Pulse(self.pixels, speed=0.01, color=self.state.color, period=0.5)
        else:
            self.animation = PlayingAnimation(self)
    def switch_to_simultaneous_turn(self):
        self.animation = Comet(self.pixels, speed=0.1, color=self.state.color, tail_length=7, ring=True, reverse=True)
    def switch_to_admin_time(self):
        self.animation = Comet(self.pixels, speed=0.1, color=self.state.color, tail_length=7, ring=True, reverse=True)
    def switch_to_paused(self):
        self.animation = LedBlinkAnimation(self, 2, 1)
    def switch_to_sandtimer_running(self):
        self.animation = SandtimerAnimation(self)
    def switch_to_sandtimer_not_running(self):
        self.animation = SandtimerAnimation(self)
    def switch_to_start(self):
        self.switch_to_admin_time()
    def switch_to_end(self):
        self.animation = LedBlinkAnimation(self, 1, 0.5)
    def switch_to_trying_to_connect(self):
        self.animation = Comet(self.pixels, speed=0.1, color=BLUE, tail_length=7, ring=True, reverse=True)
    def switch_to_connecting(self):
        self.animation = Pulse(self.pixels, speed=0.01, color=BLUE, period=0.5)
    def switch_to_error(self):
        self.animation = Pulse(self.pixels, speed=0.01, color=RED, period=0.5)


class LedBlinkAnimation():
    def __init__(self, view: ViewPlayground, cycle_time=4, active_time=1) -> None:
        self.view = view
        self.cycle_time = cycle_time
        self.active_time = active_time
    def animate(self):
        self.view.pixels.fill(BLACK)
        self.view.pixels.show()

class PlayingAnimation():
    def __init__(self, view: ViewPlayground) -> None:
        self.view = view
    def animate(self):
        PIXEL_COUNT = len(self.view.pixels)
        sec = (self.view.state.turn_time_sec + monotonic() - self.view.state.timestamp)
        sec_abs = abs(sec)
        color = self.view.state.color if sec >= 0 else self.pulsate_color(self.view.state.color)
        q, mod = divmod(sec_abs, SEC_PER_LIGHT)
        fully_lit = min(PIXEL_COUNT-1, floor(q))
        if fully_lit > 0:
            self.view.pixels[0:fully_lit] = [color] * fully_lit
        if fully_lit < PIXEL_COUNT:
            self.view.pixels[fully_lit:PIXEL_COUNT] = [(0, 0, 0)] * (PIXEL_COUNT-fully_lit)

        pixels_to_travel = PIXEL_COUNT -1 - fully_lit
        if pixels_to_travel > 0:
            time_per_pixel = SEC_PER_LIGHT / pixels_to_travel
            current_pixel = int(PIXEL_COUNT -1 - (mod // time_per_pixel))
            self.view.pixels[current_pixel] = color

        if sec < 0:
            reversed = [None] * PIXEL_COUNT
            for i in range(0, PIXEL_COUNT):
                reversed[i] = self.pixels[PIXEL_COUNT -1-i]
            self.view.pixels[0:PIXEL_COUNT] = reversed
        self.view.pixels.show()

class SandtimerAnimation():
    def __init__(self, view: ViewPlayground) -> None:
        self.view = view
        self.out_of_time_animation = Comet(self.view.pixels, speed=0.1, color=SAND_COLOR_OUT_OF_TIME, tail_length=9, ring=True, reverse=True)
        self.out_of_time_shown = False

    def animate(self):
        PIXEL_COUNT = len(self.view.pixels)
        time_added_by_monotonic = 0 if self.view.state.state == STATE_NOT_RUNNING else monotonic() - self.state.update_ts
        turn_time = self.view.state.turn_time_sec + time_added_by_monotonic
        remaining_time = max(self.view.state.player_time_sec - turn_time, 0)

        if (remaining_time == 0):
            if not self.out_of_time_shown or self.view.state.state == STATE_RUNNING:
                self.out_of_time_animation.animate()
            if not self.out_of_time_shown:
                cp.play_tone(262, 0.5)
            self.out_of_time_shown = True
        else :
            self.out_of_time_shown = False
            pixels_left = int((remaining_time / self.view.state.player_time_sec) * PIXEL_COUNT)
            n = min(PIXEL_COUNT, pixels_left)

            if n > 0:
                self.pixels[0:n] = [SAND_COLOR_TIME_LEFT] * n

            if n < PIXEL_COUNT:
                time_per_pixel = self.view.state.player_time_sec / PIXEL_COUNT
                time_into_current_pixel = remaining_time % time_per_pixel
                fraction_into_current_pixel = time_into_current_pixel / time_per_pixel
                color_current_pixel = (
                    SAND_COLOR_TIME_LEFT[0]*fraction_into_current_pixel + SAND_COLOR_TIME_USED[0]*(1-fraction_into_current_pixel),
                    SAND_COLOR_TIME_LEFT[1]*fraction_into_current_pixel + SAND_COLOR_TIME_USED[1]*(1-fraction_into_current_pixel),
                    SAND_COLOR_TIME_LEFT[2]*fraction_into_current_pixel + SAND_COLOR_TIME_USED[2]*(1-fraction_into_current_pixel)
                    )
                self.view.pixels[n] = color_current_pixel

            self.view.pixels[n+1:10] = [SAND_COLOR_TIME_USED] * (9-n)
            if self.view.state.state == STATE_NOT_RUNNING:
                for i in range(0, PIXEL_COUNT):
                    self.view.pixels[i] = self.pulsate_color(self.view.pixels[i])
            self.view.pixels.show()
