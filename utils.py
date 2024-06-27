from time import monotonic
import adafruit_fancyled.adafruit_fancyled as fancy
import adafruit_logging as logging
log = logging.getLogger()

def find_int(i: iter[int], default: int) -> int:
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
    weight2 = max(weight, min(0.0, 1.0))
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