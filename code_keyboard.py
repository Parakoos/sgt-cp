import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
import board

BUTTON_PINS = [board.A1, board.A2, board.A3, board.A4]

kbd = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(kbd)

def btn_callback(btn_pin: Pin, presses: int, long_press: bool):
	seat = BUTTON_PINS.index(btn_pin) + 1
	if not long_press:
		if presses == 1:
			layout.write(f"{seat}t")
		elif presses == 2:
			layout.write(f"{seat}r")

# ---------- BUTTONS SETUP -------------#
from buttons import Buttons
from microcontroller import Pin
button_pin_to_val_when_pressed = {pin: False for pin in BUTTON_PINS}
buttons = Buttons(button_pin_to_val_when_pressed)
for pin in BUTTON_PINS:
	buttons.set_callback(pin, 1, False, btn_callback)
	buttons.set_callback(pin, 2, False, btn_callback)

while True:
    buttons.loop()
