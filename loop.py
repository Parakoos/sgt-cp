import adafruit_logging as logging
log = logging.getLogger()
from utils.log import log_memory_usage, log_exception
from sgt_connection import SgtConnection
from view import View
from buttons import Buttons
from microcontroller import Pin
import time

def main_loop(
		connection: SgtConnection,
		view: View,
		on_connect: callable[[None], None] = None,
		on_error: callable[[Exception], None] = None,
		loops: tuple[callable[[None], bool]] = (),
		):
	mem_ts = time.monotonic()
	is_polling = None
	while True:
		try:
			log_memory_usage('Start of Loop')
			if not connection.is_connected():
				connection.connect()
			while not connection.is_connected():
				view.animate()
			view.switch_to_no_game()
			if on_connect:
				on_connect()
			while connection.is_connected():
				busy = view.animate()
				for loop in loops:
					busy = busy or loop() # Each loop (and view.animate) should return True if it should block polling
				messages_sent = connection.send_queue()
				if busy and is_polling:
					log.debug('======== DISABLE POLLING ========')
					is_polling = False
				elif not busy and not is_polling:
					log.debug('======== ENABLE POLLING ========')
					is_polling = True
				elif messages_sent and not is_polling:
					log.debug('======== POLLING BECAUSE OF MESSAGE SENT ========')
					is_polling = True
				if is_polling:
					connection.poll_for_new_messages()
				connection.handle_new_messages()
				if time.monotonic() - mem_ts > 10:
					log_memory_usage('End of Loop')
					mem_ts = time.monotonic()
			log.debug('-------------------- DISCONNECTED --------------------')
		except Exception as e:
			log_exception(e)
			view.show_error(e)
			view.switch_to_error()
			try:
				if on_error:
					on_error(e)
			except Exception as on_error_exception:
				log.error('Second inner exception! Immediate restart.')
				log_exception(on_error_exception)
			log.debug('-------------------- RESTART --------------------')
			try:
				connection.restart()
			except Exception as on_restart_exception:
				log.error('Second inner exception! Immediate restart.')
				log_exception(on_restart_exception)

class ErrorHandlerResumeOnButtonPress:
	def __init__(self, view: View, buttons: Buttons) -> None:
		self.view = view
		self.buttons = buttons
		self.in_error = False

	def clear_error_on_button_press(self, btn_pin: Pin, presses: int, long_press: bool):
		self.in_error = False

	def on_error(self, exception: Exception):
		self.in_error = True
		self.buttons.clear_callbacks()
		self.buttons.set_fallback(self.clear_error_on_button_press)

		log.info('Animating error view until any button pressed')
		while self.in_error:
			self.view.animate()
			self.buttons.loop()
		self.buttons.clear_callbacks()
		log.info('On error handler completed due to button press')

class ErrorHandlerNoResume:
	def __init__(self, view: View) -> None:
		self.view = view

	def on_error(self, exception: Exception):
		log.info('Animating error until end of time')
		try:
			while True:
				self.view.animate()
		except Exception:
			while True:
				pass