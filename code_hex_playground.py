import adafruit_logging as logging
log = logging.getLogger()
log.setLevel(10)
from game_state import GameState
# from adafruit_circuitplayground import cp

# =================== Settings =================== #
SEAT_DEFINITIONS = [(0,6),(6,6),(12,6),(18,6),(24,6)]
# SEAT_DEFINITIONS = [(0,10),(10,10),(20,10)]
LED_BRIGHTNESS_NORMAL = 0.1				# 0-1. How bright do you want the LED?
LED_BRIGHTNESS_HIGHLIGHT = 0.5			# When highlighting something, how bright should it be?
SHAKE_THRESHOLD = 20					# How sensitive should it be for detecting shakes?
DOUBLE_SHAKE_PREVENTION_TIMEOUT = 3		# Seconds after a shake when no second shake can be detected
ORIENTATION_ON_THRESHOLD = 9.0			# 0-10. Higher number, less sensitive.
ORIENTATION_OFF_THRESHOLD = 4.0			# 0-10. Higher number, more sensitive.
ORIENTATION_CHANGE_DELAY = 1			# How long to debounce changes in orientation
# =============== End of Settings ================ #

# Suggested Script and Action Mapping
# These are sent on connection to the SGT to pre-populate the Action/Write scripts for quick save.
BLE_DEVICE_NAME = "Hex Table (Playground)"
BLUETOOTH_FIELD_DIVIDER = ';'
# BLUETOOTH_FIELD_ORDER = ['sgtTimerMode','sgtState','sgtColor','sgtTurnTime','sgtPlayerTime','sgtTotalPlayTime','sgtGameStateVersion','sgtName','sgtSeat','sgtTs','sgtPlayerSeats','sgtPlayerColors','sgtPlayerNames','sgtPlayerActions','sgtActionPrimary','sgtActionInactive','sgtActionSecondary','sgtActionAdmin','sgtActionPause','sgtActionUndo']
BLUETOOTH_FIELD_ORDER = ['sgtTimerMode','sgtState','sgtColorHsv','sgtTurnTime','sgtPlayerTime','sgtTotalPlayTime', 'sgtTimeReminders','sgtPlayerSeats','sgtPlayerColorsHsv','sgtPlayerActions','sgtSeat']

# ---------- SHARED IMPORTS -------------#
import board

# ---------- VIEW SETUP -------------#
from view_multi import ViewMulti
from view_console import ViewConsole
from view_table_outline import ViewTableOutline
# from view_seated_action_leds import ViewSeatedActionLeds
# from pixel_as_digital_out import PixelAsDigitalOut
# cp.pixels.brightness = LED_BRIGHTNESS_NORMAL

# arcade_leds = [PixelAsDigitalOut(cp.pixels, s) for s in range(len(SEAT_DEFINITIONS))]

from adafruit_dotstar import DotStar
dots = DotStar(board.SCL, board.SDA, 30, brightness=1, auto_write=False)
viewTableOutline = ViewTableOutline(dots, seat_definitions=SEAT_DEFINITIONS)
view = ViewMulti([
	ViewConsole(),
	viewTableOutline,
	#  ViewSeatedActionLeds(arcade_leds),
	])
view.set_state(GameState())

# ---------- SOUNDS -------------#
# from tone_playground import TonePlayground
# tone = TonePlayground()

from tone import Tone
tone = Tone()

# ---------- BLUETOOTH SETUP -------------#
from sgt_connection_bluetooth import SgtConnectionBluetooth
sgt_connection = SgtConnectionBluetooth(view,
					device_name=BLE_DEVICE_NAME,
					field_order=BLUETOOTH_FIELD_ORDER,
					field_divider=BLUETOOTH_FIELD_DIVIDER,
				)

# ---------- ACCELEROMETER / ORIENTATION SETUP -------------#
# from accelerometer_playground import Accelerometer_Playground
# accelerometer = Accelerometer_Playground(shake_threshold=SHAKE_THRESHOLD, double_shake_prevention_timeout=DOUBLE_SHAKE_PREVENTION_TIMEOUT)
# accelerometer.set_shake_callback(lambda: sgt_connection.enqueue_send_undo(on_success=tone.shake))
# from orientation import Orientation, AXIS_Z, DIR_NEG
# orientation = Orientation(accelerometer, ORIENTATION_ON_THRESHOLD, ORIENTATION_OFF_THRESHOLD, ORIENTATION_CHANGE_DELAY)
# orientation.set_callback(AXIS_Z, DIR_NEG, lambda _: sgt_connection.send("To Face Down"), lambda _: sgt_connection.send("From Face Down"))

# ---------- BUTTONS SETUP -------------#
from buttons import Buttons
from microcontroller import Pin
BUTTON_PINS = (board.BUTTON_A, board.BUTTON_B)
button_pin_to_val_when_pressed = {}
for btn_pin in BUTTON_PINS:
	button_pin_to_val_when_pressed[btn_pin] = True
buttons = Buttons(button_pin_to_val_when_pressed)
def btn_callback(btn_pin: Pin, presses: int, long_press: bool):
	def on_success():
		# arcade_leds[BUTTON_PINS.index(btn_pin)].value = False
		tone.success()

	if long_press:
		if presses == 1:
			sgt_connection.enqueue_send_toggle_admin(on_success=on_success, on_failure=tone.error)
		elif presses == 2:
			sgt_connection.enqueue_send_toggle_pause(on_success=on_success, on_failure=tone.error)
		elif presses == 3:
			sgt_connection.enqueue_send_undo(on_success=on_success, on_failure=tone.error)
		elif presses == 4:
			raise Exception('Test Error!')
	else:
		seat = BUTTON_PINS.index(btn_pin) + 1
		if presses == 1:
			sgt_connection.enqueue_send_primary(seat=seat, on_success=on_success, on_failure=tone.error)
		elif presses == 2:
			sgt_connection.enqueue_send_secondary(seat=seat, on_success=on_success, on_failure=tone.error)


def pressed_keys_update_callback(pressed_keys: set[Pin]):
	viewTableOutline.on_pressed_seats_change(set((BUTTON_PINS.index(btn_pin) + 1 for btn_pin in pressed_keys)))

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
		buttons.set_fallback(btn_callback)
		# buttons.set_callback_multikey({board.BUTTON_A, board.BUTTON_B}, callback=lambda : sgt_connection.send("Button AB", on_success=on_success))

main_loop(sgt_connection, view, on_connect, error_handler.on_error, (buttons.loop,))