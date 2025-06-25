from core.utils.settings import get_float
TIME_ON = get_float('TIME_REMINDER_ON_DURATION', 1.0)
TIME_OFF = get_float('TIME_REMINDER_OFF_DURATION', 0.5)

from adafruit_logging import getLogger
log = getLogger()
from time import monotonic

from core.view.view import View

class ViewTimeReminderOnOff(View):
	def __init__(self, on_fn, off_fn):
		super().__init__()
		self.on_fn = on_fn
		self.off_fn = off_fn
		self.time_reminder_count = 0
		self.time_reminder_ts = None
		self.current_status = False

	def on_time_reminder(self, time_reminder_count: int):
		self.time_reminder_count = time_reminder_count
		self.time_reminder_ts = monotonic() if time_reminder_count > 0 else None
		self.off_fn()

	def animate(self) -> bool:
		shared_stuff_busy = super().animate()
		if self.time_reminder_ts == None:
			return
		completed_cycles, time_into_cycle = divmod(monotonic() - self.time_reminder_ts, TIME_ON+TIME_OFF)
		if completed_cycles >= self.time_reminder_count:
			self.time_reminder_ts = None
			self.off_fn()
		elif time_into_cycle < TIME_ON and not self.current_status:
			self.on_fn()
			self.current_status = True
		elif time_into_cycle >= TIME_ON and self.current_status:
			self.off_fn()
			self.current_status = False
		return shared_stuff_busy