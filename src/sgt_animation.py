import time
from adafruit_led_animation.animation import Animation
from easing import EasingBase
from utils.color import DisplayedColor, StaticColor
from utils.transition import ColorTransitionFunction
from adafruit_pixelbuf import PixelBuf
import adafruit_logging as logging
log = logging.getLogger()

class SgtAnimation():
	def __init__(self, color: DisplayedColor|StaticColor, *members: tuple[Animation, float|int|None, bool]) -> None:
		self.members = members
		self.current_index = -1
		self.animation_start_ts = 0
		self.timed_by_cycles = False
		if isinstance(color, DisplayedColor):
			self.displayed_color = color
		elif isinstance(color, StaticColor):
			self.displayed_color = color.create_display_color()
		else:
			raise TypeError(f"Expected Color, got {type(color)}")
		self.transition = None
		self.next()

	def next(self):
		self.current_index = (self.current_index + 1) % len(self.members)
		animation, animation_timing, interruptable = self.members[self.current_index]
		animation.reset()
		animation.color = self.displayed_color.current_color
		self.timed_by_cycles = animation.on_cycle_complete_supported
		if self.timed_by_cycles:
			animation.cycle_count = 0
		else:
			self.animation_start_ts = time.monotonic()

	def animate(self, show=True) -> bool:
		animation, animation_timing, interruptable = self.members[self.current_index]
		if self.transition:
			if self.transition.loop():
				self.transition = None
			self.set_color(self.displayed_color)

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

	def set_color(self, new_display_color: DisplayedColor, transition: EasingBase|None = None):
		if transition:
			self.transition = ColorTransitionFunction[self.displayed_color, new_display_color, transition]
		else:
			self.displayed_color = new_display_color
			self.members[self.current_index][0].color = self.displayed_color.current_color

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
	def __init__(self, pixel_object: PixelBuf, color: int):
		super().__init__(pixel_object, 0.01, color)

	def draw(self):
		self.pixel_object.fill(self.color)
