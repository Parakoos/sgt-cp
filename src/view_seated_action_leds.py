from view import View
from game_state import GameState
from digitalio import DigitalInOut

class ViewSeatedActionLeds(View):
	def __init__(self, leds: list[DigitalInOut]):
		super().__init__()
		self.leds = leds
	def on_state_update(self, state: GameState|None, old_state: GameState|None):
		if state == None:
			for led in self.leds:
				led.value = False
		else:
			for player in state.players:
				index = player.seat - 1
				if index < len(self.leds):
					self.leds[index].value = player.action != None
