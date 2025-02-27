from time import monotonic
import adafruit_logging as logging
log = logging.getLogger()

class Reorder():
	def __init__(self, initiating_seat: int):
		self.is_done = False
		self.new_seat_order = [initiating_seat]
		self.ts_last_change = monotonic()

	def handle_activated_seats(self, seats: set[int]):
		if self.is_done:
			return
		old_seat_set = set(self.new_seat_order)
		removed_seats = old_seat_set - seats
		added_seats = seats - old_seat_set
		for removed_seat in removed_seats:
			self.new_seat_order.remove(removed_seat)
		for added_seat in added_seats:
			self.new_seat_order.append(added_seat)
		log.debug(f"Reorder: Removed={removed_seats}, Added: {added_seats}, New Order: {self.new_seat_order} @ {self.ts_last_change}")
		self.ts_last_change = monotonic()