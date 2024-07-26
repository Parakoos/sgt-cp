import adafruit_logging as logging
log = logging.getLogger()
log.setLevel(10)
import board
from game_state import GameState

# =================== Settings =================== #
PIXELS_PIN = board.IO43			# Pin of the neopixel strip
PIXELS_LENGTH = 252				# Length of the neopixel strip
SEAT_DEFINITIONS = ((231,42),(189,42),(147,42),(105,42),(63,42),(21,42))

BUTTON_PINS = [board.IO1, board.IO2, board.IO3, board.IO4, board.IO5, board.IO6]
BUTTON_VAL_WHEN_PRESSED = False

LATCH_PIN = board.IO44
SPI_CLOCK_PIN = board.IO7
SPI_MOSI_PIN = board.IO9
# =============== End of Settings ================ #

# ---------- ARCADE BUTTON LEDS -------------#
from digitalio import DigitalInOut
from busio import SPI
from adafruit_74hc595 import ShiftRegister74HC595
# Setup Button LEDs Shift Register
latch_pin = DigitalInOut(LATCH_PIN)
spi = SPI(SPI_CLOCK_PIN, MOSI=SPI_MOSI_PIN)
sr = ShiftRegister74HC595(spi, latch_pin)
arcade_leds=[sr.get_pin(s+1) for s in range(len(SEAT_DEFINITIONS))]

# ---------- VIEW SETUP -------------#
from view_multi import ViewMulti
from view_console import ViewConsole
from view_table_outline import ViewTableOutline
from view_seated_action_leds import ViewSeatedActionLeds

from neopixel import NeoPixel
pixels = NeoPixel(PIXELS_PIN, PIXELS_LENGTH, brightness=1, auto_write=False)
viewTableOutline = ViewTableOutline(pixels, seat_definitions=SEAT_DEFINITIONS)
view = ViewMulti([
	ViewConsole(),
	viewTableOutline,
	ViewSeatedActionLeds(arcade_leds),
	])
view.set_state(None)

# ---------- WIFI -------------#
from sgt_connection_mqtt import SgtConnectionMQTT
sgt_connection = SgtConnectionMQTT(view)
viewTableOutline.set_connection(sgt_connection)

# ---------- BUTTONS SETUP -------------#
from buttons import Buttons
from microcontroller import Pin
button_pin_to_val_when_pressed = {}
for btn_pin in BUTTON_PINS:
	button_pin_to_val_when_pressed[btn_pin] = BUTTON_VAL_WHEN_PRESSED
buttons = Buttons(button_pin_to_val_when_pressed)
sim_turn_selection_in_progress = False
def btn_callback(btn_pin: Pin, presses: int, long_press: bool):
	global sim_turn_selection_in_progress
	if sim_turn_selection_in_progress:
		# Stop reaction to buttons while the sim turn selection is in progress.
		return
	def on_success():
		arcade_leds[BUTTON_PINS.index(btn_pin)].value = False

	if long_press:
		if presses == 1:
			sgt_connection.enqueue_send_toggle_admin(on_success=on_success)
		elif presses == 2:
			# sgt_connection.enqueue_send_toggle_pause(on_success=on_success)
			if view.state.allow_sim_turn_start():
				seat = BUTTON_PINS.index(btn_pin) + 1
				viewTableOutline.begin_sim_turn_selection(seat)
				sim_turn_selection_in_progress = True
		elif presses == 3:
			sgt_connection.enqueue_send_undo(on_success=on_success)
	else:
		seat = BUTTON_PINS.index(btn_pin) + 1
		if presses == 1:
			sgt_connection.enqueue_send_primary(seat=seat, on_success=on_success)
		elif presses == 2:
			sgt_connection.enqueue_send_secondary(seat=seat, on_success=on_success)

def pressed_keys_update_callback(pressed_keys: set[Pin]):
	global sim_turn_selection_in_progress
	viewTableOutline.on_pressed_seats_change(set((BUTTON_PINS.index(btn_pin) + 1 for btn_pin in pressed_keys)))
	if len(pressed_keys) == 0:
		# We know the sim turn selection is over once all buttons have been released
		sim_turn_selection_in_progress = False

# ---------- MAIN LOOP -------------#
from loop import main_loop, ErrorHandlerResumeOnButtonPress
error_handler = ErrorHandlerResumeOnButtonPress(view, buttons)
def on_connect():
	buttons.clear_callbacks()
	buttons.set_pressed_keys_update_callback(pressed_keys_update_callback)
	for btn_pin in BUTTON_PINS:
		buttons.set_callback(btn_pin, presses=1, callback = btn_callback)
		buttons.set_callback(btn_pin, presses=2, callback = btn_callback)
		buttons.set_callback(btn_pin, presses=1, long_press=True, callback = btn_callback)
		buttons.set_callback(btn_pin, presses=2, long_press=True, callback = btn_callback)
		buttons.set_callback(btn_pin, presses=3, long_press=True, callback = btn_callback)
		buttons.set_callback(btn_pin, presses=4, long_press=True, callback = btn_callback)

main_loop(sgt_connection, view, on_connect, error_handler.on_error, (buttons.loop,))