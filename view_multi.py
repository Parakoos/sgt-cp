from game_state import GameState
from view import View

class ViewMulti(View):
    def __init__(self, views: list[View]):
        super().__init__()
        self.views = views
        for view in self.views:
            view.enable_time_reminder_check = False

    def animate(self) -> bool:
        busy_animating = super().animate()
        for view in self.views:
            busy_animating = view.animate() or busy_animating
        return busy_animating

    def show_error(self, exception):
        for view in self.views:
            view.show_error(exception)

    def set_connection_progress_text(self, text):
        for view in self.views:
            view.set_connection_progress_text(text)

    def set_state(self, state: GameState):
        self.state = state
        for view in self.views:
            view.set_state(state)

    def on_time_reminder(self, time_reminder_count: int):
        for view in self.views:
            view.on_time_reminder(time_reminder_count)