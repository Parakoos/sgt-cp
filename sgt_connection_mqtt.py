import adafruit_logging as logging
log = logging.getLogger()
# from log.info import log.info
from ssl import create_default_context
from socketpool import SocketPool
from wifi import radio
from adafruit_minimqtt.adafruit_minimqtt import MQTT as ADA_MQTT
from settings import WIFI_SSID, WIFI_PASSWORD, MQTT_HOST, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD, MQTT_SUBSCRIBE_TOPIC, MQTT_PUBLISH_TOPIC
from adafruit_requests import Session
import time
# from typing import Type
from view import View
from sgt_connection import SgtConnection
from game_state import GameState
import json

pool = SocketPool(radio)
ssl_context = create_default_context()
is_connected = False

class SgtConnectionMQTT(SgtConnection):
    def __init__(self, view: View):
        super().__init__(view)
        self.last_poll_ts = -1000
        self.unix_time_offset = 0
        self.mqtt_client = ADA_MQTT(
            broker=MQTT_HOST,
            port=MQTT_PORT,
            username=MQTT_USERNAME,
            password=MQTT_PASSWORD,
            socket_pool=pool,
            ssl_context=ssl_context,
            is_ssl=True,
        )
        self.mqtt_client.on_connect = self.on_connected
        self.mqtt_client.on_disconnect = self.on_disconnected
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.enable_logger(logging, log_level=20, logger_name="mqtt")

    def is_connected(self):
        return self.mqtt_client.is_connected()

    def ensure_connected_to_wifi(self):
        if radio.ap_info == None:
            self.view.set_connection_progress_text(f"Connecting to WIFI ({WIFI_SSID})")
            radio.connect(WIFI_SSID, WIFI_PASSWORD)
            log.info(radio.ap_info)
            self.lookup_unix_time_offset()

    def connect(self) -> bool:
        self.ensure_connected_to_wifi()
        self.view.set_connection_progress_text(f"Connecting to MQTT")
        self.mqtt_client.connect()

    def on_connected(self, client, userdata, flags, rc):
        log.info(f"Connected to MQTT! Listening for topic changes on {MQTT_SUBSCRIBE_TOPIC}")
        client.subscribe(MQTT_SUBSCRIBE_TOPIC)

    def on_disconnected(self, client, userdata, rc):
        log.info("Disconnected from MQTT!")

    def on_message(self, client, topic, message:str):
        log.info(f"MQTT message: {message}")
        game_state = GameState(state_json=message, timestamp_offset=self.unix_time_offset)
        self.view.set_state(game_state)

    def send(self, value: str, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        log.info("send: %s", value)

        if value == None:
            if on_failure != None:
                on_failure()
            return
        if not self.mqtt_client.is_connected():
            self.connect()
        action = json.dumps({"gameStateVersion": self.view.state.game_state_version, "action": value})
        log.debug('MQTT Publish to %s value %s', MQTT_PUBLISH_TOPIC, action)
        self.mqtt_client.publish(MQTT_PUBLISH_TOPIC, action)
        if on_success != None:
            on_success()

    def send_primary(self, on_success, on_failure):
        log.info("send_primary: %s", self.view.state.action_primary)
        return self.send(self.view.state.action_primary, on_success, on_failure)

    def send_secondary(self, on_success, on_failure):
        return self.send(self.view.state.action_secondary, on_success, on_failure)

    def send_admin(self, on_success, on_failure):
        return self.send(self.view.state.action_admin, on_success, on_failure)

    def send_pause(self):
        if self.view.state.has_action('game/pause'):
            return self.send('game/pause')

    def send_unpause(self):
        if self.view.state.has_action('game/unpause'):
            return self.send('game/unpause')

    def send_undo(self, on_success: callable[[], None] = None):
        return self.send('game/undo', on_success)

    def poll(self):
        if not self.mqtt_client.is_connected():
            self.connect()
        self.mqtt_client.loop(1)

    def lookup_unix_time_offset(self):
        self.view.set_connection_progress_text('Getting current time')
        requests = Session(pool, ssl_context)
        response = requests.get('http://worldtimeapi.org/api/timezone/Etc/UTC')
        now = round(time.monotonic())
        json = response.json()
        time_unix_sec = json['unixtime']
        diff = now - time_unix_sec
        log.info(f"Current Unix Time: {time_unix_sec} at mono {now} (diff: {diff})")
        self.unix_time_offset = diff
