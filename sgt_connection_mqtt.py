import adafruit_logging as logging
log = logging.getLogger()
from ssl import create_default_context
from socketpool import SocketPool
from wifi import radio
from adafruit_minimqtt.adafruit_minimqtt import MQTT as ADA_MQTT
from adafruit_requests import Session
import time
from view import View
from sgt_connection import SgtConnection
from game_state import GameState
import json

pool = SocketPool(radio)
ssl_context = create_default_context()
is_connected = False

class SgtConnectionMQTT(SgtConnection):
	def __init__(self,
				view: View,
				mqtt_host: str,
				mqtt_port: int,
				mqtt_username: str,
				mqtt_password: str,
				mqtt_topic_game: str,
				mqtt_topic_command: str,
				wifi_ssid: str,
				wifi_password: str,
				manual_time_offset: int,
				):
		super().__init__(view)
		self.mqtt_topic_game = mqtt_topic_game
		self.mqtt_topic_command = mqtt_topic_command
		self.wifi_ssid = wifi_ssid
		self.wifi_password = wifi_password
		self.last_poll_ts = -1000
		self.unix_time_offset = 0
		self.manual_time_offset = manual_time_offset
		self.mqtt_client = ADA_MQTT(
			broker=mqtt_host,
			port=mqtt_port,
			username=mqtt_username,
			password=mqtt_password,
			socket_pool=pool,
			ssl_context=ssl_context,
			is_ssl=True,
		)
		self.mqtt_client.on_connect = self._on_connected
		self.mqtt_client.on_disconnect = self._on_disconnected
		self.mqtt_client.on_message = self._on_message
		self.mqtt_client.enable_logger(logging, log_level=20, logger_name="mqtt")
		self.queue = []
		self.latest_message = None

	def is_connected(self):
		return self.mqtt_client.is_connected()

	def _ensure_connected_to_wifi(self):
		if radio.ap_info == None:
			self.view.set_connection_progress_text(f"Connecting to WIFI ({self.wifi_ssid})")
			radio.connect(self.wifi_ssid, self.wifi_password)
			log.info(radio.ap_info)

	def connect(self) -> bool:
		self._ensure_connected_to_wifi()
		self._lookup_unix_time_offset()
		self.view.set_connection_progress_text(f"Connecting to MQTT")
		self.mqtt_client.connect()

	def _on_connected(self, client, userdata, flags, rc):
		log.info(f"Connected to MQTT! Listening for topic changes on {self.mqtt_topic_game}")
		client.subscribe(self.mqtt_topic_game)

	def _on_disconnected(self, client, userdata, rc):
		log.info("Disconnected from MQTT!")

	def _on_message(self, client, topic, message:str):
		log.info(f"MQTT message: {message}")
		self.latest_message = message

	def _enqueue_send(self, value: str, seat: int|None = None):
		if value != None:
			self.queue.append((value, seat))

	def send_queue(self) -> bool:
		if len(self.queue) == 0:
			return False
		while self.queue:
			value, seat = self.queue.pop(0)
			self._send(value, seat)
		return True

	def _send(self, value: str, seat: int|None = None):
		if value == None:
			return
		log.info("send: %s", value)
		if not self.mqtt_client.is_connected():
			self.connect()
		gameStateVersion = self.view.state.game_state_version
		action_map = {"gameStateVersion": gameStateVersion, "action": value}
		if seat != None:
			action_map["seat"] = seat
		action = json.dumps(action_map)
		log.debug('MQTT Publish to %s value %s', self.mqtt_topic_command, action)
		self.mqtt_client.publish(self.mqtt_topic_command, action)

		new_game_state = self.predict_next_game_state(value)
		if new_game_state:
			self.view.set_state(new_game_state)

	def poll_for_new_messages(self):
		if not self.mqtt_client.is_connected():
			self.connect()
		start_ts = time.monotonic()
		self.mqtt_client.loop(1)
		self.view.record_polling_delay(time.monotonic() - start_ts)

	def handle_new_messages(self) -> None:
		if self.latest_message != None:
			game_state = GameState(json_state_string=self.latest_message, timestamp_offset=self.unix_time_offset)
			self.latest_message = None
			self.view.set_state(game_state)

	def _lookup_unix_time_offset(self):
		if self.unix_time_offset != 0:
			log.debug(f'Unix time already set to {self.unix_time_offset:,}')
			return
		log.info(' ============================= LOOK UP UNIX TIME ==========================================')
		self.view.set_connection_progress_text('Getting current time')
		requests = Session(pool, ssl_context)
		response = requests.get('http://worldtimeapi.org/api/timezone/Etc/UTC')
		now = round(time.monotonic())
		json = response.json()
		time_unix_sec = json['unixtime']
		diff = now - time_unix_sec
		log.info(f"Current Unix Time: {time_unix_sec} at mono {now} (diff: {diff})")
		self.unix_time_offset = diff + self.manual_time_offset

	def enqueue_send_primary(self, seat: int|None = None, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_send(super().enqueue_send_primary(seat, on_success, on_failure), seat=seat)
	def enqueue_send_secondary(self, seat: int|None = None, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_send(super().enqueue_send_secondary(seat, on_success, on_failure), seat=seat)
	def enqueue_send_toggle_admin(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_send(super().enqueue_send_toggle_admin(on_success, on_failure))
	def enqueue_send_admin_on(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_send(super().enqueue_send_admin_on(on_success, on_failure))
	def enqueue_send_admin_off(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_send(super().enqueue_send_admin_off(on_success, on_failure))
	def enqueue_send_toggle_pause(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_send(super().enqueue_send_toggle_pause(on_success, on_failure))
	def enqueue_send_pause_on(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_send(super().enqueue_send_pause_on(on_success, on_failure))
	def enqueue_send_pause_off(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_send(super().enqueue_send_pause_off(on_success, on_failure))
	def enqueue_send_undo(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_send(super().enqueue_send_undo(on_success, on_failure))
