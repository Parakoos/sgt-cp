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

class NoOpTransition():
	def __init__(self, duration: float) -> None:
		self.start_time = None
		self.duration = duration

	def loop(self):
		if self.start_time == None:
			self.start_time = monotonic()
		elapsed_time = monotonic() - self.start_time
		return elapsed_time > self.duration

class PropertyTransition():
	easing: EasingBase
	def __init__(self, object: any, property: str, target_value: float, easing: EasingBase, duration: float) -> None:
		self.start_time = None
		self.object = object
		self.property = property
		self.easing = easing
		self.target_value = target_value
		self.duration = duration

	def loop(self):
		if self.start_time == None:
			self.start_time = monotonic()
			self.easing = self.easing(start=getattr(self.object, self.property), end=self.target_value, duration=self.duration)
		elapsed_time = min(self.easing.duration, monotonic() - self.start_time)
		setattr(self.object, self.property, self.easing.ease(elapsed_time))
		return self.duration == elapsed_time

class ColorTransitionFunction():
	def __init__(self, from_color: DisplayedColor, to_color: DisplayedColor, easing: EasingBase) -> None:
		self.start_time = None
		self.easing = easing
		self.target_color = to_color
		self.color_to_update = from_color

	def loop(self):
		if self.start_time == None:
			self.start_time = monotonic()
			if self.color_to_update.is_black():
				self.starting_fancy = self.target_color.fancy_color
				self.starting_brightness = 0.0
			else:
				self.starting_fancy = self.color_to_update.fancy_color
				self.starting_brightness = self.color_to_update.brightness

			if self.target_color.is_black():
				self.target_fancy = self.color_to_update.fancy_color
				self.target_brightness = 0.0
			else:
				self.target_fancy = self.target_color.fancy_color
				self.target_brightness = self.target_color.brightness
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
