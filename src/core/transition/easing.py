import math

class EasingBase:
	limit = (0, 1)

	def __init__(self, start=0, end=1, duration=1):
		self.start = start
		self.end = end
		self.duration = duration

	@classmethod
	def func(cls, t):
		raise NotImplementedError

	def ease(self, alpha):
		t = self.limit[0] * (1 - alpha) + self.limit[1] * alpha
		t /= self.duration
		a = self.func(t)
		return self.end * a + self.start * (1 - a)

	def __call__(self, alpha):
		return self.ease(alpha)


"""
Linear
"""
class LinearInOut(EasingBase):
	def func(self, t):
		return t

"""
Quadratic easing functions
"""


class QuadEaseInOut(EasingBase):
	def func(self, t):
		if t < 0.5:
			return 2 * t * t
		return (-2 * t * t) + (4 * t) - 1


class QuadEaseIn(EasingBase):
	def func(self, t):
		return t * t


class QuadEaseOut(EasingBase):
	def func(self, t):
		return -(t * (t - 2))


class QuadEaseOutIn(EasingBase):
	def __init__(self, start=0, end=1, duration=1):
		super().__init__(start, end, duration)
		self.f1 = QuadEaseOut(0, 0.5, 0.5)
		self.f2 = QuadEaseIn(0.5, 1, 0.5)
	def func(self, t):
		if t < 0.5:
			return self.f1(t)
		return self.f2(t-0.5)

"""
Cubic easing functions
"""


class CubicEaseIn(EasingBase):
	def func(self, t):
		return t * t * t


class CubicEaseOut(EasingBase):
	def func(self, t):
		return (t - 1) * (t - 1) * (t - 1) + 1


class CubicEaseInOut(EasingBase):
	def func(self, t):
		if t < 0.5:
			return 4 * t * t * t
		p = 2 * t - 2
		return 0.5 * p * p * p + 1


class CubicEaseOutIn(EasingBase):
	def __init__(self, start=0, end=1, duration=1):
		super().__init__(start, end, duration)
		self.f1 = CubicEaseOut(0, 0.5, 0.5)
		self.f2 = CubicEaseIn(0.5, 1, 0.5)
	def func(self, t):
		if t < 0.5:
			return self.f1(t)
		return self.f2(t-0.5)

"""
Quartic easing functions
"""


class QuarticEaseIn(EasingBase):
	def func(self, t):
		return t * t * t * t


class QuarticEaseOut(EasingBase):
	def func(self, t):
		return (t - 1) * (t - 1) * (t - 1) * (1 - t) + 1


class QuarticEaseInOut(EasingBase):
	def func(self, t):
		if t < 0.5:
			return 8 * t * t * t * t
		p = t - 1
		return -8 * p * p * p * p + 1

class QuarticEaseOutIn(EasingBase):
	def __init__(self, start=0, end=1, duration=1):
		super().__init__(start, end, duration)
		self.f1 = QuarticEaseOut(0, 0.5, 0.5)
		self.f2 = QuarticEaseIn(0.5, 1, 0.5)
	def func(self, t):
		if t < 0.5:
			return self.f1(t)
		return self.f2(t-0.5)


"""
Quintic easing functions
"""


class QuinticEaseIn(EasingBase):
	def func(self, t):
		return t * t * t * t * t


class QuinticEaseOut(EasingBase):
	def func(self, t):
		return (t - 1) * (t - 1) * (t - 1) * (t - 1) * (t - 1) + 1


class QuinticEaseInOut(EasingBase):
	def func(self, t):
		if t < 0.5:
			return 16 * t * t * t * t * t
		p = (2 * t) - 2
		return 0.5 * p * p * p * p * p + 1

class QuinticEaseOutIn(EasingBase):
	def __init__(self, start=0, end=1, duration=1):
		super().__init__(start, end, duration)
		self.f1 = QuinticEaseOut(0, 0.5, 0.5)
		self.f2 = QuinticEaseIn(0.5, 1, 0.5)
	def func(self, t):
		if t < 0.5:
			return self.f1(t)
		return self.f2(t-0.5)

"""
Sine easing functions
"""


class SineEaseIn(EasingBase):
	def func(self, t):
		return math.sin((t - 1) * math.pi / 2) + 1


class SineEaseOut(EasingBase):
	def func(self, t):
		return math.sin(t * math.pi / 2)


class SineEaseInOut(EasingBase):
	def func(self, t):
		return 0.5 * (1 - math.cos(t * math.pi))

