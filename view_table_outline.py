from view import View
from game_state import GameState, Player
from neopixel import NeoPixel
from easing import EasingBase
from adafruit_led_animation.animation.rainbowcomet import RainbowComet
from adafruit_led_animation.animation.comet import Comet
from sgt_animation import SgtAnimation, SgtSolid
from utils import find_thing, set_brightness, TransitionFunction, ParallellTransitionFunctions, ColorTransitionFunction
from math import ceil
import adafruit_logging as logging
log = logging.getLogger()

BLACK = (0,0,0)
BLUE = (0,0,255)
RED = (255,0,0)

class ViewTableOutline(View):
    def __init__(self,
            pixels: NeoPixel,
            seat_definitions: list[tuple[float, int]],
            brightness_normal: float,
            brightness_highlight: float,
            ease_fade: EasingBase,
            ease_fade_duration: float,
            ease_line: EasingBase,
            ease_line_pixels_per_seconds: int,
            refresh_rate: float=0.01,
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
        self.ease_fade = ease_fade
        self.ease_fade_duration = ease_fade_duration
        self.ease_line = ease_line
        self.ease_line_pixels_per_seconds = ease_line_pixels_per_seconds
        self.switch_to_not_connected()
    def animate(self):
        return self.animation.animate()
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
        self.animation = SgtAnimation(
            (RainbowComet(self.pixels, self.refresh_rate, tail_length=round(len(self.pixels)/0.5), bounce=True), 1, False),
            (SgtSolid(self.pixels, self.refresh_rate, set_brightness(BLACK, self.brightness_highlight)), 0.5, True),
        )
    def switch_to_sandtimer_running(self, state: GameState, old_state: GameState):
        raise Exception('Not implemented yet')
    def switch_to_sandtimer_not_running(self, state: GameState, old_state: GameState):
        raise Exception('Not implemented yet')
    def switch_to_start(self, state: GameState, old_state: GameState):
        self._activate_multiplayer_animation()
    def switch_to_end(self, state: GameState, old_state: GameState):
        self._activate_multiplayer_animation()
    def switch_to_no_game(self):
        self.animation = SgtAnimation(
            (RainbowComet(self.pixels, self.refresh_rate, tail_length=round(len(self.pixels)/0.5), bounce=True), 1, False),
            (SgtSolid(self.pixels, self.refresh_rate, set_brightness(BLACK, self.brightness_highlight)), 0.5, True),
        )
    def switch_to_not_connected(self):
        self.animation = SgtAnimation((SgtSolid(self.pixels, self.refresh_rate, set_brightness(BLUE, self.brightness_highlight)), None, True))
    def switch_to_error(self):
        self.animation = SgtAnimation(
            (Comet(self.pixels, self.refresh_rate, RED, tail_length=round(len(self.pixels)/0.5), bounce=True), 1, False),
            (SgtSolid(self.pixels, self.refresh_rate, set_brightness(BLACK, self.brightness_highlight)), 0.5, True),
        )
    def on_state_update(self, state: GameState, old_state: GameState):
        if isinstance(self.animation, SgtSeatedAnimation):
            self.animation.on_state_update(state, old_state)
    def _activate_multiplayer_animation(self):
        if not isinstance(self.animation, SgtSeatedMultiplayerAnimation):
            self.animation = SgtSeatedMultiplayerAnimation(self.seat_definitions, self.pixels, self.brightness_normal, self.brightness_highlight, self.ease_fade, self.ease_fade_duration)
    def _activate_singleplayer_animation(self):
        if not isinstance(self.animation, SgtSeatedSingleplayerAnimation):
            self.animation = SgtSeatedSingleplayerAnimation(self.seat_definitions, self.pixels, self.brightness_normal, self.brightness_highlight, self.ease_fade, self.ease_fade_duration, self.ease_line, self.ease_line_pixels_per_seconds)

class Line():
    def __init__(self, midpoint: float, length: float, color: tuple[int, int, int]) -> None:
        self.midpoint = midpoint
        self.length = length
        self.color = color
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
    def __init__(self,
                 seat_definitions: list[tuple[int, int]],
                 pixels: NeoPixel,
                 brightness_normal: float,
                 brightness_highlight: float,
                 ease_fade: EasingBase,
                 ease_fade_duration: float,
                 ):
        self.pixels=pixels
        self.seat_definitions = seat_definitions
        self.brightness_normal = brightness_normal
        self.brightness_highlight = brightness_highlight
        self.length = len(self.pixels)
        self.ease_fade = ease_fade
        self.ease_fade_duration = ease_fade_duration

    def on_state_update(self, state: GameState, old_state: GameState):
        pass

    def draw_line(self, line:Line):
        lower_bound = ceil(line.midpoint - (line.length/2))
        upper_bound = ceil(line.midpoint + (line.length/2))
        for n in range (lower_bound, upper_bound):
            self.pixels[n%self.length] = line.color

class SgtSeatedMultiplayerAnimation(SgtSeatedAnimation):
    def __init__(self,
                 seat_definitions: list[tuple[float, int]],
                 pixels: NeoPixel,
                 brightness_normal: float,
                 brightness_highlight: float,
                 ease_fade: EasingBase,
                 ease_fade_duration: float,
                 ):
        super().__init__(seat_definitions, pixels, brightness_normal, brightness_highlight, ease_fade, ease_fade_duration)
        self.seat_lines = list(LineTransition(Line(midpoint=s[0], length=0, color=BLACK), transitions=[]) for s in seat_definitions)

        # Fade to black
        def _set_brightness(brightness: float):
            pixels.brightness = brightness
            pixels.show()
        saved_brightness = pixels.brightness
        tranny = TransitionFunction(self.ease_fade(saved_brightness, 0, self.ease_fade_duration), _set_brightness)
        while not tranny.loop():
            pass
        self.animate()
        pixels.brightness = saved_brightness

    def animate(self):
        self.pixels.fill(BLACK)
        has_more_transitions = False
        for seat_line in self.seat_lines:
            if len(seat_line.transitions) > 0:
                if(seat_line.transitions[0].loop()):
                    seat_line.transitions = seat_line.transitions[1:]
            has_more_transitions = has_more_transitions or len(seat_line.transitions) > 0
            self.draw_line(seat_line.line)
        self.pixels.show()
        return has_more_transitions

    def set_line_length(self, line_length: float, seat: int):
        self.seat_lines[seat].line.length = line_length
    def set_line_color(self, color: tuple[int,int,int], seat: int):
        self.seat_lines[seat].line.color = color

    def on_state_update(self, state: GameState, old_state: GameState):
        for seat, line in enumerate(self.seat_definitions):
            old_color = self.seat_lines[seat].line.color
            old_line_length = self.seat_lines[seat].line.length
            new_color = None
            new_line_length = line[1]
            player = find_thing((p for p in state.players if p.seat == seat+1), None)
            if not isinstance(player, Player):
                new_color = None
            elif state.state == 'si':
                if (seat+1) in state.seat:
                    # Player is involved.
                    new_color = player.color
                    if player.action != 'in':
                        # Player has passed
                        new_line_length = ceil(new_line_length / 4)
            elif state.state == 'ad':
                if (seat+1) in state.seat:
                    # Player is involved. Since it is an admin turn, all involved players gets a short line.
                    new_color = player.color
                    new_line_length = ceil(new_line_length / 4)
            else:
                new_color = player.color

            if old_color == BLACK and new_color != None:
                self.seat_lines[seat].line.length = 0
                self.seat_lines[seat].line.color = new_color
                self.seat_lines[seat].transitions = [TransitionFunction(self.ease_fade(0, new_line_length, self.ease_fade_duration), self.set_line_length, seat)]
            elif old_color != BLACK and new_color == None:
                self.seat_lines[seat].transitions = [TransitionFunction(self.ease_fade(old_line_length, 0, self.ease_fade_duration), self.set_line_length, seat)]
            elif old_color != BLACK and (old_color != new_color or old_line_length != new_line_length):
                trannies = []
                if old_color != new_color:
                    trannies.append(ColorTransitionFunction(from_color=old_color, to_color=new_color, easing=self.ease_fade(0, 1, self.ease_fade_duration), callback=self.set_line_color, callback_data=seat))
                if old_line_length != new_line_length:
                    trannies.append(TransitionFunction(self.ease_fade(old_line_length, new_line_length, self.ease_fade_duration), self.set_line_length, seat))
                self.seat_lines[seat].transitions = [ParallellTransitionFunctions(*trannies)]
        while self.animate():
            pass

class SgtSeatedSingleplayerAnimation(SgtSeatedAnimation):
    seat_line: LineTransition
    color_background: tuple[int,int,int]

    def __init__(self,
                 seat_definitions: list[tuple[int, int]],
                 pixels: NeoPixel,
                 brightness_normal: float,
                 brightness_highlight: float,
                 ease_fade: EasingBase,
                 ease_fade_duration: float,
                 ease_line: EasingBase,
                 ease_line_pixels_per_seconds: int
                ):
        super().__init__(seat_definitions, pixels, brightness_normal, brightness_highlight, ease_fade, ease_fade_duration)
        self.color_background = BLACK
        self.seat_line = None
        self.ease_line = ease_line
        self.ease_line_pixels_per_seconds = ease_line_pixels_per_seconds

        # Fade to black
        def _set_brightness(brightness: float):
            pixels.brightness = brightness
            pixels.show()
        saved_brightness = pixels.brightness
        tranny = TransitionFunction(self.ease_fade(saved_brightness, 0, self.ease_fade_duration), _set_brightness)
        while not tranny.loop():
            pass
        self.animate()
        pixels.brightness = saved_brightness

    def animate(self):
        if self.seat_line == None:
            self.pixels.fill(BLACK)
            self.pixels.show()
            return False
        self.pixels.fill(self.color_background)
        if len(self.seat_line.transitions) > 0:
            if(self.seat_line.transitions[0].loop()):
                self.seat_line.transitions = self.seat_line.transitions[1:]
        self.draw_line(self.seat_line.line)
        self.pixels.show()
        return len(self.seat_line.transitions) > 0

    def set_color_normal(self, color: tuple[int,int,int]):
        self.color_background = color
    def set_line_color(self, color: tuple[int,int,int]):
        self.seat_line.line.color = color
    def set_line_midpoint(self, midpoint: float):
        self.seat_line.line.midpoint = midpoint % self.length
    def set_line_length(self, length: float):
        self.seat_line.line.length = length

    def on_state_update(self, state: GameState, old_state: GameState):
        active_player = state.get_active_player()

        if active_player == None:
            raise Exception('No active player!')

        player_line_midpoint, player_line_length = self.seat_definitions[active_player.seat-1]

        if self.seat_line == None:
            self.seat_line = LineTransition(Line(player_line_midpoint, 0, BLACK), [])

        line_transitions = []

        bg_color = set_brightness(active_player.color, self.brightness_normal) if state.state == 'pl' else BLACK
        fg_color = set_brightness(active_player.color, self.brightness_highlight)

        from_pixel = self.seat_line.line.midpoint
        to_pixel = player_line_midpoint
        line_ease_duration = self.ease_fade_duration
        line_ease = self.ease_fade
        if from_pixel != to_pixel:
            steps_if_adding = (to_pixel-from_pixel) % self.length
            steps_if_subtracting = (from_pixel-to_pixel) % self.length
            line_ease_duration = min(steps_if_adding, steps_if_subtracting)/self.ease_line_pixels_per_seconds
            line_ease = self.ease_line
            if (steps_if_adding <= steps_if_subtracting):
                line_transitions.append(TransitionFunction(line_ease(start=from_pixel, end=from_pixel+steps_if_adding, duration=line_ease_duration), callback=self.set_line_midpoint))
            else:
                line_transitions.append(TransitionFunction(line_ease(start=from_pixel, end=from_pixel-steps_if_subtracting, duration=line_ease_duration), callback=self.set_line_midpoint))
        if self.seat_line.line.color != fg_color:
            line_transitions.append(ColorTransitionFunction(from_color=self.seat_line.line.color, to_color=fg_color, easing=line_ease(duration=line_ease_duration), callback=self.set_line_color))
        if self.seat_line.line.length != player_line_length:
            line_transitions.append(TransitionFunction(line_ease(start=self.seat_line.line.length, end=player_line_length, duration=line_ease_duration), callback=self.set_line_length))

        if from_pixel != to_pixel:
            # We want to first fade out the current background color to black,
            # Then move the player line to the new position, changing its color while doing so,
            # and finally fade in the background to the new color.
            trans_fade_out = ColorTransitionFunction(from_color=self.color_background, to_color=BLACK, easing=self.ease_fade(0, 1, self.ease_fade_duration), callback=self.set_color_normal)
            trans_fade_in = ColorTransitionFunction(from_color=BLACK, to_color=bg_color, easing=self.ease_fade(0, 1, self.ease_fade_duration), callback=self.set_color_normal)
            self.seat_line.transitions = [
                trans_fade_out,
                ParallellTransitionFunctions(*line_transitions),
                trans_fade_in,
            ]
        else:
            self.seat_line.transitions = []
            if len(line_transitions) > 0:
                self.seat_line.transitions.append(ParallellTransitionFunctions(*line_transitions))
            if self.color_background != bg_color:
                self.seat_line.transitions.append(ColorTransitionFunction(from_color=self.color_background, to_color=bg_color, easing=self.ease_fade(0, 1, self.ease_fade_duration), callback=self.set_color_normal))

        while self.animate():
            pass