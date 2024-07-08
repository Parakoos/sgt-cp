from time import monotonic
from easing import EasingBase
from utils.color import mix

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
	def __init__(self, from_color: tuple[int,int,int], to_color: tuple[int,int,int], easing: EasingBase, callback: callable[[tuple[int,int,int], any|None], None], callback_data: any = None) -> None:
		self.start_time = None
		self.easing = easing
		self.callback = callback
		self.callback_data = callback_data
		self.from_color = from_color
		self.to_color = to_color

	def loop(self):
		if self.start_time == None:
			self.start_time = monotonic()
		elapsed_time = min(self.easing.duration, monotonic() - self.start_time)
		progress = self.easing.ease(elapsed_time)
		mixed_color = mix(self.from_color, self.to_color, progress)
		if self.callback_data != None:
			self.callback(mixed_color, self.callback_data)
		else:
			self.callback(mixed_color)
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
