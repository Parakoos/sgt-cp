import time
import array
import math
import board
import digitalio

try:
	from audiocore import RawSample
except ImportError:
	from audioio import RawSample

try:
	from audioio import AudioOut
except ImportError:
	try:
		from audiopwmio import PWMAudioOut as AudioOut
	except ImportError:
		pass  # not always supported by every board!

TONE_FREQ = [ 262,# C4
			294,  # D4
			330,  # E4
			349,  # F4
			392,  # G4
			440,  # A4
			494 ] # B4

def tone(frequency, duration):
	# FREQUENCY = 440  # 440 Hz middle 'A'
	SAMPLERATE = 8000  # 8000 samples/second, recommended!

	# Generate one period of sine wav.
	length = SAMPLERATE // frequency
	sine_wave = array.array("H", [0] * length)
	for i in range(length):
		sine_wave[i] = int(math.sin(math.pi * 2 * i / length) * (2 ** 15) + 2 ** 15)

	# Enable the speaker
	speaker_enable = digitalio.DigitalInOut(board.SPEAKER_ENABLE)
	speaker_enable.direction = digitalio.Direction.OUTPUT
	speaker_enable.value = True

	audio = AudioOut(board.SPEAKER)
	sine_wave_sample = RawSample(sine_wave)

	# A single sine wave sample is hundredths of a second long. If you set loop=False, it will play
	# a single instance of the sample (a quick burst of sound) and then silence for the rest of the
	# duration of the time.sleep(). If loop=True, it will play the single instance of the sample
	# continuously for the duration of the time.sleep().
	audio.play(sine_wave_sample, loop=True)  # Play the single sine_wave sample continuously...
	time.sleep(duration)  # for the duration of the sleep (in seconds)
	audio.stop()  # and then stop.

def beep_success():
	tone(TONE_FREQ[3], duration=0.1)

def beep_shake():
	tone(TONE_FREQ[5], duration=0.1)
	tone(TONE_FREQ[2], duration=0.1)
	tone(TONE_FREQ[5], duration=0.1)
	tone(TONE_FREQ[2], duration=0.1)

def beep_error():
	tone(TONE_FREQ[0], duration=0.1)
	tone(TONE_FREQ[6], duration=0.2)

def cascade():
	for i in range(len(TONE_FREQ)):
		tone(TONE_FREQ[i], duration=0.1)
