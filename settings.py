
# Set your wifi credentials here
# WIFI_SSID = "SHODAN"
# WIFI_PASSWORD = "enlightened"
WIFI_SSID = "Kvänjarp" # "verizon"
WIFI_PASSWORD = "037214424" # "3720gaviota"

# Setup your MQTT credentials here. Get them from https://sharedgametimer.com/mqtt
SGT_USER_ID = "S3I2DekROZtQNPPX0fdaiENL3lrt" # "DogN7jdBk1YA2e790SVtcl3MOjG3"
MQTT_HOST = "c360d66cbd94454898a146a8117eb5b2.s2.eu.hivemq.cloud"
MQTT_PORT = 8883
# MQTT_PATH = "/mqtt"
MQTT_SUBSCRIBE_TOPIC = SGT_USER_ID + "/game"
MQTT_PUBLISH_TOPIC = SGT_USER_ID + "/commands"
MQTT_USERNAME = "tester"
MQTT_PASSWORD = "1 Meeple"
MQTT_POLL_FREQ = 5
MQTT_IS_SSL = True

BRIGHTNESS_OPTIONS = [0.06, 0.2, 0.4, 0.7, 1.0]    # The different brightnesses to cycle through
BRIGHTNESS_INITIAL_INDEX = 4       # 0-indexed. Which brightness to start with.

from board import A1
PIEZO_PIN = A1

MOVEMENT_THRESHOLD = 18
INACTIVITY_THRESHOLD = 18
INACTIVITY_TIME = 4

ORIENTATION_ON_THRESHOLD = 8.0      # 0-10. Higher number, less sensitive.
ORIENTATION_OFF_THRESHOLD = 4.0     # 0-10. Higher number, more sensitive.
ORIENTATION_RIGHT = 'Right'         # The names of the various directions.
ORIENTATION_LEFT = 'Left'
ORIENTATION_STANDING = 'Standing'
ORIENTATION_UPSIDE_DOWN = 'Upside Down'
ORIENTATION_FACE_DOWN = 'Face Down'
ORIENTATION_FACE_UP = 'Face Up'

# Circuit Python Settings
BLE_DEVICE_NAME = "Circuit Playground"
SEC_PER_LIGHT = 60                  # How many seconds does each lit light represent?
LED_BRIGHTNESS = 0.1                # 0-1. How bright do you want the LED?
SHAKE_THRESHOLD = 20                # How sensitive should it be for detecting shakes?
DOUBLE_SHAKE_PREVENTION_TIMEOUT = 3 # Seconds after a shake when no second shake can be detected
ORIENTATION_CHANGE_DELAY = 1        # How long to debounce changes in orientation
ORIENTATION_ON_THRESHOLD = 9.0      # 0-10. Higher number, less sensitive.
ORIENTATION_OFF_THRESHOLD = 4.0     # 0-10. Higher number, more sensitive.
ORIENTATION_FACE_DOWN = 'Face Down' # The names of the various directions.
ORIENTATION_FACE_UP = 'Face Up'     # These are sent as 'To/From <name>'
ORIENTATION_ACTIVATIONS = {         # Which orientations should you send to the SGT?
    ORIENTATION_FACE_DOWN: True,    # Enabling all should work, but will send a lot of
    ORIENTATION_FACE_UP: True,     # notifications to the timer.
}

SAND_COLOR_OUT_OF_TIME = (255, 0, 0)
SAND_COLOR_TIME_LEFT = (0, 255, 0)
SAND_COLOR_TIME_USED = (0, 0, 160)