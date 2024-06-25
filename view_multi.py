from game_state import GameState
from view import View

class ViewMulti(View):
    def __init__(self, views: list[View]):
        super().__init__()
        self.views = views

    def animate(self):
        interruptable = True
        for view in self.views:
            interruptable = view.animate() and interruptable
        return interruptable

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
