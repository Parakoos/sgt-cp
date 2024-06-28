from adafruit_pixelbuf import PixelBuf
from view import View
from game_state import GameState, Player
from neopixel import NeoPixel
from easing import SineEaseIn, LinearInOut
from sgt_animation import SgtAnimation, SgtSolid
from utils import find_color, set_brightness, TransitionFunction, mix
from math import ceil
import adafruit_logging as logging
log = logging.getLogger()

BLACK = (0,0,0)
BLUE = (0,0,255)

class ViewTableOutline(View):
    def __init__(self,
            pixels: NeoPixel,
            seat_definitions: list[tuple[float, int]],
            brightness_normal: float,
            brightness_highlight: float,
            refresh_rate: float=0.001,
        ):
        super().__init__()
        self.pixels = pixels
        self.seat_definitions = seat_definitions
        self.seat_count = len(seat_definitions)
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
            self.animation = SgtSeatedMultiplayerAnimation(self.seat_definitions, self.pixels, self.brightness_normal, self.brightness_highlight)
    def switch_to_end(self, state: GameState, old_state: GameState):
        raise Exception('Not implemented yet')
    def switch_to_no_game(self):
        raise Exception('Not implemented yet')
    def switch_to_not_connected(self):
        self.animation = SgtAnimation((SgtSolid(self.pixels, self.refresh_rate, set_brightness(BLUE, self.brightness_highlight)), None, True))
    def switch_to_error(self):
        raise Exception('Not implemented yet')
    def on_state_update(self, state: GameState, old_state: GameState):
        if isinstance(self.animation, SgtSeatedAnimation):
            self.animation.on_state_update(state, old_state)

class Line():
    def __init__(self, midpoint: float, size: float, color: tuple[int, int, int]) -> None:
        self.midpoint = midpoint
        self.size = size
        self.color = color
    def __repr__(self):
        facts = []
        if (self.midpoint):
            facts.append(f'midpoint={self.midpoint}')
        if (self.midpoint):
            facts.append(f'size={self.size}')
        if (self.midpoint):
            facts.append(f'color={self.color}')
        return f"<Line: {', '.join(facts)}>"

class LineTransition():
    def __init__(self, line: Line, transition: TransitionFunction|None) -> None:
        self.line = line
        self.transition = transition
    def __repr__(self):
        facts = []
        if (self.line):
            facts.append(f'line={self.line}')
        if (self.transition):
            facts.append(f'transition={self.transition}')
        return f"<LineTransition: {', '.join(facts)}>"

class SgtSeatedAnimation():
    def __init__(self, seat_definitions: list[tuple[int, int]], pixels: NeoPixel, brightness_normal: float, brightness_highlight: float):
        self.pixels=pixels
        self.seat_definitions = seat_definitions
        self.brightness_normal = brightness_normal
        self.brightness_highlight = brightness_highlight
        self.length = len(self.pixels)

    def on_state_update(self, state: GameState, old_state: GameState):
        pass

    def draw_line(self, line:Line):
        lower_bound = ceil(line.midpoint - (line.size/2))
        upper_bound = ceil(line.midpoint + (line.size/2))
        for n in range (lower_bound, upper_bound):
            self.pixels[n] = line.color

class SgtSeatedMultiplayerAnimation(SgtSeatedAnimation):
    def __init__(self, seat_definitions: list[tuple[float, int]], pixels: NeoPixel, brightness_normal: float, brightness_highlight: float):
        super().__init__(seat_definitions, pixels, brightness_normal, brightness_highlight)
        self.seat_lines = list(LineTransition(Line(midpoint=s[0], size=0, color=BLACK), transition=None) for s in seat_definitions)

    def animate(self):
        self.pixels.fill(BLACK)
        has_transition = False
        for seat_line in self.seat_lines:
            if seat_line.transition:
                if(seat_line.transition.loop()):
                    seat_line.transition = None
                else:
                    has_transition = True
            self.draw_line(seat_line.line)
        self.pixels.show()
        return not has_transition

    def on_state_update(self, state: GameState, old_state: GameState):
        for seat, line in enumerate(self.seat_definitions):
            old_color = find_color((p.color for p in old_state.players if p.seat == seat+1), None)
            new_color = find_color((p.color for p in state.players if p.seat == seat+1), None)
            if old_color == None and new_color != None:
                def cb(line_length: float, seat: int):
                    self.seat_lines[seat].line.size = line_length
                self.seat_lines[seat].line.size = 0
                self.seat_lines[seat].line.color = new_color
                self.seat_lines[seat].transition = TransitionFunction(LinearInOut(0, line[1], 0.5), cb, seat)
            elif old_color != None and new_color == None:
                def cb(line_length: float, seat: int):
                    self.seat_lines[seat].line.size = line_length
                self.seat_lines[seat].transition = TransitionFunction(LinearInOut(self.seat_lines[seat].line.size, 0, 0.5), cb, seat)
            elif old_color != None and old_color != new_color:
                def cb(progress: float, cb_data: tuple[int, tuple[int,int,int], tuple[int,int,int]]):
                    self.seat_lines[cb_data[0]].line.color = mix(cb_data[1], cb_data[2], progress)
                self.seat_lines[seat].line.size = line[1]
                self.seat_lines[seat].transition = TransitionFunction(LinearInOut(0, 1, 0.5), cb, (seat, old_color, new_color))
        while not self.animate():
            pass
