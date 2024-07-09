from utils.settings import get_float

# 0-1. How bright do you want the LED?
LED_BRIGHTNESS_NORMAL = get_float('TABLE_LED_BRIGHTNESS_NORMAL', 0.1)
# When highlighting something, how bright should it be?
LED_BRIGHTNESS_HIGHLIGHT = get_float('TABLE_LED_BRIGHTNESS_HIGHLIGHT', 0.5)

import adafruit_fancyled.adafruit_fancyled as fancy
import adafruit_logging as logging
log = logging.getLogger()

class PlayerColor():
	def __init__(self, color_hex: str) -> None:
		self.fancy = fancy.unpack(int(color_hex,16))
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

	def __repr__(self):
		return  f'{hex(self.current_color)}'

WHITE = PlayerColor('ffffff')
BLACK = PlayerColor('000000')
BLUE = PlayerColor('0000ff')
RED = PlayerColor('ff0000')
