import adafruit_logging as logging
log = logging.getLogger()
from time import monotonic
from settings import ORIENTATION_ON_THRESHOLD, ORIENTATION_OFF_THRESHOLD

class Orientation:
    def __init__(self, accelerometer):
        self.accelerometer = accelerometer
        self.orientation = None          # Up, Down, Front, Back, Left or Right (string)
        self.last_loop_ts = monotonic()
        self.rotation_start_vals = None
        # self.orientation_tmp = None      # What is the latest detected orientation
        # self.orientation_tmp_ts = 0      # When did we set the self.orientation_tmp value.
        self.callbacks = {}

    def set_callback(self, orientation, to_callback=None, from_callback=None):
        self.callbacks[orientation] = (to_callback, from_callback)

    def loop(self, force=False):
        if (not force) and (monotonic() - self.last_loop_ts) < 2:
            # log.info("skip orient loop: %s - %s", force, (monotonic() - self.last_loop_ts))
            return

        acceleration = self.accelerometer.get_acceleration()
        x_orient = self.check_orientation_axis(acceleration[0], "x+", "x-")
        y_orient = self.check_orientation_axis(acceleration[1], "y+", "y-")
        z_orient = self.check_orientation_axis(acceleration[2], "z+", "z-")
        new_orient = x_orient or y_orient or z_orient

        if self.orientation != None and self.orientation != new_orient and self.orientation in self.callbacks and self.callbacks[self.orientation][1]:
            # Leave current orientation
            self.callbacks[self.orientation][1](self.orientation)

        if new_orient != None and self.orientation != new_orient and new_orient in self.callbacks and self.callbacks[new_orient][0]:
            # Enter new orientation
            self.callbacks[new_orient][0](new_orient)
            self.orientation = new_orient

        self.last_loop_ts = monotonic()
        self.orientation = new_orient

    def check_orientation_axis(self, value, pos_orientation, neg_orientation):
        if value > ORIENTATION_ON_THRESHOLD:
            return pos_orientation
        elif -value > ORIENTATION_ON_THRESHOLD:
            return neg_orientation
        else:
            return None