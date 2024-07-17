import adafruit_logging as logging
log = logging.getLogger()
from time import monotonic
from easing import EasingBase
from utils.color import DisplayedColor, BLACK
from ulab.numpy import trapz
import adafruit_fancyled.adafruit_fancyled as fancy

class TransitionFunction():
	def __init__(self, easing: EasingBase, loop: bool=False) -> None:
		self.start_time = None
		self.easing = easing
		self.value = None
		self.mode_loop = loop

	def loop(self):
		"""
		:returns: true if the transition has completed.
		"""
		if self.start_time == None:
			self.start_time = monotonic()
			self.on_start()

		if self.mode_loop:
			elapsed_time = (monotonic() - self.start_time) % self.easing.duration
			self.value = self.easing.ease(elapsed_time)
			return False
		else:
			elapsed_time = min(self.easing.duration, monotonic() - self.start_time)
			self.value = self.easing.ease(elapsed_time)
			return self.easing.duration == elapsed_time

	def on_start(self):
		pass

class CallbackTransitionFunction(TransitionFunction):
	def __init__(self, easing: EasingBase, callback: callable[[float, any], None], callback_data: any = None) -> None:
		super().__init__(easing)
		self.callback = callback
		self.callback_data = callback_data

	def loop(self):
		"""
		:returns: true if the transition has completed.
		"""
		done = super().loop()
		if self.callback_data != None:
			self.callback(self.value, self.callback_data)
		else:
			self.callback(self.value)
		return done

class NoOpTransition():
	def __init__(self, duration: float) -> None:
		self.start_time = None
		self.duration = duration

	def loop(self):
		if self.start_time == None:
			self.start_time = monotonic()
		elapsed_time = monotonic() - self.start_time
		return elapsed_time > self.duration

class PropertyTransition(TransitionFunction):
	def __init__(self, object: any, property: str, target_value: float, easing: EasingBase, duration: float) -> None:
		super().__init__(easing)
		self.object = object
		self.property = property
		self.target_value = target_value
		self.duration = duration

	def loop(self):
		if self.start_time == None:
			self.easing = self.easing(start=getattr(self.object, self.property), end=self.target_value, duration=self.duration)
		done = super().loop()
		setattr(self.object, self.property, self.value)
		return done

class ColorTransitionFunction(TransitionFunction):
	def __init__(self, from_color: DisplayedColor, to_color: DisplayedColor, easing: EasingBase) -> None:
		super().__init__(easing)
		self.start_time = None
		self.easing = easing
		self.target_color = to_color if to_color != None else BLACK.black
		self.color_to_update = from_color

	def loop(self):
		if self.target_color == self.color_to_update:
			return True
		if self.start_time == None:
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

			self.hsv_transition = isinstance(self.starting_fancy, fancy.CHSV) and isinstance(self.target_fancy, fancy.CHSV)
			if self.hsv_transition:
				self.starting_hue = self.starting_fancy.hue
				distance_if_adding = (self.target_fancy.hue-self.starting_hue) % 1
				distance_if_subtracting = (self.starting_hue-self.target_fancy.hue) % 1
				if (distance_if_adding <= distance_if_subtracting):
					self.target_hue = self.starting_hue + distance_if_adding
				else:
					self.target_hue = self.starting_hue - distance_if_subtracting
		done = super().loop()
		progress = self.value
		if self.hsv_transition:
			anti_progress = (1-progress)
			h = (progress * self.target_hue + anti_progress * self.starting_hue) % 1
			s = progress * self.target_fancy.saturation + anti_progress * self.starting_fancy.saturation
			v = progress * self.target_fancy.value + anti_progress * self.starting_fancy.value
			new_fancy = fancy.CHSV(h,s,v)
		else:
			new_fancy = fancy.mix(self.starting_fancy, self.target_fancy, progress) if self.starting_fancy != self.target_fancy else self.starting_fancy
		new_brightness = round(self.starting_brightness * (1-progress) + self.target_brightness * progress, 2)
		self.color_to_update.update(new_fancy, new_brightness)
		return done

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

class RampUpDownTransitionFunction():
	ramp_up_ease: EasingBase
	ramp_down_ease: EasingBase
	def __init__(self, target_velocity: float, start_position: float, end_position: float, ease_in: EasingBase, ease_in_duration: float, ease_out: EasingBase, ease_out_duration: float) -> None:
		self.ramp_up_ease = ease_in(0, target_velocity, ease_in_duration)
		self.ramp_down_ease = ease_out(target_velocity, 0, ease_out_duration)
		ramp_up_distance = trapz([self.ramp_up_ease(x/100)*ease_in_duration for x in range(0, 101)], dx=0.01)
		ramp_down_distance = trapz([self.ramp_down_ease(x/100)*ease_out_duration for x in range(0, 101)], dx=0.01)
		mid_distance = end_position - start_position - ramp_up_distance - ramp_down_distance
		mid_duration = mid_distance / target_velocity
		self.mid_velocity = target_velocity
		self.time_until_ramp_down = self.ramp_up_ease.duration + mid_duration
		self.duration = self.ramp_up_ease.duration + self.ramp_down_ease.duration + mid_duration
		self.end_position = end_position

		# Loop Variables
		self.prev_loop_ts = None
		self.velocity = None
		self.start_time = None
		self.value = start_position

	def loop(self):
		if self.start_time == None:
			self.start_time = monotonic()
			self.prev_loop_ts = self.start_time
			self.velocity = self.ramp_up_ease(0)
			return False
		now = monotonic()
		t = min(now - self.start_time, self.duration)
		if t == self.duration:
			self.value = self.end_position
			return True
		if t < self.ramp_up_ease.duration:
			self.velocity = self.ramp_up_ease(t)
		elif t < self.time_until_ramp_down:
			self.velocity = self.mid_velocity
		else:
			t_into_rampdown = min(self.ramp_down_ease.duration, t - self.time_until_ramp_down)
			self.velocity = self.ramp_down_ease(t_into_rampdown)

		delta = now - self.prev_loop_ts
		self.value += delta * self.velocity
		self.prev_loop_ts = now
		return False
