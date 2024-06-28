import adafruit_logging as logging
log = logging.getLogger()
log.setLevel(10)
from game_state import GameState
from adafruit_circuitplayground import cp

# =================== Settings =================== #
SEAT_DEFINITIONS = [(0,6),(6,6),(12,6),(18,6),(24,6)]
LED_BRIGHTNESS_NORMAL = 0.1         # 0-1. How bright do you want the LED?
LED_BRIGHTNESS_HIGHLIGHT = 0.5      # When highlighting something, how bright should it be?
SHAKE_THRESHOLD = 20                # How sensitive should it be for detecting shakes?
DOUBLE_SHAKE_PREVENTION_TIMEOUT = 3 # Seconds after a shake when no second shake can be detected
ORIENTATION_ON_THRESHOLD = 9.0      # 0-10. Higher number, less sensitive.
ORIENTATION_OFF_THRESHOLD = 4.0     # 0-10. Higher number, more sensitive.
ORIENTATION_CHANGE_DELAY = 1        # How long to debounce changes in orientation

# =============== End of Settings ================ #


# Suggested Script and Action Mapping
# These are sent on connection to the SGT to pre-populate the Action/Write scripts for quick save.
BLE_DEVICE_NAME = "Hex Table"
BLUETOOTH_FIELD_DIVIDER = ';'
BLUETOOTH_FIELD_ORDER = ['sgtTimerMode','sgtState','sgtColor','sgtTurnTime','sgtPlayerTime','sgtTotalPlayTime','sgtGameStateVersion','sgtName','sgtSeat','sgtTs','sgtPlayerSeats','sgtPlayerColors','sgtPlayerNames','sgtPlayerActions','sgtActionPrimary','sgtActionInactive','sgtActionSecondary','sgtActionAdmin','sgtActionPause','sgtActionUndo']
suggestions = {
    "script": [
        f'0 %0A{BLUETOOTH_FIELD_DIVIDER.join(BLUETOOTH_FIELD_ORDER)}%0A'
],
    "scriptName": BLE_DEVICE_NAME + " Write",
    "defaultTriggers": ["includePlayers","includePause","includeAdmin","includeSimultaneousTurns","includeGameStart","includeGameEnd","includeSandTimerStart","includeSandTimerReset","includeSandTimerStop","includeSandTimerOutOfTime","runOnStateChange","runOnPlayerOrderChange", "runOnPoll"],
    "actionMap": [
        ('Enable ACK', 'remoteActionEnableAcknowledge'),
        ('ACK', 'remoteActionAcknowledge'),
        ('Poll', 'remoteActionPoll'),
        # ('Button AB', 'remoteActionToggleAdmin'),
        # ('Button A', 'remoteActionPrimary'),
        # ('Button B', 'remoteActionSecondary'),
        # ('Shake', 'remoteActionUndo'),
        # ('To Face Down', 'remoteActionTurnAdminOn'),
        # ('From Face Down', 'remoteActionTurnAdminOff'),
        # ('Switch ON', 'remoteActionTurnPauseOn'),
        # ('Switch OFF', 'remoteActionTurnPauseOff'),
        # ('Do Primary', 'remoteActionPrimary'),
        # ('Do Secondary', 'remoteActionSecondary'),
        # ('Do Undo', 'remoteActionUndo'),
        # ('Toggle Admin', 'remoteActionToggleAdmin'),
        # ('Admin On', 'remoteActionTurnAdminOn'),
        # ('Admin Off', 'remoteActionTurnAdminOff'),
        # ('Toggle Pause', 'remoteActionTogglePause'),
        # ('Pause On', 'remoteActionTurnPauseOn'),
        # ('Pause Off', 'remoteActionTurnPauseOff'),
        # ('Reorder', 'remoteActionReorder'),
    ],
    "actionMapName": "Hardcoded Actions",
}

# ---------- SHARED IMPORTS -------------#
import board
import time

# ---------- VIEW SETUP -------------#
from view_multi import ViewMulti
from view_console import ViewConsole
from view_table_outline import ViewTableOutline
cp.pixels.brightness = LED_BRIGHTNESS_NORMAL

from adafruit_dotstar import DotStar
dots = DotStar(board.SCL, board.SDA, 30, brightness=1, auto_write=False)
view = ViewMulti([ViewConsole(), ViewTableOutline(dots, seat_definitions=SEAT_DEFINITIONS, brightness_normal=LED_BRIGHTNESS_NORMAL, brightness_highlight=LED_BRIGHTNESS_HIGHLIGHT )])
view.set_state(GameState())

def set_state(log_label, state):
    log.debug(log_label)
    view.set_state(GameState(json_state_string=state, timestamp_offset=0))
    while not view.animate():
        log.debug('In an active animation')
    log.debug('No more active animation')
