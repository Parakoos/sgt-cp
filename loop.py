import adafruit_logging as logging
log = logging.getLogger()
from utils import log_memory_usage, log_exception
from sgt_connection import SgtConnection
from view import View
import time

def main_loop(connection: SgtConnection, view: View, loops: tuple[callable[[None], bool]]):
	mem_ts = time.monotonic()
	is_polling = None
	while True:
		try:
			log_memory_usage('Start of Loop')
			if not connection.is_connected():
				connection.connect()
			while not connection.is_connected():
				view.animate()
			while connection.is_connected():
				busy = view.animate()
				for loop in loops:
					busy = busy or loop() # Each loop (and view.animate) should return True if it should block polling
				if busy and is_polling:
					log.debug('======== DISABLE POLLING ========')
					is_polling = False
				elif not busy and not is_polling:
					log.debug('======== ENABLE POLLING ========')
					is_polling = True
				if is_polling:
					connection.poll()
				if time.monotonic() - mem_ts > 10:
					log_memory_usage('End of Loop')
					mem_ts = time.monotonic()
			log.debug('-------------------- DISCONNECTED --------------------')
		except Exception as e:
			log_exception(e)
			view.show_error(e)
			view.switch_to_error()
			timeout = time.monotonic() + 3
			try:
				while view.animate() and time.monotonic() < timeout:
					view.animate()
			except Exception:
				while time.monotonic() < timeout:
					pass
			log.debug('-------------------- RESTART --------------------')