from time import monotonic
from easing import EasingBase
import adafruit_fancyled.adafruit_fancyled as fancy
import adafruit_logging as logging
log = logging.getLogger()

def find_int(i: iter[int], default: int) -> int:
	try:
		return next(i)
	except StopIteration:
		return default

def find_color(i: iter[tuple[int, int, int]], default: tuple[int, int, int]) -> tuple[int, int, int]:
	try:
		return next(i)
	except StopIteration:
		return default

def do_for_time(time, callback):
	timeout = monotonic() + time
	while monotonic() < timeout:
		callback()

def mix(color1: tuple[int,int,int], color2: tuple[int,int,int], weight: float = 0.5) -> tuple[int,int,int]:
    """Blend between two colors using given ratio.
    :returns: (r,g,b) int tuple
    """
    weight2 = max(0.0, min(weight, 1.0))
    weight1: float = 1.0 - weight2
    return (
        int(color1[0] * weight1 + color2[0] * weight2),
        int(color1[1] * weight1 + color2[1] * weight2),
        int(color1[2] * weight1 + color2[2] * weight2),
    )

def set_brightness(color: tuple[int,int,int], brightness: float) -> tuple[int,int,int]:
	color_floats = [c/255 for c in color]
	fancy.gamma_adjust(color_floats, brightness=brightness, inplace=True)
	result = tuple(round(c*255) for c in color_floats)
	return result

class TransitionFunction():
	def __init__(self, easing: EasingBase, callback: callable[[float, any], None], callback_data: any = None) -> None:
		self.start_time = None
		self.easing = easing
		self.callback = callback
		self.callback_data = callback_data
		pass

	def loop(self):
		if self.start_time == None:
			self.start_time = monotonic()
		elapsed_time = min(self.easing.duration, monotonic() - self.start_time)
		self.callback(self.easing.ease(elapsed_time), self.callback_data)
		return self.easing.duration == elapsed_time
