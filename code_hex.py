import adafruit_logging as logging
log = logging.getLogger()
log.setLevel(10)
import board
from game_state import GameState
from easing import LinearInOut, BounceEaseOut

# =================== Settings =================== #
PIXELS_PIN = board.IO43             # Pin of the neopixel strip
PIXELS_LENGTH = 252                 # Length of the neopixel strip
SEAT_DEFINITIONS = ((231,42),(189,42),(147,42),(105,42),(63,42),(21,42))
LED_BRIGHTNESS_NORMAL = 0.1         # 0-1. How bright do you want the LED?
LED_BRIGHTNESS_HIGHLIGHT = 0.5      # When highlighting something, how bright should it be?
EASE_FADE = LinearInOut             # Easing function for color fades
EASE_FADE_DURATION = 0.8            # Duration of color fades
EASE_LINE = BounceEaseOut           # Easing function for moving the active player line
EASE_LINE_PIXEL_PER_SEC = 36        # How was the active player line moves (average)

BUTTON_PINS = [board.IO1, board.IO2, board.IO3, board.IO4, board.IO5, board.IO6]
BUTTON_VAL_WHEN_PRESSED = False

LATCH_PIN = board.IO44
SPI_CLOCK_PIN = board.IO7
SPI_MOSI_PIN = board.IO9

WIFI_SSID = "PanicStation"          # Your WIFI access point name
WIFI_PASSWORD = ""                  # Your WIFI password
# Setup your MQTT credentials here. Get them from https://sharedgametimer.com/mqtt
SGT_USER_ID = "CU0Cn1uchQdGASmCWQxPRG4wb6x1"
MQTT_HOST = "c360d66cbd94454898a146a8117eb5b2.s2.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_TOPIC_GAME = SGT_USER_ID + "/game"
MQTT_TOPIC_COMMAND = SGT_USER_ID + "/commands"
MQTT_USERNAME = "tester"
MQTT_PASSWORD = "1 Meeple"

# =============== End of Settings ================ #

# ---------- LEDs -------------#
from digitalio import DigitalInOut
from busio import SPI
from adafruit_74hc595 import ShiftRegister74HC595
# # Setup Button LEDs Shift Register
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
view = ViewMulti([
     ViewConsole(),
     ViewTableOutline(
          pixels,
          seat_definitions=SEAT_DEFINITIONS,
          brightness_normal=LED_BRIGHTNESS_NORMAL,
          brightness_highlight=LED_BRIGHTNESS_HIGHLIGHT,
          ease_fade=EASE_FADE,
          ease_fade_duration=EASE_FADE_DURATION,
          ease_line=EASE_LINE,
          ease_line_pixels_per_seconds=EASE_LINE_PIXEL_PER_SEC,
          ),
     ViewSeatedActionLeds(arcade_leds),
     ])
view.set_state(GameState())

# ---------- WIFI -------------#
from sgt_connection_mqtt import SgtConnectionMQTT
sgt_connection = SgtConnectionMQTT(view,
                 mqtt_host=MQTT_HOST,
                 mqtt_port=MQTT_PORT,
                 mqtt_username=MQTT_USERNAME,
                 mqtt_password=MQTT_PASSWORD,
                 mqtt_topic_game=MQTT_TOPIC_GAME,
                 mqtt_topic_command=MQTT_TOPIC_COMMAND,
                 wifi_ssid=WIFI_SSID,
                 wifi_password=WIFI_PASSWORD,
)

# ---------- BUTTONS SETUP -------------#
from buttons import Buttons
from microcontroller import Pin
button_pin_to_val_when_pressed = {}
for btn_pin in BUTTON_PINS:
    button_pin_to_val_when_pressed[btn_pin] = BUTTON_VAL_WHEN_PRESSED
buttons = Buttons(button_pin_to_val_when_pressed)
def btn_callback(btn_pin: Pin, presses: int, long_press: bool):
    def on_success():
        arcade_leds[BUTTON_PINS.index(btn_pin)].value = False

    if long_press:
        if presses == 1:
            sgt_connection.send_toggle_admin(on_success=on_success)
        elif presses == 2:
            sgt_connection.send_toggle_pause(on_success=on_success)
        elif presses == 3:
            sgt_connection.send_undo(on_success=on_success)
    else:
        seat = BUTTON_PINS.index(btn_pin) + 1
        if presses == 1:
            sgt_connection.send_primary(seat=seat, on_success=on_success)
        elif presses == 2:
            sgt_connection.send_secondary(seat=seat, on_success=on_success)

for btn_pin in BUTTON_PINS:
    buttons.set_callback(btn_pin, presses=1, callback = btn_callback)
    buttons.set_callback(btn_pin, presses=2, callback = btn_callback)
    buttons.set_callback(btn_pin, presses=1, long_press=True, callback = btn_callback)
    buttons.set_callback(btn_pin, presses=2, long_press=True, callback = btn_callback)
    buttons.set_callback(btn_pin, presses=3, long_press=True, callback = btn_callback)


is_polling = None
# ---------- MAIN LOOP -------------#
while True:
    if not sgt_connection.is_connected():
          sgt_connection.connect()
    while not sgt_connection.is_connected():
          view.animate()
    while sgt_connection.is_connected():
        busy_animating = view.animate()
        busy_pressing_buttons = buttons.loop()
        interruptable = not(busy_animating or busy_pressing_buttons)
        if interruptable and is_polling == False:
            log.debug('======== ENABLE POLLING ========')
        if not interruptable and is_polling == True:
            log.debug('======== DISABLE POLLING ========')
        is_polling = interruptable
        if is_polling:
            sgt_connection.poll()