from view import View
from game_state import STATE_PLAYING, STATE_ADMIN, STATE_PAUSE, STATE_START, STATE_FINISHED, STATE_NOT_CONNECTED, STATE_RUNNING, STATE_NOT_RUNNING, STATE_SIM_TURN

def _success(action:str, on_success: callable[[], None] = None):
    if on_success:
        on_success()
    return action

def _failure(on_failure: callable[[], None] = None):
    if on_failure:
        on_failure()
    return None

class SgtConnection:
    def __init__(self, view: View):
        self.view = view

    def is_connected(self) -> bool:
        return False

    def connect(self):
        pass

    def poll(self) -> None:
        return None

    def send_primary(self, seat: int|None = None, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        if self.view.state.state in (STATE_START, STATE_FINISHED):
            return _failure(on_failure)
        if seat == None:
            return _success('Primary', on_success)
        player = self.view.state.get_player_by_seat(seat)
        if player and player.action != None:
            return _success('Primary', on_success)
        else:
            return _failure(on_failure)
    def send_secondary(self, seat: int|None = None, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        if self.view.state.state != STATE_PLAYING:
            return _failure(on_failure)
        if seat == None:
            return _success('Secondary', on_success)
        player = self.view.state.get_player_by_seat(seat)
        if player and player.action == 'se':
            return _success('Secondary', on_success)
        else:
            return _failure(on_failure)
    def send_toggle_admin(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        if self.view.state.state in (STATE_PLAYING, STATE_ADMIN, STATE_SIM_TURN):
            return _success('ToggleAdmin', on_success)
        else:
            return _failure(on_failure)
    def send_admin_on(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        if self.view.state.state == STATE_PLAYING:
            return _success('TurnAdminOn', on_success)
        else:
            return _failure(on_failure)
    def send_admin_off(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        if self.view.state.state == STATE_ADMIN:
            return _success('TurnAdminOff', on_success)
        else:
            return _failure(on_failure)
    def send_toggle_pause(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        if self.view.state.state in (STATE_START, STATE_FINISHED):
            return _failure(on_failure)
        else:
            return _success('TogglePause', on_success)
    def send_pause_on(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        if self.view.state.state in (STATE_START, STATE_FINISHED, STATE_PAUSE):
            return _failure(on_failure)
        else:
            return _success('TurnPauseOn', on_success)
    def send_pause_off(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        if self.view.state.state == STATE_PAUSE:
            return _success('TurnPauseOff', on_success)
        else:
            return _failure(on_failure)
    def send_undo(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        if self.view.state.state in (STATE_START, STATE_FINISHED, STATE_RUNNING, STATE_NOT_RUNNING):
            return _failure(on_failure)
        else:
            return _success('Undo', on_success)

    def predict_next_game_state(self, command: str):
        if command == 'ToggleAdmin':
            if self.view.state.state in (STATE_PLAYING, STATE_SIM_TURN):
                return self.predict_next_game_state('TurnAdminOn')
            elif self.view.state.state == STATE_ADMIN:
                return self.predict_next_game_state('TurnAdminOff')
        elif command == 'TurnAdminOn':
            if self.view.state.state in (STATE_PLAYING, STATE_SIM_TURN):
                return self.view.state.make_copy(state_override=STATE_ADMIN)
        elif command == 'TurnAdminOff':
            if self.view.state.state == STATE_ADMIN:
                for player in self.view.state.players:
                    if player.action == 'in':
                        return self.view.state.make_copy(state_override=STATE_SIM_TURN)
                    elif player.action != None:
                        return self.view.state.make_copy(state_override=STATE_PLAYING)
        elif command == 'TogglePause':
            if self.view.state.state in (STATE_PLAYING, STATE_SIM_TURN, STATE_ADMIN):
                return self.predict_next_game_state('TurnPauseOn')
            elif self.view.state.state == STATE_PAUSE:
                return self.predict_next_game_state('TurnPauseOff')
        elif command == 'TurnPauseOn':
            if self.view.state.state in (STATE_PLAYING, STATE_SIM_TURN, STATE_ADMIN):
                return self.view.state.make_copy(state_override=STATE_PAUSE)
        elif command == 'TurnPauseOff':
            if self.view.state.state == STATE_PAUSE:
                for player in self.view.state.players:
                    if player.action == 'in':
                        return self.view.state.make_copy(state_override=STATE_SIM_TURN)
                    elif player.action != None:
                        return self.view.state.make_copy(state_override=STATE_PLAYING)
                # No one had any actions. We must want to go to admin time
                return self.view.state.make_copy(state_override=STATE_ADMIN)
        return None