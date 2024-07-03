import adafruit_logging as logging
log = logging.getLogger()
import time
from view import View
from sgt_connection import SgtConnection

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
import json
from traceback import print_exception

class SgtConnectionBluetooth(SgtConnection):
    def __init__(self,
                 view: View,
                 suggestions: dict,
                 ble_device_name: str,
                 on_state_line: callable[[str, float], None],
                 on_error: callable[[], None] = None,
                 ):
        super().__init__(view)
        self.on_state_line = on_state_line
        self.on_error=on_error
        self.ble = BLERadio()
        self.uart = UARTService()
        self.advertisement = ProvideServicesAdvertisement(self.uart)
        self.ble.name = ble_device_name
        self.incomplete_line_read = None
        self.last_is_connected_check = False
        self.all_read_text = ''
        self.text_read = ''
        self.last_line_executed = None
        self.suggestions = suggestions
        self.byte_array = bytearray(20)

    def is_connected(self) -> bool:
        if self.ble.connected and not self.last_is_connected_check:
            self.view.set_connection_progress_text('Connected')
            self.ble.stop_advertising()
            timeout = time.monotonic() + 3
            while time.monotonic() < timeout:
                self.view.animate()
            self.send('Enable ACK')
            self.send('Poll')
        self.last_is_connected_check = self.ble.connected
        return self.ble.connected

    def connect(self):
        self.view.set_connection_progress_text(f"Advertising BLE as {self.ble.name}")
        self.ble.start_advertising(self.advertisement)

    def poll(self) -> None:
        if self.uart.in_waiting == 0:
            if self.incomplete_line_read and time.monotonic() - self.incomplete_line_read[0] > 6:
                log.debug('Old incomplete line. Clear the buffer and line, then call on_error. %s', self.incomplete_line_read)
                self.uart.reset_input_buffer()
                self.incomplete_line_read = None
                if self.on_error:
                    self.on_error()
            return

        while self.uart.in_waiting > 0:
            bytes_read = self.uart.readinto(buf=self.byte_array, nbytes=self.uart.in_waiting)
            read_text = str(self.byte_array[:bytes_read], 'utf-8')
            # log.debug('ACK of line %s', read_text)
            self.send('ACK')
            self.all_read_text += read_text
            lines = [(time.monotonic(), line) for line in read_text.split("\n")]
            if self.incomplete_line_read != None:
                lines[0] = (self.incomplete_line_read[0], self.incomplete_line_read[1]+lines[0][1])
                self.incomplete_line_read = None

            if len(lines) == 0:
                return
            last_item = lines.pop()
            lines = [line for line in lines if line[1] != '']
            if len(lines[:-1]) > 0:
                print(f'SKIP: {lines[:-1]}')

            # log.debug("Last Item: %s, lines: %s", last_item, lines)
            if last_item[1] == '':
                if len(lines) > 0:
                    do_this_line = lines.pop()
                    if do_this_line[1] == 'GET SETUP':
                        log.debug('SENDING SUGGESTED SETUP')
                        self.send(json.dumps(self.suggestions))
                        self.last_line_executed = do_this_line[1]
                    elif (do_this_line[1] == self.last_line_executed):
                        log.debug(f"SKIP DUPLICATE LINE: {self.last_line_executed}")
                    else:
                        log.debug(f"EXECUTE LINE: {do_this_line}")
                        try:
                            self.on_state_line(do_this_line[1], do_this_line[0])
                            self.last_line_executed = do_this_line[1]
                        except Exception as e:
                            print_exception(e)
                            if self.on_error:
                                self.on_error()
            else:
                log.debug('incomplete line: "%s"', last_item[1])
                self.incomplete_line_read = last_item
                time.sleep(0.05)
    def send(self, value: str|None):
        if value == None:
            return
        log.info("-> %s", value)
        self.uart.write((value+"\n").encode("utf-8"))

        new_game_state = self.predict_next_game_state(value)
        if new_game_state:
            self.view.set_state(new_game_state)
            while self.view.animate():
                pass

    def send_primary(self, seat: int|None = None, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        action = super().send_primary(seat, on_success, on_failure)
        if action != None and seat != None:
            self.send(f'{action} #{seat}')
        else:
            self.send(action)
    def send_secondary(self, seat: int|None = None, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        action = super().send_secondary(seat, on_success, on_failure)
        if action != None and seat != None:
            self.send(f'{action} #{seat}')
        else:
            self.send(action)
    def send_toggle_admin(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        self.send(super().send_toggle_admin(on_success, on_failure))
    def send_admin_on(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        self.send(super().send_admin_on(on_success, on_failure))
    def send_admin_off(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        self.send(super().send_admin_off(on_success, on_failure))
    def send_toggle_pause(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        self.send(super().send_toggle_pause(on_success, on_failure))
    def send_pause_on(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        self.send(super().send_pause_on(on_success, on_failure))
    def send_pause_off(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        self.send(super().send_pause_off(on_success, on_failure))
    def send_undo(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        self.send(super().send_undo(on_success, on_failure))