class SineEaseOutIn(EasingBase):
	def __init__(self, start=0, end=1, duration=1):
		super().__init__(start, end, duration)
		self.f1 = SineEaseOut(0, 0.5, 0.5)
		self.f2 = SineEaseIn(0.5, 1, 0.5)
	def func(self, t):
		if t < 0.5:
			return self.f1(t)
		return self.f2(t-0.5)


"""
Circular easing functions
"""


class CircularEaseIn(EasingBase):
	def func(self, t):
		return 1 - math.sqrt(1 - (t * t))


class CircularEaseOut(EasingBase):
	def func(self, t):
		return math.sqrt((2 - t) * t)


class CircularEaseInOut(EasingBase):
	def func(self, t):
		if t < 0.5:
			return 0.5 * (1 - math.sqrt(1 - 4 * (t * t)))
		return 0.5 * (math.sqrt(-((2 * t) - 3) * ((2 * t) - 1)) + 1)

class CircularEaseOutIn(EasingBase):
	def __init__(self, start=0, end=1, duration=1):
		super().__init__(start, end, duration)
		self.f1 = CircularEaseOut(0, 0.5, 0.5)
		self.f2 = CircularEaseIn(0.5, 1, 0.5)
	def func(self, t):
		if t < 0.5:
			return self.f1(t)
		return self.f2(t-0.5)

"""
Exponential easing functions
"""


class ExponentialEaseIn(EasingBase):
	def func(self, t):
		if t == 0:
			return 0
		return math.pow(2, 10 * (t - 1))


class ExponentialEaseOut(EasingBase):
	def func(self, t):
		if t == 1:
			return 1
		return 1 - math.pow(2, -10 * t)


class ExponentialEaseInOut(EasingBase):
	def func(self, t):
		if t == 0 or t == 1:
			return t

		if t < 0.5:
			return 0.5 * math.pow(2, (20 * t) - 10)
		return -0.5 * math.pow(2, (-20 * t) + 10) + 1

class ExponentialEaseOutIn(EasingBase):
	def __init__(self, start=0, end=1, duration=1):
		super().__init__(start, end, duration)
		self.f1 = ExponentialEaseOut(0, 0.5, 0.5)
		self.f2 = ExponentialEaseIn(0.5, 1, 0.5)
	def func(self, t):
		if t < 0.5:
			return self.f1(t)
		return self.f2(t-0.5)


"""
Elastic Easing Functions
"""


class ElasticEaseIn(EasingBase):
	def func(self, t):
		return math.sin(13 * math.pi / 2 * t) * math.pow(2, 10 * (t - 1))


class ElasticEaseOut(EasingBase):
	def func(self, t):
		return math.sin(-13 * math.pi / 2 * (t + 1)) * math.pow(2, -10 * t) + 1


class ElasticEaseInOut(EasingBase):
	def func(self, t):
		if t < 0.5:
			return (
				0.5
				* math.sin(13 * math.pi / 2 * (2 * t))
				* math.pow(2, 10 * ((2 * t) - 1))
			)
		return 0.5 * (
			math.sin(-13 * math.pi / 2 * ((2 * t - 1) + 1))
			* math.pow(2, -10 * (2 * t - 1))
			+ 2
		)


"""
Back Easing Functions
"""


class BackEaseIn(EasingBase):
	def func(self, t):
		return t * t * t - t * math.sin(t * math.pi)


class BackEaseOut(EasingBase):
	def func(self, t):
		p = 1 - t
		return 1 - (p * p * p - p * math.sin(p * math.pi))


class BackEaseInOut(EasingBase):
	def func(self, t):
		if t < 0.5:
			p = 2 * t
			return 0.5 * (p * p * p - p * math.sin(p * math.pi))

		p = 1 - (2 * t - 1)

		return 0.5 * (1 - (p * p * p - p * math.sin(p * math.pi))) + 0.5


"""
Bounce Easing Functions
"""


class BounceEaseIn(EasingBase):
	def func(self, t):
		return 1 - BounceEaseOut().func(1 - t)


class BounceEaseOut(EasingBase):
	def func(self, t):
		if t < 4 / 11:
			return 121 * t * t / 16
		elif t < 8 / 11:
			return (363 / 40.0 * t * t) - (99 / 10.0 * t) + 17 / 5.0
		elif t < 9 / 10:
			return (4356 / 361.0 * t * t) - (35442 / 1805.0 * t) + 16061 / 1805.0
		return (54 / 5.0 * t * t) - (513 / 25.0 * t) + 268 / 25.0


class BounceEaseInOut(EasingBase):
	def func(self, t):
		if t < 0.5:
			return 0.5 * BounceEaseIn().func(t * 2)
		return 0.5 * BounceEaseOut().func(t * 2 - 1) + 0.5
