from neopixel import NeoPixel

class PausablePixels(NeoPixel):
	def __init__(self, pin, n, *, bpp = 3, brightness = 1, auto_write = True, pixel_order = None):
		super().__init__(pin, n, bpp=bpp, brightness=brightness, auto_write=auto_write, pixel_order=pixel_order)
		self.pause = False

	def show(self):
		if not self.pause:
			super(NeoPixel, self).show()