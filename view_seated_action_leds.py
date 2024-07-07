from view import View
from game_state import GameState
from digitalio import DigitalInOut

class ViewSeatedActionLeds(View):
	def __init__(self, leds: list[DigitalInOut]):
		super().__init__()
		self.leds = leds
	def on_state_update(self, state: GameState, old_state: GameState):
		for player in state.players:
			index = player.seat - 1
			if index < len(self.leds):
				self.leds[index].value = player.action != None
