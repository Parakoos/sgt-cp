import adafruit_logging as logging
log = logging.getLogger()
log.setLevel(10)
import board
from game_state import GameState
from reorder import Reorder

# =================== Settings =================== #
BUTTON_PINS = [board.BUTTON, board.D1, board.D2]
# =============== End of Settings ================ #

# ---------- VIEW SETUP -------------#
from view_multi import ViewMulti
from view_console import ViewConsole
view = ViewMulti([ViewConsole()])
view.set_state(None)

# ---------- WIFI -------------#
from sgt_connection_mqtt import SgtConnectionMQTT
sgt_connection = SgtConnectionMQTT(view)

# ---------- BUTTONS SETUP -------------#
from buttons import Buttons
from microcontroller import Pin
button_pin_to_val_when_pressed = {
	board.BUTTON: False,
	board.D1: True,
	board.D2: True,
}
buttons = Buttons(button_pin_to_val_when_pressed)
def btn_callback(btn_pin: Pin, presses: int, long_press: bool):
	log.info('btn_callback: %s, %s, %s', btn_pin, presses, long_press)
	if view.reorder is not None:
		log.info('Buttons presses disabled during reorder')
	elif long_press:
		if presses == 1:
			log.info(f"Long Press: State={view.state.state}, StateType={view.state.state_type}")
			if (view.state.allow_reorder()):
				log.info(f"Reordering in progress. Stop listening to normal button presses.")
				seat = BUTTON_PINS.index(btn_pin) + 1
				view.reorder = Reorder(initiating_seat=seat)
			else:
				sgt_connection.enqueue_send_toggle_admin()
		elif presses == 2:
			# sgt_connection.enqueue_send_toggle_pause()
			sgt_connection.enqueue_send_start_sim_turn(set([1,2]))
		elif presses == 3:
			sgt_connection.enqueue_send_undo()
		elif presses == 4:
			raise Exception('Test Error!')
	else:
		seat = BUTTON_PINS.index(btn_pin) + 1
		if presses == 1:
			sgt_connection.enqueue_send_primary(seat=seat)
		elif presses == 2:
			sgt_connection.enqueue_send_secondary(seat=seat)

def pressed_keys_update_callback(pressed_keys: set[Pin]):
	if view.state is None:
		return
	log.info(f"Pressed keys: {pressed_keys}: State={view.state.state}, StateType={view.state.state_type}")
	if view.reorder is not None:
		if len(pressed_keys) == 0:
			log.info(f"Reordering stopped")
			view.reorder = None
		else:
			pressed_seats = set(map(lambda x: BUTTON_PINS.index(x) + 1, pressed_keys))
			log.info(f"Pressed Seats: {pressed_seats}")
			view.reorder.handle_activated_seats(pressed_seats)
	# if len(pressed_keys) == len(view.state.players):
	# 	sgt_connection.enqueue_send_start_game(2)

# ---------- MAIN LOOP -------------#
from loop import main_loop, ErrorHandlerResumeOnButtonPress
error_handler = ErrorHandlerResumeOnButtonPress(view, buttons)
def on_connect():
	buttons.clear_callbacks()
	buttons.set_pressed_keys_update_callback(pressed_keys_update_callback)
	for btn_pin in BUTTON_PINS:
		buttons.set_callback(btn_pin, presses=1, callback = btn_callback)
		buttons.set_callback(btn_pin, presses=2, callback = btn_callback)
		buttons.set_callback(btn_pin, presses=1, long_press=True, callback = btn_callback)
		buttons.set_callback(btn_pin, presses=2, long_press=True, callback = btn_callback)
		buttons.set_callback(btn_pin, presses=3, long_press=True, callback = btn_callback)
		buttons.set_callback(btn_pin, presses=4, long_press=True, callback = btn_callback)

main_loop(sgt_connection, view, on_connect, error_handler.on_error, (buttons.loop,))