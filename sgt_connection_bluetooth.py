import adafruit_logging as logging
log = logging.getLogger()
import time
from view import View
from sgt_connection import SgtConnection
from settings import BLE_DEVICE_NAME

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService


class SgtConnectionBluetooth(SgtConnection):
    def __init__(self, view: View, on_connect: callable[[], None], on_state_line: callable[[str, float], None]):
        super().__init__(view)
        self.on_connect = on_connect
        self.on_state_line = on_state_line
        self.ble = BLERadio()
        self.uart = UARTService()
        self.advertisement = ProvideServicesAdvertisement(self.uart)
        self.ble.name = BLE_DEVICE_NAME
        self.incomplete_line_read = None
        self.last_is_connected_check = False

    def is_connected(self) -> bool:
        if self.ble.connected and not self.last_is_connected_check:
            self.view.set_connection_progress_text('Connected')
            self.ble.stop_advertising()
            self.on_connect()
        self.last_is_connected_check = self.ble.connected
        return self.ble.connected

    def connect(self):
        self.view.set_connection_progress_text(f"Advertising BLE as {self.ble.name}")
        self.ble.start_advertising(self.advertisement)

    def poll(self) -> None:
        while self.uart.in_waiting > 0:
            read_text_ts = time.monotonic()
            read_text = str(self.uart.read(self.uart.in_waiting), 'utf-8')
            lines = [(read_text_ts, line) for line in read_text.split("\n")]
            log.debug("read_lines: %s", lines)

            if len(lines) == 0:
                return
            last_item = lines.pop()
            if last_item[1] == '':
                do_this_line = lines.pop()
                if len(lines) > 0:
                    log.debug(f"SKIP: {lines}")
                time.sleep(0.01)
                if self.uart.in_waiting:
                    log.debug(f"SKIP AFTER ALL: {do_this_line}")
                    self.incomplete_line_read = None
                else:
                    try:
                        log.debug(f"EXECUTE LINE: {do_this_line}")
                        self.on_state_line(do_this_line[1], do_this_line[0])
                    except:
                        if self.incomplete_line_read != None:
                            line_prefixed_with_incomplete = (self.incomplete_line_read[0], self.incomplete_line_read[1] + do_this_line[1])
                            log.debug(f"EXECUTE LINE (with incomplete): {line_prefixed_with_incomplete}")
                            self.on_state_line(line_prefixed_with_incomplete[1], line_prefixed_with_incomplete[0])
                    finally:
                        self.incomplete_line_read = None
                        print("The 'try except' is finished")
            else:
                if len(lines) > 0:
                    log.debug(f"SKIP: {lines}")
                log.debug(f"Incomplete Line: {last_item}")
                self.incomplete_line_read = last_item

    def send(self, value: str, on_success: callable[[], None] = None):
        log.info(value)
        if on_success:
            on_success()
        self.uart.write((value+"\n").encode("utf-8"))
