
class PixelAsDigitalOut():
	def __init__(self, pixels, index) -> None:
		self.pixels = pixels
		self.index = index

	@property
	def value(self):
		return self.pixels[self.index] == 0xffffff

	@value.setter
	def value(self, val):
		self.pixels[self.index] = 0xffffff if val else 0x000000
		self.pixels.show()