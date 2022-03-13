from threading import Lock


class GameStateProperty:
    def __init__(self):
        self.callbacks = []
        self.lock = Lock()
        self._game_state = {}

    def bind(self, callback):
        self.callbacks.append(callback)

    @property
    def game_state(self):
        return self._game_state

    @game_state.setter
    def game_state(self, value):
        with self.lock:
            self._game_state = value
            for callback in self.callbacks:
                callback(self._game_state)


game_state_property = GameStateProperty()
