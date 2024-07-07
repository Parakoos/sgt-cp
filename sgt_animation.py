import time
from adafruit_led_animation.animation import Animation
from easing import EasingBase
import adafruit_fancyled.adafruit_fancyled as fancy
from adafruit_pixelbuf import PixelBuf
import adafruit_logging as logging
from utils import mix
log = logging.getLogger()

class SgtAnimation():
	def __init__(self, *members: tuple[Animation, float|int|None, bool], color: int|None = None) -> None:
		self.members = members
		self.current_index = -1
		self.animation_start_ts = 0
		self.timed_by_cycles = False
		self.color=members[0][0].color
		self.transition = None
		self.next()

	def next(self):
		self.current_index = (self.current_index + 1) % len(self.members)
		animation, animation_timing, interruptable = self.members[self.current_index]
		animation.reset()
		if self.color:
			animation.color = self.color
		self.timed_by_cycles = animation.on_cycle_complete_supported
		if self.timed_by_cycles:
			animation.cycle_count = 0
		else:
			self.animation_start_ts = time.monotonic()

	def animate(self, show=True) -> bool:
		animation, animation_timing, interruptable = self.members[self.current_index]
		if self.transition:
			easing, start_time, start_color, target_color = self.transition
			elapsed_time = time.monotonic() - start_time
			fade_progress = easing.ease(elapsed_time)
			color = mix(start_color, target_color, fade_progress)
			self.set_color(color)
			if elapsed_time >= easing.duration:
				self.transition = None

		animation.animate(show)
		if animation_timing == None:
			# If the timing is None, then we never advance.
			pass
		elif (self.timed_by_cycles):
			if (animation.cycle_count >= animation_timing):
				self.next()
		else:
			if time.monotonic() - self.animation_start_ts >= animation_timing:
				self.next()
		return not(self.transition == None and self.members[self.current_index][2])

	def set_color(self, color: tuple[int,int,int], transition: EasingBase = None):
		if transition:
			self.transition = (transition, time.monotonic(), self.color, color)
		else:
			self.color = color
			self.members[self.current_index][0].color = color

class SgtAnimationGroup():
	def __init__(self, animations: list[SgtAnimation], parent_pixel_obj: PixelBuf) -> None:
		self.animations = animations
		self.parent_pixel_obj = parent_pixel_obj

	def animate(self, show=True) -> True:
		busy_animating = False
		for animation in self.animations:
			busy_animating = animation.animate(False) or busy_animating
		self.parent_pixel_obj.show()
		return busy_animating

class SgtSolid(Animation):
	def __init__(self, pixel_object, speed, color, name=None):
		super().__init__(pixel_object, speed, color, peers=None, paused=False, name=name)

	def draw(self):
		self.pixel_object.fill(self.color)
