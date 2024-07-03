import adafruit_logging as logging
log = logging.getLogger()
from game_state import GameState
from utils import log_exception, check_if_crossed_time_border
from time import monotonic

class View():
    def __init__(self):
        self.state = None
        self.polling_delays = []
        self.current_times = None
        self.time_reminder_check_timeout = 0
        self.enable_time_reminder_check = True

    def animate(self) -> bool:
        "Return true of the animation is busy. Returns false if the animation is static."
        if self.enable_time_reminder_check and self.state and self.state.time_reminders and self.state.state in (GameState.STATE_PLAYING, GameState.STATE_SIM_TURN) and monotonic() >= self.time_reminder_check_timeout:
            # We have time reminders set, and we are close to performing one of its border crossings.
            # We should return True from here to mark this view as busy.
            current_times = self.state.get_current_timings()
            if self.current_times == None:
                self.current_times = current_times
                return True
            elif self.current_times.turn_time == current_times.turn_time:
                # We haven't made a change in the time. Just return busy
                return True
            else:
                crossed_borders = check_if_crossed_time_border(self.state.time_reminders, self.current_times.turn_time, current_times.turn_time)
                self.current_times = current_times
                if crossed_borders > 0:
                    self.on_time_reminder(crossed_borders)
                    return True
                else:
                    time_to_next_border_crossing = -crossed_borders
                    average_polling_delay = 1 if len(self.polling_delays) == 0 else sum(self.polling_delays) / len(self.polling_delays)
                    stop_animating_this_close_to_next_border_crossing = average_polling_delay + 1
                    time_to_start_checking_border_crossings = time_to_next_border_crossing - stop_animating_this_close_to_next_border_crossing
                    if time_to_start_checking_border_crossings > 0:
                        self.time_reminder_check_timeout = monotonic() + time_to_start_checking_border_crossings
                        log.info('Start checking time reminders at t=%s', self.time_reminder_check_timeout)
                        return False
                    else:
                        return True
        else:
            # We do not have time reminders, or we are comfortably far away from it, so we are not busy.
            return False
    def show_error(self, exception):
        log_exception(exception)
        self.switch_to_error()
    def set_connection_progress_text(self, text):
        pass
    def switch_to_playing(self, state: GameState, old_state: GameState):
        pass
    def switch_to_simultaneous_turn(self, state: GameState, old_state: GameState):
        pass
    def switch_to_admin_time(self, state: GameState, old_state: GameState):
        pass
    def switch_to_paused(self, state: GameState, old_state: GameState):
        pass
    def switch_to_sandtimer_running(self, state: GameState, old_state: GameState):
        pass
    def switch_to_sandtimer_not_running(self, state: GameState, old_state: GameState):
        pass
    def switch_to_start(self, state: GameState, old_state: GameState):
        pass
    def switch_to_end(self, state: GameState, old_state: GameState):
        pass
    def switch_to_no_game(self):
        pass
    def switch_to_not_connected(self):
        pass
    def switch_to_error(self):
        pass
    def on_state_update(self, state: GameState, old_state: GameState):
        pass
    def on_time_reminder(self, time_reminder_count: int):
        "Sub-classes should implement this to handle triggered time reminders"
        pass

    def set_state(self, state: GameState | None):
        old_state = self.state
        self.state = state
        self.time_reminder_check_timeout = 0
        self.current_times = self.state.get_current_timings()
        if self.state == None:
            self.switch_to_no_game()
        elif old_state == None or self.state.state != old_state.state:
            if state.state == GameState.STATE_PLAYING:
                self.switch_to_playing(state, old_state)
            elif state.state == GameState.STATE_SIM_TURN:
                self.switch_to_simultaneous_turn(state, old_state)
            elif state.state == GameState.STATE_ADMIN:
                self.switch_to_admin_time(state, old_state)
            elif state.state == GameState.STATE_PAUSE:
                self.switch_to_paused(state, old_state)
            elif state.state == GameState.STATE_FINISHED:
                self.switch_to_end(state, old_state)
            elif state.state == GameState.STATE_START:
                self.switch_to_start(state, old_state)
            elif state.state == GameState.STATE_RUNNING:
                self.switch_to_sandtimer_running(state, old_state)
            elif state.state == GameState.STATE_NOT_RUNNING:
                self.switch_to_sandtimer_not_running(state, old_state)
            elif state.state == GameState.STATE_NOT_CONNECTED:
                self.switch_to_not_connected
            else:
                raise Exception(f'Unknown state: {state.state}')
        self.on_state_update(state, old_state)

    def record_polling_delay(self, delay: float):
        self.polling_delays.append(delay)
        self.polling_delays = self.polling_delays[0:5]
