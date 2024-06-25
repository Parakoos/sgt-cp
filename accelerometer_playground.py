from accelerometer import Accelerometer
from adafruit_circuitplayground import cp
import time

class Accelerometer_Playground(Accelerometer):
    def __init__(self, shake_threshold = 20, double_shake_prevention_timeout = 3) -> None:
        super().__init__()
        self.shake_threshold = shake_threshold
        self.double_shake_prevention_timeout = double_shake_prevention_timeout
        self.shake_callback = None
        self.last_shake_ts = -1000

    def loop(self):
        if (
            self.set_shake_callback != None
            and time.monotonic() - self.last_shake_ts > self.double_shake_prevention_timeout
            and cp.shake(shake_threshold=self.shake_threshold)
        ):
            self.set_shake_callback()

    def get_acceleration(self) -> tuple[float, float, float]:
        return cp.acceleration

    def set_shake_callback(self, callback):
        self.shake_callback = callback