import adafruit_logging as logging
log = logging.getLogger()
from game_state import GameState

class View():
    def __init__(self):
        self.state = None

    def animate(self) -> bool:
        "Return true of the animation is busy. Returns false if the animation is static."
        return False
    def show_error(self, exception):
        log.exception(exception)
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

    def set_state(self, state: GameState | None):
        old_state = self.state
        self.state = state
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

