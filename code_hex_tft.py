import adafruit_logging as logging
log = logging.getLogger()
log.setLevel(10)
import board
from game_state import GameState
# from easing import LinearInOut, BounceEaseOut

# =================== Settings =================== #
# PIXELS_PIN = board.IO43			# Pin of the neopixel strip
# PIXELS_LENGTH = 252				# Length of the neopixel strip
# SEAT_DEFINITIONS = ((231,42),(189,42),(147,42),(105,42),(63,42),(21,42))
# LED_BRIGHTNESS_NORMAL = 0.1		# 0-1. How bright do you want the LED?
# LED_BRIGHTNESS_HIGHLIGHT = 0.5	# When highlighting something, how bright should it be?
# EASE_FADE = LinearInOut			# Easing function for color fades
# EASE_FADE_DURATION = 0.8			# Duration of color fades
# EASE_LINE = BounceEaseOut			# Easing function for moving the active player line
# EASE_LINE_PIXEL_PER_SEC = 36		# How was the active player line moves (average)

BUTTON_PINS = [board.BUTTON, board.D1, board.D2]
# BUTTON_VAL_WHEN_PRESSED = False

# LATCH_PIN = board.IO44
# SPI_CLOCK_PIN = board.IO7
# SPI_MOSI_PIN = board.IO9
# =============== End of Settings ================ #

# # ---------- LEDs -------------#
# from digitalio import DigitalInOut
# from busio import SPI
# from adafruit_74hc595 import ShiftRegister74HC595
# # # Setup Button LEDs Shift Register
# latch_pin = DigitalInOut(LATCH_PIN)
# spi = SPI(SPI_CLOCK_PIN, MOSI=SPI_MOSI_PIN)
# sr = ShiftRegister74HC595(spi, latch_pin)
# arcade_leds=[sr.get_pin(s) for s in range(len(SEAT_DEFINITIONS))]

# ---------- VIEW SETUP -------------#
from view_multi import ViewMulti
from view_console import ViewConsole
# from view_table_outline import ViewTableOutline
# from view_seated_action_leds import ViewSeatedActionLeds

# from neopixel import NeoPixel
# pixels = NeoPixel(PIXELS_PIN, PIXELS_LENGTH, brightness=1, auto_write=False)
view = ViewMulti([
	ViewConsole(),
	#  ViewTableOutline(
	#	pixels,
	#	seat_definitions=SEAT_DEFINITIONS,
	#	brightness_normal=LED_BRIGHTNESS_NORMAL,
	#	brightness_highlight=LED_BRIGHTNESS_HIGHLIGHT,
	#	ease_fade=EASE_FADE,
	#	ease_fade_duration=EASE_FADE_DURATION,
	#	ease_line=EASE_LINE,
	#	ease_line_pixels_per_seconds=EASE_LINE_PIXEL_PER_SEC,
	#	),
	#  ViewSeatedActionLeds(arcade_leds),
	])
view.set_state(GameState())

# ---------- WIFI -------------#
from sgt_connection_mqtt import SgtConnectionMQTT
sgt_connection = SgtConnectionMQTT(view)

# ---------- BUTTONS SETUP -------------#
from buttons import Buttons
from microcontroller import Pin
button_pin_to_val_when_pressed = {
	board.BUTTON: False,
	board.D1: True,
	board.D2: True,
}
buttons = Buttons(button_pin_to_val_when_pressed)
def btn_callback(btn_pin: Pin, presses: int, long_press: bool):
	log.info('btn_callback: %s, %s, %s', btn_pin, presses, long_press)
	if long_press:
		if presses == 1:
			sgt_connection.enqueue_send_toggle_admin()
		elif presses == 2:
			sgt_connection.enqueue_send_toggle_pause()
		elif presses == 3:
			sgt_connection.enqueue_send_undo()
		elif presses == 4:
			raise Exception('Test Error!')
	else:
		seat = BUTTON_PINS.index(btn_pin) + 1
		if presses == 1:
			sgt_connection.enqueue_send_primary(seat=seat)
		elif presses == 2:
			sgt_connection.enqueue_send_secondary(seat=seat)


# ---------- MAIN LOOP -------------#
from loop import main_loop, ErrorHandlerResumeOnButtonPress
error_handler = ErrorHandlerResumeOnButtonPress(view, buttons)
def on_connect():
	buttons.clear_callbacks()
	for btn_pin in BUTTON_PINS:
		buttons.set_callback(btn_pin, presses=1, callback = btn_callback)
		buttons.set_callback(btn_pin, presses=2, callback = btn_callback)
		buttons.set_callback(btn_pin, presses=1, long_press=True, callback = btn_callback)
		buttons.set_callback(btn_pin, presses=2, long_press=True, callback = btn_callback)
		buttons.set_callback(btn_pin, presses=3, long_press=True, callback = btn_callback)
		buttons.set_callback(btn_pin, presses=4, long_press=True, callback = btn_callback)

main_loop(sgt_connection, view, on_connect, error_handler.on_error, (buttons.loop,))