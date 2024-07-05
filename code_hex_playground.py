import adafruit_logging as logging
log = logging.getLogger()
log.setLevel(10)
from game_state import GameState
# from adafruit_circuitplayground import cp
from easing import LinearInOut, BounceEaseInOut, CubicEaseInOut

# =================== Settings =================== #
SEAT_DEFINITIONS = [(0,6),(6,6),(12,6),(18,6),(24,6)]
LED_BRIGHTNESS_NORMAL = 0.1         # 0-1. How bright do you want the LED?
LED_BRIGHTNESS_HIGHLIGHT = 0.5      # When highlighting something, how bright should it be?
SHAKE_THRESHOLD = 20                # How sensitive should it be for detecting shakes?
DOUBLE_SHAKE_PREVENTION_TIMEOUT = 3 # Seconds after a shake when no second shake can be detected
ORIENTATION_ON_THRESHOLD = 9.0      # 0-10. Higher number, less sensitive.
ORIENTATION_OFF_THRESHOLD = 4.0     # 0-10. Higher number, more sensitive.
ORIENTATION_CHANGE_DELAY = 1        # How long to debounce changes in orientation
EASE_FADE = LinearInOut             # Easing function for color fades
EASE_FADE_DURATION = 0.5            # Duration of color fades
EASE_WARN = (CubicEaseInOut, CubicEaseInOut) # Easing functions to and from a warning highlight, mostly during time reminders.
EASE_WARN_DURATION = 0.5            # The duration of a warning
EASE_WARN_MAX_TIMES = 5             # Maximum times a warning is shown in series
EASE_LINE = BounceEaseInOut         # Easing function for moving the active player line
EASE_LINE_PIXEL_PER_SEC = 5         # How was the active player line moves (average)
# =============== End of Settings ================ #


# Suggested Script and Action Mapping
# These are sent on connection to the SGT to pre-populate the Action/Write scripts for quick save.
BLE_DEVICE_NAME = "Hex Table (Playground)"
BLUETOOTH_FIELD_DIVIDER = ';'
# BLUETOOTH_FIELD_ORDER = ['sgtTimerMode','sgtState','sgtColor','sgtTurnTime','sgtPlayerTime','sgtTotalPlayTime','sgtGameStateVersion','sgtName','sgtSeat','sgtTs','sgtPlayerSeats','sgtPlayerColors','sgtPlayerNames','sgtPlayerActions','sgtActionPrimary','sgtActionInactive','sgtActionSecondary','sgtActionAdmin','sgtActionPause','sgtActionUndo']
BLUETOOTH_FIELD_ORDER = ['sgtTimerMode','sgtState','sgtTurnTime','sgtPlayerTime','sgtTotalPlayTime', 'sgtTimeReminders','sgtPlayerSeats','sgtPlayerColors','sgtPlayerActions','sgtSeat']
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
        ('Primary', 'remoteActionPrimary'),
        ('Secondary', 'remoteActionSecondary'),
        ('Undo', 'remoteActionUndo'),
        ('ToggleAdmin', 'remoteActionToggleAdmin'),
        ('TurnAdminOn', 'remoteActionTurnAdminOn'),
        ('TurnAdminOff', 'remoteActionTurnAdminOff'),
        ('TogglePause', 'remoteActionTogglePause'),
        ('TurnPauseOn', 'remoteActionTurnPauseOn'),
        ('TurnPauseOff', 'remoteActionTurnPauseOff'),
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
# from view_seated_action_leds import ViewSeatedActionLeds
# from pixel_as_digital_out import PixelAsDigitalOut
# cp.pixels.brightness = LED_BRIGHTNESS_NORMAL

# arcade_leds = [PixelAsDigitalOut(cp.pixels, s) for s in range(len(SEAT_DEFINITIONS))]

from adafruit_dotstar import DotStar
dots = DotStar(board.SCL, board.SDA, 30, brightness=1, auto_write=False)
view = ViewMulti([
     ViewConsole(),
     ViewTableOutline(
          dots,
          seat_definitions=SEAT_DEFINITIONS,
          brightness_normal=LED_BRIGHTNESS_NORMAL,
          brightness_highlight=LED_BRIGHTNESS_HIGHLIGHT,
          ease_fade=EASE_FADE,
          ease_fade_duration=EASE_FADE_DURATION,
          ease_warn=EASE_WARN,
          ease_warn_duration=EASE_WARN_DURATION,
          ease_warn_max_times=EASE_WARN_MAX_TIMES,
          ease_line=EASE_LINE,
          ease_line_pixels_per_seconds=EASE_LINE_PIXEL_PER_SEC,
          ),
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
# from accelerometer_playground import Accelerometer_Playground
# accelerometer = Accelerometer_Playground(shake_threshold=SHAKE_THRESHOLD, double_shake_prevention_timeout=DOUBLE_SHAKE_PREVENTION_TIMEOUT)
# accelerometer.set_shake_callback(lambda: sgt_connection.send_undo(on_success=tone.shake))
# from orientation import Orientation, AXIS_Z, DIR_NEG
# orientation = Orientation(accelerometer, ORIENTATION_ON_THRESHOLD, ORIENTATION_OFF_THRESHOLD, ORIENTATION_CHANGE_DELAY)
# orientation.set_callback(AXIS_Z, DIR_NEG, lambda _: sgt_connection.send("To Face Down"), lambda _: sgt_connection.send("From Face Down"))

# ---------- BUTTONS SETUP -------------#
# from buttons import Buttons
# from microcontroller import Pin
# BUTTON_PINS = (board.BUTTON_A, board.BUTTON_B)
# button_pin_to_val_when_pressed = {}
# for btn_pin in BUTTON_PINS:
#     button_pin_to_val_when_pressed[btn_pin] = True
# buttons = Buttons(button_pin_to_val_when_pressed)
# def btn_callback(btn_pin: Pin, presses: int, long_press: bool):
#     def on_success():
#         arcade_leds[BUTTON_PINS.index(btn_pin)].value = False
#         tone.success()

#     if long_press:
#         if presses == 1:
#             sgt_connection.send_toggle_admin(on_success=on_success, on_failure=tone.error)
#         elif presses == 2:
#             sgt_connection.send_toggle_pause(on_success=on_success, on_failure=tone.error)
#         elif presses == 3:
#             sgt_connection.send_undo(on_success=on_success, on_failure=tone.error)
#     else:
#         seat = BUTTON_PINS.index(btn_pin) + 1
#         if presses == 1:
#             sgt_connection.send_primary(seat=seat, on_success=on_success, on_failure=tone.error)
#         elif presses == 2:
#             sgt_connection.send_secondary(seat=seat, on_success=on_success, on_failure=tone.error)

# for btn_pin in BUTTON_PINS:
#     buttons.set_callback(btn_pin, presses=1, callback = btn_callback)
#     buttons.set_callback(btn_pin, presses=2, callback = btn_callback)
#     buttons.set_callback(btn_pin, presses=1, long_press=True, callback = btn_callback)
#     buttons.set_callback(btn_pin, presses=2, long_press=True, callback = btn_callback)
#     buttons.set_callback(btn_pin, presses=3, long_press=True, callback = btn_callback)
# # buttons.set_callback_multikey({board.BUTTON_A, board.BUTTON_B}, callback=lambda : sgt_connection.send("Button AB", on_success=on_success))
# buttons.set_fallback(tone.cascade)

# ---------- MAIN LOOP -------------#
from loop import main_loop
main_loop(sgt_connection, view, ())