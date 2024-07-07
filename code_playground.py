import adafruit_logging as logging
log = logging.getLogger()
log.setLevel(10)
import json
from settings import BLE_DEVICE_NAME
from game_state import GameState
from adafruit_circuitplayground import cp

# Suggested Script and Action Mapping
# These are sent on connection to the SGT to pre-populate the Action/Write scripts for quick save.
BLUETOOTH_FIELD_DIVIDER = ';'
BLUETOOTH_FIELD_ORDER = ["timerMode","state","color","turnTime","playerTime"]
suggestions = {
	"script": [
		f'0 {BLUETOOTH_FIELD_DIVIDER.join(BLUETOOTH_FIELD_ORDER)}%0A'
],
	"scriptName": BLE_DEVICE_NAME + " Write",
	"defaultTriggers": ["includePlayers","includePause","includeAdmin","includeSimultaneousTurns","includeGameStart","includeGameEnd","includeSandTimerStart","includeSandTimerReset","includeSandTimerStop","includeSandTimerOutOfTime","runOnStateChange","runOnPlayerOrderChange","runOnPoll","runOnBluetoothConnect","runOnBluetoothDisconnect"],
	"actionMap": [
		('Button AB', 'remoteActionToggleAdmin'),
		('Button A', 'remoteActionPrimary'),
		('Button B', 'remoteActionSecondary'),
		('Shake', 'remoteActionUndo'),
		('Connected', 'remoteActionPoll'),
		('To Face Down', 'remoteActionTurnAdminOn'),
		('From Face Down', 'remoteActionTurnAdminOff'),
		('Switch ON', 'remoteActionTurnPauseOn'),
		('Switch OFF', 'remoteActionTurnPauseOff'),
	],
	"actionMapName": BLE_DEVICE_NAME + " Actions",
}

# ---------- IMPORT REQUIRED TO SHOW SPLASH -------------#
import board
import time
from settings import LED_BRIGHTNESS
from accelerometer_playground import Accelerometer_Playground
from orientation import Orientation

# ---------- VIEW SETUP -------------#
from view_multi import ViewMulti
from view_console import ViewConsole
from view_playground import ViewPlayground
cp.pixels.brightness = LED_BRIGHTNESS

from adafruit_dotstar import DotStar
dots = DotStar(board.SCL, board.SDA, 30, brightness=LED_BRIGHTNESS)
view = ViewMulti([ViewConsole(), ViewPlayground(cp.pixels), ViewPlayground(dots)])

# ---------- SOUNDS -------------#
from tone_playground import TonePlayground
tone = TonePlayground()

# ---------- BLUETOOTH SETUP -------------#
from sgt_connection_bluetooth import SgtConnectionBluetooth
def on_connect():
	ts = time.monotonic()
	while time.monotonic() - ts < 2:
		view.animate()
	sgt_connection.send("Connected")

def on_state_line(state_line, timestamp):
	if state_line == "GET SETUP SUGGESTIONS":
		sgt_connection.send(json.dumps(suggestions))
		sgt_connection.send("Connected")
	else:
		view.set_state(GameState(
			ble_state_string = state_line,
			ble_field_order = BLUETOOTH_FIELD_ORDER,
			ble_field_divider = BLUETOOTH_FIELD_DIVIDER,
			timestamp_offset = timestamp - time.monotonic()
			)
		)
sgt_connection = SgtConnectionBluetooth(view, on_connect=on_connect, on_state_line=on_state_line)

# ---------- ACCELEROMETER / ORIENTATION SETUP -------------#
accelerometer = Accelerometer_Playground()
accelerometer.set_shake_callback(lambda: sgt_connection.send_undo(on_success=tone.shake))
orientation = Orientation(accelerometer)
orientation.set_callback("z+", lambda _: sgt_connection.send("To Face Up"), lambda _: sgt_connection.send("To Face Down"))

# ---------- BUTTONS SETUP -------------#
from buttons import Buttons
buttons = Buttons({
	board.BUTTON_A: True,
	board.BUTTON_B: True,
})
buttons.set_callback(board.BUTTON_A, callback = lambda : sgt_connection.send("Button A", on_success=tone.success))
buttons.set_callback(board.BUTTON_B, callback = lambda : sgt_connection.send("Button B", on_success=tone.success))
buttons.set_callback_multikey({board.BUTTON_A, board.BUTTON_B}, callback=lambda : sgt_connection.send("Button AB", on_success=tone.success))
buttons.set_fallback(tone.cascade)

# ---------- MAIN LOOP -------------#
while True:
	if not sgt_connection.is_connected():
		sgt_connection.connect()
	while not sgt_connection.is_connected():
		view.animate()
	on_connect()
	while sgt_connection.is_connected():
		sgt_connection.poll()
		buttons.loop()
		accelerometer.loop()
		orientation.loop()
		view.animate()