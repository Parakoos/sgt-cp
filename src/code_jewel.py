import adafruit_logging as logging
log = logging.getLogger()
log.setLevel(10)
from adafruit_led_animation.animation.rainbow import Rainbow

# Suggested Script and Action Mapping
# These are sent on connection to the SGT to pre-populate the Action/Write scripts for quick save.
BLE_DEVICE_NAME = "Jewel"
BLUETOOTH_FIELD_DIVIDER = ';'
BLUETOOTH_FIELD_ORDER = ['sgtTimerMode','sgtState','sgtColorHsv','sgtTurnTime','sgtPlayerTime','sgtTotalPlayTime','sgtTimeReminders']

# ---------- SHARED IMPORTS -------------#
import board

# ---------- VIEW SETUP -------------#
from view_multi import ViewMulti
from view_console import ViewConsole
from view_mono_light import ViewMonoLight
from view_time_reminder_onoff import ViewTimeReminderOnOff
from pausable_pixels import PausablePixels
from adafruit_led_animation.helper import PixelSubset
_dots = PausablePixels(board.D6, 19, brightness=0.3, auto_write=False)
outer_ring = PixelSubset(_dots, 0, 12)
central_dot = PixelSubset(_dots, 12, 13)
middle_ring = PixelSubset(_dots, 13, 19)
central_disk = PixelSubset(_dots, 12, 19)

def vibrate_on():
	central_disk.fill((255,0,0))
	central_disk.show()
def vibrate_off():
	central_disk.fill((0,0,0))
	central_disk.show()

view = ViewMulti([
	ViewConsole(),
	ViewMonoLight(outer_ring),
	ViewTimeReminderOnOff(vibrate_on, vibrate_off),
	])
view.set_state(None)

# ---------- BLUETOOTH SETUP -------------#
from sgt_connection_bluetooth import SgtConnectionBluetooth
sgt_connection = SgtConnectionBluetooth(view,
		device_name=BLE_DEVICE_NAME,
		field_order=BLUETOOTH_FIELD_ORDER,
		field_divider=BLUETOOTH_FIELD_DIVIDER,
	)

# ---------- BUTTONS SETUP -------------#
from buttons import Buttons
from microcontroller import Pin
btn_pin = board.D4  # The button pin used for the single button on the Jewel
buttons = Buttons({btn_pin: False})
def btn_callback(pin: Pin, presses: int, long_press: bool):
	log.info(f"Button pressed: {presses} times, long press: {long_press}")
	def on_success():
		pass

	if long_press:
		if presses == 1:
			sgt_connection.enqueue_send_toggle_admin(on_success=on_success)
		elif presses == 2:
			sgt_connection.enqueue_send_undo(on_success=on_success)
	else:
		if presses == 1:
			sgt_connection.enqueue_send_primary(on_success=on_success)
		elif presses == 2:
			sgt_connection.enqueue_send_secondary(on_success=on_success)

def pressed_keys_callback(pins: set[Pin]):
	if len(pins) == 0:
		_dots.pause = False
		central_dot.fill(0x0)
		central_dot.show()
	else:
		_dots.pause = False
		central_dot.fill(0xFFFFFF)
		central_dot.show()
		_dots.pause = True

# ---------- MAIN LOOP -------------#
from loop import main_loop, ErrorHandlerResumeOnButtonPress
error_handler = ErrorHandlerResumeOnButtonPress(view, buttons)
def on_connect():
	buttons.clear_callbacks()
	buttons.set_callback(pin=btn_pin, presses=1, callback = btn_callback)
	buttons.set_callback(pin=btn_pin, presses=2, callback = btn_callback)
	buttons.set_callback(pin=btn_pin, presses=1, long_press=True, callback = btn_callback)
	buttons.set_callback(pin=btn_pin, presses=2, long_press=True, callback = btn_callback)
	buttons.set_pressed_keys_update_callback(pressed_keys_callback)

main_loop(sgt_connection, view, on_connect, error_handler.on_error, (buttons.loop,))