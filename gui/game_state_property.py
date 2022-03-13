"""
Contains class to update gui when game state is changed and global instance of such class.
"""

from threading import Lock


class GameStateProperty:
    """
    Class with game state property. Used to update gui when game state is changed.
    """
    def __init__(self):
        self.callbacks = []
        self.lock = Lock()
        self._game_state = {}

    def bind(self, callback):
        """
        Adds callback to callback list
        :param callback: new callback
        :return:
        """
        self.callbacks.append(callback)

    @property
    def game_state(self):
        """
        Game state dict property
        :return: Game state dict property
        """
        return self._game_state

    @game_state.setter
    def game_state(self, value):
        """
        Game state dict property setter
        :param value: New game state value
        :return:
        """
        with self.lock:
            self._game_state = value
            for callback in self.callbacks:
                callback(self._game_state)


game_state_property = GameStateProperty()
