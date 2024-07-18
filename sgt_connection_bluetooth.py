import adafruit_logging as logging
log = logging.getLogger()
import time
from view import View
from sgt_connection import SgtConnection
from game_state import GameState
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
import json
from traceback import print_exception

class SgtConnectionBluetooth(SgtConnection):
	def __init__(self,
				view: View,
				device_name: str,
				field_order: list[str],
				field_divider: str,
				):
		super().__init__(view)
		self.ble = BLERadio()
		self.uart = UARTService()
		self.advertisement = ProvideServicesAdvertisement(self.uart)
		self.ble.name = device_name
		self.incomplete_line_read = None
		self.last_is_connected_check = False
		self.all_read_text = ''
		self.text_read = ''
		self.last_line_executed = None
		self.byte_array = bytearray(20)
		self.command_to_send = None
		self.line_to_process = None
		self.field_order = field_order
		self.field_divider = field_divider
		self.suggestions = json.dumps({
			"script": [
				f'0 %0A{field_divider.join(field_order)}%0A'
			],
				"scriptName": device_name + " Write",
				"defaultTriggers": ["includePlayers","includePause","includeAdmin","includeSimultaneousTurns","includeGameStart","includeGameEnd","includeSandTimerStart","includeSandTimerReset","includeSandTimerStop","includeSandTimerOutOfTime","runOnStateChange","runOnPlayerOrderChange", "runOnPoll"],
				"actionMap": [
					('Enable ACK', 'remoteActionEnableAcknowledge'),
					('ACK', 'remoteActionAcknowledge'),
					('Poll', 'remoteActionPoll'),
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
			})
	def is_connected(self) -> bool:
		if self.ble.connected and not self.last_is_connected_check:
			self.view.set_connection_progress_text('Establishing Connection')
			self.ble.stop_advertising()
			# Wait for the first poll request to go through,
			time_of_last_poll_request = 0
			while self.ble.connected and self.uart.in_waiting == 0:
				if time.monotonic() - time_of_last_poll_request > 0.5:
					time_of_last_poll_request = time.monotonic()
					log.debug('Waiting for ping')
					self._send('Ping')
				self.view.animate()
			if self.ble.connected:
				log.debug('Ping Acknowledged')
				self._send('Enable ACK')
				self.uart.reset_input_buffer()
				self._send('Poll')
			else:
				raise Exception('Disconnected while waiting for ping')

		self.last_is_connected_check = self.ble.connected
		return self.ble.connected

	def connect(self):
		self.view.set_connection_progress_text(f"Advertising BLE as {self.ble.name}")
		self.ble.start_advertising(self.advertisement)

	def poll_for_new_messages(self) -> None:
		if self.uart.in_waiting == 0:
			if self.incomplete_line_read and time.monotonic() - self.incomplete_line_read[0] > 6:
				log.debug('Old incomplete line. Clear the buffer and line, then call poll for new data. %s', self.incomplete_line_read)
				self.uart.reset_input_buffer()
				self.incomplete_line_read = None
				self._poll_for_latest_state()
			return

		while self.uart.in_waiting > 0:
			bytes_read = self.uart.readinto(buf=self.byte_array, nbytes=self.uart.in_waiting)
			read_text = str(self.byte_array[:bytes_read], 'utf-8')
			# log.debug('ACK of line %s', read_text)
			self._send('ACK')
			self.all_read_text += read_text
			lines = [(time.monotonic(), line) for line in read_text.split("\n")]
			if self.incomplete_line_read != None:
				lines[0] = (self.incomplete_line_read[0], self.incomplete_line_read[1]+lines[0][1])
				self.incomplete_line_read = None

			if len(lines) == 0:
				return
			last_item = lines.pop()
			lines = [line for line in lines if line[1] != '']
			if len(lines[:-1]) > 0:
				print(f'SKIP: {lines[:-1]}')

			# log.debug("Last Item: %s, lines: %s", last_item, lines)
			if last_item[1] == '':
				if len(lines) > 0:
					do_this_line = lines.pop()
					if do_this_line[1] == 'GET SETUP':
						log.debug('SENDING SUGGESTED SETUP')
						self._send(self.suggestions)
						self.last_line_executed = do_this_line[1]
					elif (do_this_line[1] == self.last_line_executed):
						log.debug(f"SKIP DUPLICATE LINE: {self.last_line_executed}")
					else:
						log.debug(f"EXECUTE LINE: {do_this_line}")
						try:
							self.line_to_process = do_this_line
							self.last_line_executed = do_this_line[1]
						except Exception as e:
							print_exception(e)
							self._poll_for_latest_state()
			else:
				log.debug('incomplete line: "%s"', last_item[1])
				self.incomplete_line_read = last_item
				time.sleep(0.05)
	def handle_new_messages(self) -> None:
		if self.line_to_process == None:
			return False
		new_state = GameState(
			ble_state_string = self.line_to_process[1],
			ble_field_order = self.field_order,
			ble_field_divider = self.field_divider,
			timestamp_offset = self.line_to_process[0] - time.monotonic()
			)
		self.line_to_process = None
		self.view.set_state(new_state)
		return True
	def _send(self, value: str|None):
		if value == None:
			return
		log.info("-> %s", value)
		self.uart.write((value+"\n").encode("utf-8"))

		new_game_state = self.predict_next_game_state(value)
		if new_game_state:
			self.view.set_state(new_game_state)
			while self.view.animate():
				pass

	def _enqueue_command(self, value: str):
		if value != None:
			self.command_to_send = value

	def send_command(self) -> bool:
		if self.command_to_send == None:
			return False
		else:
			self._send(self.command_to_send)
			self.command_to_send = None
			return True

	def enqueue_send_primary(self, seat: int|None = None, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		action = super().enqueue_send_primary(seat, on_success, on_failure)
		if action != None and seat != None:
			self._enqueue_command(f'{action} #{seat}')
		else:
			self._enqueue_command(action)
	def enqueue_send_secondary(self, seat: int|None = None, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		action = super().enqueue_send_secondary(seat, on_success, on_failure)
		if action != None and seat != None:
			self._enqueue_command(f'{action} #{seat}')
		else:
			self._enqueue_command(action)
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
	def enqueue_send_start_game(self, seat: int|None = None, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
		action = super().enqueue_send_start_game(seat, on_success, on_failure)
		if action != None and seat != None:
			self._enqueue_command(f'{action} #{seat}')
		else:
			self._enqueue_command(action)

	def _poll_for_latest_state(self):
		log.debug('Polling for new data')
		self._send("Poll")