import adafruit_logging as logging
log = logging.getLogger()
from time import monotonic
from easing import EasingBase
from utils.color import DisplayedColor
import adafruit_fancyled.adafruit_fancyled as fancy

class TransitionFunction():
	def __init__(self, easing: EasingBase, callback: callable[[float, any], None], callback_data: any = None) -> None:
		self.start_time = None
		self.easing = easing
		self.callback = callback
		self.callback_data = callback_data
		pass

	def loop(self):
		"""
		:returns: true if the transition has completed.
		"""
		if self.start_time == None:
			self.start_time = monotonic()
		elapsed_time = min(self.easing.duration, monotonic() - self.start_time)
		progress = self.easing.ease(elapsed_time)
		if self.callback_data != None:
			self.callback(progress, self.callback_data)
		else:
			self.callback(progress)
		return self.easing.duration == elapsed_time

class ColorTransitionFunction():
	def __init__(self, from_color: DisplayedColor, to_color: DisplayedColor, easing: EasingBase) -> None:
		self.start_time = None
		self.easing = easing
		self.starting_fancy = from_color.fancy_color
		self.starting_brightness = from_color.brightness
		self.target_fancy = to_color.fancy_color
		self.target_brightness = to_color.brightness
		self.color_to_update = from_color

	def loop(self):
		if self.start_time == None:
			self.start_time = monotonic()
		elapsed_time = min(self.easing.duration, monotonic() - self.start_time)
		progress = self.easing.ease(elapsed_time)
		new_fancy = fancy.mix(self.starting_fancy, self.target_fancy, progress) if self.starting_fancy != self.target_fancy else self.starting_fancy
		new_brightness = round(self.starting_brightness * (1-progress) + self.target_brightness * progress, 2)
		self.color_to_update.update(new_fancy, new_brightness)
		return self.easing.duration == elapsed_time

class ParallellTransitionFunctions():
	def __init__(self, *fns: TransitionFunction) -> None:
		self.fns = fns

	def loop(self):
		is_done = True
		for fn in self.fns:
			is_done = fn.loop() and is_done
		return is_done

class SerialTransitionFunctions():
	def __init__(self, fns: list[TransitionFunction]) -> None:
		self.fns = fns

	def loop(self):
		if len(self.fns) > 0 and self.fns[0].loop():
			self.fns = self.fns[1:]
		return len(self.fns) == 0

	def append(self, fn: TransitionFunction):
		self.fns.append(fn)