set_state('Game starts, green player 1.',           '{"players":[{"seat":1,"name":"Gus","color":"486bfa"}],"gameStateVersion":1,"ts":0,"state":"st"}')
set_state('Player 1 changes color to magenta',      '{"players":[{"seat":1,"name":"Gus","color":"41ff00"}],"gameStateVersion":2,"ts":0,"state":"st"}')
set_state('Add Player 2, red',                      '{"players":[{"seat":1,"name":"Gus","color":"41ff00"},              {"seat":2,"name":"Don","color":"ff0b00"}],              "gameStateVersion":3,"ts":0,"state":"st"}')
set_state('RED moves seat to #4',                   '{"players":[{"seat":1,"name":"Gus","color":"41ff00"},              {"seat":4,"name":"Don","color":"ff0b00"}],              "gameStateVersion":4,"ts":0,"state":"st"}')
# set_state('Start the game',                         '{"players":[{"seat":1,"name":"Gus","color":"41ff00","action":"pr"},{"seat":4,"name":"Don","color":"ff0b00"}],              "gameStateVersion":5,"ts":0,"timerMode":"cu","state":"pl","color":"41ff00","name":"Gus","seat":1,"turnTime":0,"playerTime":null,"totalPlayTime":0,"actions":{"primary":{"label":"Start Game","action":"game/startTurn"},"admin":{"label":"Start Setup","action":"game/startSetupAdmin"}}}')
# set_state('End Turn',                               '{"players":[{"seat":1,"name":"Gus","color":"41ff00"},              {"seat":4,"name":"Don","color":"ff0b00","action":"pr"}],"gameStateVersion":6,"ts":0,"timerMode":"cu","state":"pl","color":"ff0b00","name":"Don","seat":4,"turnTime":0,"playerTime":null,"totalPlayTime":1,"actions":{"primary":{"label":"End Turn","action":"game/endTurn"},"admin":{"label":"Start mid-turn admin","action":"game/startMidTurnAdmin"},"pause":{"label":"Pause","action":"game/pause"},"undo":{"label":"Undo","action":"game/undo"}}}')

log.debug('done')

while True:
     view.animate()
     pass

# ---------- SOUNDS -------------#
from tone_playground import TonePlayground
tone = TonePlayground()

# ---------- BLUETOOTH SETUP -------------#
from sgt_connection_bluetooth import SgtConnectionBluetooth
def on_state_line(state_line, timestamp):
    view.set_state(GameState(
        ble_state_string = state_line,
        ble_field_order = BLUETOOTH_FIELD_ORDER,
        ble_field_divider = BLUETOOTH_FIELD_DIVIDER,
        timestamp_offset = timestamp - time.monotonic()
        )
    )
def poll_for_latest_state():
     log.debug('Polling for new data')
     sgt_connection.send("Poll")
sgt_connection = SgtConnectionBluetooth(view,
                    suggestions=suggestions,
                    ble_device_name=BLE_DEVICE_NAME,
                    on_state_line=on_state_line,
                    on_error=poll_for_latest_state)

# ---------- ACCELEROMETER / ORIENTATION SETUP -------------#
from accelerometer_playground import Accelerometer_Playground
accelerometer = Accelerometer_Playground(shake_threshold=SHAKE_THRESHOLD, double_shake_prevention_timeout=DOUBLE_SHAKE_PREVENTION_TIMEOUT)
accelerometer.set_shake_callback(lambda: sgt_connection.send_undo(on_success=tone.shake))
from orientation import Orientation, AXIS_Z, DIR_NEG
orientation = Orientation(accelerometer, ORIENTATION_ON_THRESHOLD, ORIENTATION_OFF_THRESHOLD, ORIENTATION_CHANGE_DELAY)
orientation.set_callback(AXIS_Z, DIR_NEG, lambda _: sgt_connection.send("To Face Down"), lambda _: sgt_connection.send("From Face Down"))

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

is_polling = None
from gc import collect, mem_free
# ---------- MAIN LOOP -------------#
while True:
    if not sgt_connection.is_connected():
          sgt_connection.connect()
    while not sgt_connection.is_connected():
          view.animate()
    while sgt_connection.is_connected():
        interruptable = view.animate()
        if interruptable and is_polling == False:
            log.debug('======== ENABLE POLLING ========')
        if not interruptable and is_polling == True:
            log.debug('======== DISABLE POLLING ========')
        is_polling = interruptable
        if is_polling:
            time.sleep(1) # Simulate delay in checking connection
            log.debug('Free memory: %s', mem_free())
            sgt_connection.poll()
        buttons.loop()
        accelerometer.loop()
        orientation.loop()