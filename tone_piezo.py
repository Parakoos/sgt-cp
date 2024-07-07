from simpleio import tone
from tone import Tone
from microcontroller import Pin

class TonePiezo(Tone):
	def __init__(self, pin: Pin) -> None:
		super().__init__()
		self.pin = pin

	def play_tone(self, freq: int, duration: float):
		tone(self.pin, freq, duration)
