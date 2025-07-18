from core.utils.settings import get_int, get_float, get_string
# The connection details of your home WIFI.
WIFI_SSID = get_string('CIRCUITPY_WIFI_SSID')
WIFI_PASSWORD = get_string('CIRCUITPY_WIFI_PASSWORD')

# Get the following values from https://sharedgametimer.com/mqtt
SGT_USER_ID = get_string('MQTT_SGT_USER_ID') # The bit before '/command' and '/game' topics.
MQTT_HOST = get_string('MQTT_HOST')
MQTT_PORT = get_int('MQTT_PORT')
MQTT_USERNAME = get_string('MQTT_USERNAME')
MQTT_PASSWORD = get_string('MQTT_PASSWORD')
MQTT_SOCKET_TIMEOUT = get_float('MQTT_SOCKET_TIMEOUT', 0)

# Optional time offset in seconds to improve syncing between SGT and the MCU
MQTT_MANUAL_TIME_OFFSET = get_int('MQTT_MANUAL_TIME_OFFSET', 0)

import adafruit_logging as logging
log = logging.getLogger()
import ssl
import socketpool
import wifi
from adafruit_minimqtt.adafruit_minimqtt import MQTT as ADA_MQTT
from adafruit_requests import Session
import time
import json

from core.view.view import View
from core.connection.sgt_connection import SgtConnection
from core.game_state import GameState

