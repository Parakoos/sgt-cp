from game_state import GameState

class View():
    def __init__(self):
        self.state = GameState()

    def animate(self):
        pass
    def show_error(self, exception):
        pass
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
    def switch_to_trying_to_connect(self, state: GameState, old_state: GameState):
        pass
    def switch_to_connecting(self, state: GameState, old_state: GameState):
        pass
    def switch_to_error(self, state: GameState, old_state: GameState):
        pass
    def on_state_update(self, state: GameState, old_state: GameState):
        pass

    def set_state(self, state: GameState):
        state_update = self.state.state != state.state
        state_version_update = self.state.game_state_version != state.game_state_version
        old_state = self.state
        self.state = state
        if state_update:
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
            else :
                self.switch_to_error(state, old_state)
        self.on_state_update(state, old_state)

