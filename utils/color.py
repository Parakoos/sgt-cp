from utils.settings import get_float, get_string

# 0-1. How bright do you want the LED?
LED_BRIGHTNESS_NORMAL = get_float('LED_BRIGHTNESS_NORMAL', 0.1)
# When highlighting something, how bright should it be?
LED_BRIGHTNESS_HIGHLIGHT = get_float('LED_BRIGHTNESS_HIGHLIGHT', 0.6)
# Comma-separated list of steps to anchor saturation/steps to.
# E.g., "0.33,0.66" would ensure that the value can only be 0, 0.33, 0.66 or 1, whichever is closest
# Empty string leaves it unchanged, meaning it sets the value to whatever SGT provides.
# Values must be listed low to high.
_HSV_SATURATION_STEPS = get_string('HSV_SATURATION_STEPS', 0.5)
_HSV_VALUE_STEPS = get_string('HSV_VALUE_STEPS', 0.5)
# Add this amount to the saturation/value (before the step). Final amount will never negative or greater than 1.
HSV_SATURATION_MODIFIER = get_float('HSV_SATURATION_MODIFIER', 0.2)
HSV_VALUE_MODIFIER = get_float('HSV_VALUE_MODIFIER', 0.2)

if _HSV_SATURATION_STEPS != '':
	HSV_SATURATION_STEPS = [0.0] + [float(s) for s in _HSV_SATURATION_STEPS.split(',')] + [1.0]

if _HSV_VALUE_STEPS != '':
	HSV_VALUE_STEPS = [0.0] + [float(s) for s in _HSV_VALUE_STEPS.split(',')] + [1.0]

def find_step(steps: list[float], value: float):
	for i in range(len(steps)-1):
		if value >= steps[i] and value <= steps[i+1]:
			return steps[i] if value - steps[i] < steps[i+1] - value else steps[i+1]

import adafruit_fancyled.adafruit_fancyled as fancy
import adafruit_logging as logging
log = logging.getLogger()

class PlayerColor():
	def __init__(self, color_hex: str, hsv=False, adjustments=True) -> None:
		rgbOrHsv = [int(color_hex[0:2],16), int(color_hex[2:4],16), int(color_hex[4:6],16)]
		self.fancy = fancy.CHSV(*rgbOrHsv) if hsv else fancy.CRGB(*rgbOrHsv)
		if isinstance(self.fancy, fancy.CHSV) and adjustments:
			self.fancy.saturation = min(1.0, max(0.0, self.fancy.saturation+HSV_SATURATION_MODIFIER))
			self.fancy.value = min(1.0, max(0.0, self.fancy.value+HSV_VALUE_MODIFIER))
			if _HSV_SATURATION_STEPS != '':
				self.fancy.saturation = find_step(HSV_SATURATION_STEPS, self.fancy.saturation)
			if _HSV_VALUE_STEPS != '':
				self.fancy.value = find_step(HSV_VALUE_STEPS, self.fancy.value)
		self.black = DisplayedColor(self.fancy, 0.0)
		self.base = DisplayedColor(self.fancy, 1.0)
		self.dim = DisplayedColor(self.fancy, LED_BRIGHTNESS_NORMAL)
		self.highlight = DisplayedColor(self.fancy, LED_BRIGHTNESS_HIGHLIGHT)

	def __repr__(self):
		return  f'{self.fancy}'

class DisplayedColor():
	fancy_color: fancy.CRGB|fancy.CHSV
	brightness: float
	current_color: int
	def __init__(self, fancy_color: fancy.CRGB|fancy.CHSV, brightness: float) -> None:
		self.fancy_color = None
		self.brightness = None
		self.update(fancy_color, brightness)

	def update(self, fancy_color: fancy.CRGB|fancy.CHSV, brightness: float):
		rounded_brightness = round(brightness, 2)
		if self.fancy_color == fancy_color and self.brightness == rounded_brightness:
			return
		self.current_color = fancy.gamma_adjust(fancy_color, brightness=rounded_brightness).pack()
		self.fancy_color = fancy_color
		self.brightness = rounded_brightness

	def copy(self):
		return DisplayedColor(self.fancy_color, self.brightness)

	def is_black(self):
		if self.brightness == 0:
			return True
		if isinstance(self.fancy_color, fancy.CRGB):
			return self.fancy_color.red == 0 and self.fancy_color.green == 0 and self.fancy_color.blue == 0
		if isinstance(self.fancy_color, fancy.CHSV):
			return self.fancy_color.value == 0.0

	def __eq__(self, value: object) -> bool:
		if isinstance(value, DisplayedColor):
			if self.brightness != value.brightness:
				return False
			elif self.is_black() and value.is_black():
				return True
			else:
				return equally_fancy(self.fancy_color, value.fancy_color)
		else:
			return False

	def __repr__(self):
		return  f'{hex(self.current_color)}'

def equally_fancy(f1: fancy.CRGB|fancy.CHSV, f2: fancy.CRGB|fancy.CHSV):
	if f1 is f2:
		return True
	if isinstance(f1, fancy.CHSV) and isinstance(f2, fancy.CHSV):
		if f1.value == 0.0:
			return f1.value == f2.value
		elif f1.saturation == 0.0:
			return f1.saturation == f2.saturation and f1.value == f2.value
		else:
			return f1.hue == f2.hue and f1.saturation == f2.saturation and f1.value == f2.value
	elif isinstance(f1, fancy.CRGB) and isinstance(f2, fancy.CRGB):
		return f1.red == f2.red and f1.green == f2.green and f1.blue == f2.blue
	else:
		return f1.pack() == f2.pack()

WHITE = PlayerColor('0000ff', True, False)
BLACK = PlayerColor('000000', True, False)
BLUE = PlayerColor('aaffff', True, False)
RED = PlayerColor('00ffff', True, False)
