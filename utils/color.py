from utils.settings import get_float

# 0-1. How bright do you want the LED?
LED_BRIGHTNESS_NORMAL = get_float('TABLE_LED_BRIGHTNESS_NORMAL', 0.1)
# When highlighting something, how bright should it be?
LED_BRIGHTNESS_HIGHLIGHT = get_float('TABLE_LED_BRIGHTNESS_HIGHLIGHT', 0.5)

import adafruit_fancyled.adafruit_fancyled as fancy
import adafruit_logging as logging
log = logging.getLogger()

class PlayerColor():
	def __init__(self, color_hex: str, hsv=False) -> None:
		rgbOrHsv = [int(color_hex[0:2],16), int(color_hex[2:4],16), int(color_hex[2:4],16)]
		self.fancy = fancy.CHSV(*rgbOrHsv) if hsv else fancy.CRGB(*rgbOrHsv)
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
			if isinstance(self.fancy_color, fancy.CRGB):
				return isinstance(value.fancy_color, fancy.CRGB) and self.fancy_color.red == value.fancy_color.red and self.fancy_color.green == value.fancy_color.green and self.fancy_color.blue == value.fancy_color.blue
			if isinstance(self.fancy_color, fancy.CHSV):
				return isinstance(value.fancy_color, fancy.CHSV) and self.fancy_color.hue == value.fancy_color.hue and self.fancy_color.saturation == value.fancy_color.saturation and self.fancy_color.value == value.fancy_color.value
			raise Exception('Invalid fancy color type: %s', type(self.fancy_color))
		else:
			return False

	def __repr__(self):
		return  f'{hex(self.current_color)}'

WHITE = PlayerColor('0000ff', True)
BLACK = PlayerColor('000000', True)
BLUE = PlayerColor('aaffff', True)
RED = PlayerColor('00ffff', True)
