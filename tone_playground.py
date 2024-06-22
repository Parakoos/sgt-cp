from tone import Tone
from adafruit_circuitplayground import cp

class TonePlayground(Tone):
    def __init__(self) -> None:
        super().__init__()

    def play_tone(self, freq: int, duration: float):
        cp.play_tone(freq, duration)