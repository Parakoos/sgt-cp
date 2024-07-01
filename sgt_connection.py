from view import View

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
        if self.view.state.state in ('st', 'en'):
            return _failure(on_failure)
        if seat == None:
            return _success('Primary', on_success)
        player = self.view.state.get_player_by_seat(seat)
        if player and player.action != None:
            return _success('Primary', on_success)
        else:
            return _failure(on_failure)
    def send_secondary(self, seat: int|None = None, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        if self.view.state.state != 'pl':
            return _failure(on_failure)
        if seat == None:
            return _success('Secondary', on_success)
        player = self.view.state.get_player_by_seat(seat)
        if player and player.action == 'se':
            return _success('Secondary', on_success)
        else:
            return _failure(on_failure)
    def send_toggle_admin(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        if self.view.state.state in ('pl, ad'):
            return _success('ToggleAdmin', on_success)
        else:
            return _failure(on_failure)
    def send_admin_on(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        if self.view.state.state == 'pl':
            return _success('TurnAdminOn', on_success)
        else:
            return _failure(on_failure)
    def send_admin_off(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        if self.view.state.state == 'ad':
            return _success('TurnAdminOff', on_success)
        else:
            return _failure(on_failure)
    def send_toggle_pause(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        if self.view.state.state in ('st', 'en'):
            return _failure(on_failure)
        else:
            return _success('TogglePause', on_success)
    def send_pause_on(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        if self.view.state.state in ('st', 'en', 'pa'):
            return _failure(on_failure)
        else:
            return _success('TurnPauseOn', on_success)
    def send_pause_off(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        if self.view.state.state == 'pa':
            return _success('TurnPauseOff', on_success)
        else:
            return _failure(on_failure)
    def send_undo(self, on_success: callable[[], None] = None, on_failure: callable[[], None] = None):
        if self.view.state.state in ('st', 'en', 'ru', 'nr'):
            return _failure(on_failure)
        else:
            return _success('Undo', on_success)