class SgtConnectionMQTT(SgtConnection):
	command_to_send: list[tuple[str, int|None, list[int]|None]]
	def __init__(self, view: View):
		super().__init__(view)
		self.mqtt_topic_game = f"{SGT_USER_ID}/game"
		self.mqtt_topic_command = f"{SGT_USER_ID}/commands"
		self.last_poll_ts = -1000
		self.unix_time_offset = 0
		wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD)
		pool = socketpool.SocketPool(wifi.radio)
		ssl_context = ssl.create_default_context()
		self.session = Session(pool, ssl_context)
		self.mqtt_client = ADA_MQTT(
			broker=MQTT_HOST,
			port=MQTT_PORT,
			username=MQTT_USERNAME,
			password=MQTT_PASSWORD,
			socket_pool=pool,
			ssl_context=ssl_context,
			is_ssl=True,
			socket_timeout=MQTT_SOCKET_TIMEOUT,
		)
		self.mqtt_client.on_connect = self._on_connected
		self.mqtt_client.on_disconnect = self._on_disconnected
		self.mqtt_client.on_message = self._on_message
		self.mqtt_client.on_subscribe = self._on_subscribe
		self.mqtt_client.enable_logger(logging, log_level=20, logger_name="mqtt")
		self.command_to_send = []
		self.latest_message = None

	def is_connected(self):
		return self.mqtt_client.is_connected()

	def restart(self):
		if self.mqtt_client.is_connected():
			self.mqtt_client.disconnect()

	def connect(self) -> bool:
		self.view.switch_to_not_connected()
		self._lookup_unix_time_offset()
		self.view.set_connection_progress_text(f"Connecting to MQTT")
		self.mqtt_client.connect()

	def _on_connected(self, client, userdata, flags, rc):
		log.info(f"MQTT: Connected")
		client.subscribe(self.mqtt_topic_game)

	def _on_disconnected(self, client, userdata, rc):
		log.info("MQTT: Disconnected")

	def _on_subscribe(self, client, userdata, topic, rc):
		log.info(f"MQTT: Subscribed to topic {topic}")

	def _on_message(self, client, topic, message:str):
		log.info(f"MQTT message: {message}")
		self.latest_message = message

	def _enqueue_command(self, value: str, seat: int|None = None, seats: list[int]|None = None):
		if value != None:
			self.command_to_send.append((value, seat, seats))

	def send_command(self) -> bool:
		if len(self.command_to_send) == 0 or (self.view.state != None and self.view.state.ts_command_sent_based_on_this != None and self.view.state.game_state_version != None):
			return False
		else:
			log.info(f"MQTT command queue length: ${len(self.command_to_send)}")
			self._send(*self.command_to_send.pop(0))
			return True

	def _send(self, value: str, seat: int|None = None, seats: list[int]|None = None):
		if value == None:
			return
		log.info("send: %s", value)
		if not self.mqtt_client.is_connected():
			self.connect()
		gameStateVersion = self.view.state.game_state_version
		action_map = {"gameStateVersion": gameStateVersion, "action": value}
		if (value == 'StartGame'):
			if seat != None:
				action_map["firstPlayerSeat"] = seat
			elif seats != None:
				action_map["playerOrderAsSeats"] = seats
		elif seat != None:
			action_map["seat"] = seat
		elif seats != None:
			action_map["seats"] = seats
		action = json.dumps(action_map)
		log.debug('MQTT Publish to %s value %s', self.mqtt_topic_command, action)
		self.mqtt_client.publish(self.mqtt_topic_command, action)
		self.view.state.ts_command_sent_based_on_this = time.monotonic()

	def poll_for_new_messages(self):
		if not self.mqtt_client.is_connected():
			self.connect()
		start_ts = time.monotonic()
		self.mqtt_client.loop(MQTT_SOCKET_TIMEOUT)
		self.view.record_polling_delay(time.monotonic() - start_ts)
		if self.view.state != None and self.view.state.ts_command_sent_based_on_this != None:
			if time.monotonic() - self.view.state.ts_command_sent_based_on_this > 3:
				self.view.state.ts_command_sent_based_on_this = None

	def handle_new_messages(self) -> None:
		if self.latest_message == None:
			return False
		game_state = None if len(self.latest_message.strip()) == 0 else GameState(json_state_string=self.latest_message, timestamp_offset=self.unix_time_offset)
		self.latest_message = None
		self.view.set_state(game_state)
		return True

	def _lookup_unix_time_offset(self):
		if self.unix_time_offset != 0:
			log.debug(f'Unix time already set to {self.unix_time_offset:,}')
			return
		log.info(' ============================= LOOK UP UNIX TIME ==========================================')
		self.view.set_connection_progress_text('Getting current time')
		unix_time_url = "https://parakoos.com/time.php"
		with self.session.get(unix_time_url) as response:
			now = round(time.monotonic())
			json = response.json()
			time_unix_sec = json['unixtime']
			diff = now - time_unix_sec
			log.info(f"Current Unix Time: {time_unix_sec} at mono {now} (diff: {diff})")
			self.unix_time_offset = diff + MQTT_MANUAL_TIME_OFFSET

	def enqueue_send_primary(self, seat: int|None = None, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_command(super().enqueue_send_primary(seat, on_success, on_failure), seat=seat)
	def enqueue_send_secondary(self, seat: int|None = None, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_command(super().enqueue_send_secondary(seat, on_success, on_failure), seat=seat)
	def enqueue_send_toggle_admin(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_command(super().enqueue_send_toggle_admin(on_success, on_failure))
	def enqueue_send_admin_on(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_command(super().enqueue_send_admin_on(on_success, on_failure))
	def enqueue_send_admin_off(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_command(super().enqueue_send_admin_off(on_success, on_failure))
	def enqueue_send_toggle_pause(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_command(super().enqueue_send_toggle_pause(on_success, on_failure))
	def enqueue_send_pause_on(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_command(super().enqueue_send_pause_on(on_success, on_failure))
	def enqueue_send_pause_off(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_command(super().enqueue_send_pause_off(on_success, on_failure))
	def enqueue_send_undo(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_command(super().enqueue_send_undo(on_success, on_failure))
	def enqueue_send_start_game(self, seat: int|None = None, seats: list[int]|None = None, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_command(super().enqueue_send_start_game(seat, seats, on_success, on_failure), seat=seat, seats=seats)
	def enqueue_send_start_sim_turn(self, seats: set[int]):
		command = super().enqueue_send_start_sim_turn(seats)
		if command != None:
			self._enqueue_command(command, seats=list(seats))
			return True
		else:
			return False
	def enqueue_send_new_turn_order(self, turn_order_seats: list[int]):
		command = super().enqueue_send_new_turn_order(turn_order_seats)
		if command != None:
			self._enqueue_command(command, seats=turn_order_seats)
			return True
		else:
			return False
	def enqueue_send_join_game_or_cycle_colors(self, seat: int, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_command(super().enqueue_send_join_game_or_cycle_colors(seat, on_success, on_failure), seat=seat)
	def enqueue_send_leave_game(self, seat: int, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		self._enqueue_command(super().enqueue_send_leave_game(seat, on_success, on_failure), seat=seat)