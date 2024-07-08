import adafruit_logging as logging
log = logging.getLogger()
from time import monotonic
from utils.find import find_string

AXIS_X = 0
AXIS_Y = 1
AXIS_Z = 2

DIR_POS = 1
DIR_NEG = -1

ON_ACTIVATE = True
ON_DEACTIVATE = False

class Orientation:
	def __init__(self, accelerometer, change_delay, on_threshold, off_threshold):
		self.accelerometer = accelerometer
		self.orientation = None		# tuple(axis, dir)
		self.orientation_tmp = None	# What is the latest detected orientation and when? (tuple[orientation, ts])
		self.on_threshold = on_threshold
		self.off_threshold = off_threshold
		self.change_delay = change_delay
		self.callbacks = {}

	def set_callback(self, axis: int, direction: int, to_cb: callable[[None], None] = None, from_cb: callable[[None], None] = None):
		self.callbacks[(axis, direction)] = (to_cb, from_cb)

	def loop(self):
		acceleration = self.accelerometer.get_acceleration()
		current_orientation = find_string((orientation for orientation in self.callbacks.keys() if acceleration[orientation[0]]*orientation[1] >= self.on_threshold))
		if current_orientation == self.orientation:
			# Make sure we don't change the orientation by clearing out the tmp
			self.orientation_tmp = None
		elif current_orientation != None and self.orientation_tmp == None:
			# We have a brand new orientation. Set the tmp to it, with timestamp.
			self.orientation_tmp = (current_orientation, monotonic())
		elif current_orientation != None and self.orientation_tmp[0] != current_orientation:
			# We have an orientation different from the current tmp one. Update it with a new ts.
			self.orientation_tmp = (current_orientation, monotonic())
		elif current_orientation == None and self.orientation != None:
			# Check if we have drifted far enough from the active orientation to switch it off
			if acceleration[self.orientation[0]]*self.orientation[1] < self.off_threshold:
				self.orientation_tmp = (None, monotonic())

		if self.orientation_tmp != None and monotonic() - self.orientation_tmp[1] > self.change_delay:
			if self.orientation != None and self.callbacks[self.orientation] != None:
				# Call the 'Leave Orientation' callback
				self.callbacks[self.orientation]()

			if self.orientation_tmp[0] != None:
				# Call the 'Enter Orientation' callback
				self.callbacks[self.orientation_tmp[0]]()

			self.orientation = self.orientation_tmp[0]
