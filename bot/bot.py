"""
Contains base bot class.

"""
from bot.bot_game_state import BotGameState
from game_client.actions import Action
from utility.custom_typings import GameStateDictTyping


# pylint: disable=too-few-public-methods
# Nothing else is needed here
class Bot:
    """
    Abstract bot class.

    """

    def __init__(self, game_map, game_state_class=BotGameState):
        self.game_state: BotGameState = game_state_class(game_map)

    def get_actions(self, game_state: GameStateDictTyping) -> list[Action]:
        """
        :param game_state: current state of the game
        :return: list of actions to perform
        """
        raise NotImplementedError
