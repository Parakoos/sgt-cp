import adafruit_logging as logging
log = logging.getLogger()
from microcontroller import Pin
from gc import collect
from time import monotonic

import core.reorder as reorder
from core.utils.settings import get_float
from core.utils.log import log_memory_usage, log_exception
from core.connection.sgt_connection import SgtConnection
from core.view.view import View
from core.buttons import Buttons

# The speed of the animation, in Pixels/Seconds
REORDER_COMMAND_DELAY = get_float('TABLE_REORDER_COMMAND_DELAY', 2.0)

def main_loop(
		connection: SgtConnection,
		view: View,
		on_connect: callable[[None], None] = None,
		on_error: callable[[Exception], None] = None,
		loops: tuple[callable[[None], bool]] = (),
		):
	while True:
		try:
			log_memory_usage('Start of Loop')
			if not connection.is_connected():
				connection.connect()
			while not connection.is_connected():
				view.animate()
				collect()
			view.switch_to_no_game()
			if on_connect:
				on_connect()
			collect()
			while connection.is_connected():
				view.animate()
				collect()
				for loop in loops:
					loop()
				# Check if reordering is done
				if reorder.singleton is not None and not reorder.singleton.is_done:
					have_complete_seat_order = view.state is not None and len(reorder.singleton.new_seat_order) == len(view.state.players)
					have_stayed_constant_long_enough = monotonic() - reorder.singleton.ts_last_change >= REORDER_COMMAND_DELAY
					if have_complete_seat_order and have_stayed_constant_long_enough:
						connection.enqueue_send_new_turn_order(reorder.singleton.new_seat_order)
						reorder.singleton.is_done = True
				connection.send_command()
				connection.poll_for_new_messages()
				if connection.handle_new_messages():
					log_memory_usage('After Game State Update')
				else:
					collect()
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
		import supervisor
		if presses == 1 and not long_press:
			self.in_error = False
		elif presses == 2 and not long_press:
			supervisor.reload()
		elif presses == 1 and long_press and not supervisor.runtime.usb_connected:
			import microcontroller
			microcontroller.reset()

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