from typing import Optional

from bot.action_estimator import ActionEstimator
from bot.actions_generator import ActionsGenerator
from bot.bot import Bot
from bot.bot_game_state import BotGameState
from game_client.actions import Action
from game_client.vehicles import Vehicle
from utility.custom_typings import GameStateDictTyping, MapDictTyping


class StepScoreBot(Bot):
    """
    Bot that uses formula to choose actions.

    :param self.game_state: BotGameState object
    """

    def __init__(
        self,
        game_map: MapDictTyping,
        estimator_weights=None,
        game_state_class=BotGameState,
    ):
        super().__init__(game_map, game_state_class)
        if estimator_weights is None:
            estimator_weights = [1, 1, 1, 1]
        self.actions_generator = ActionsGenerator(self.game_state)
        self.action_estimator: ActionEstimator = ActionEstimator(
            self.game_state, estimator_weights
        )

    def get_actions(self, game_state: GameStateDictTyping) -> list[Action]:
        actions: list[Action] = []

        self.game_state.update(game_state)
        for vehicle in self.game_state.current_player.ordered_vehicle_iter:
            action = self.__get_action(vehicle)
            if action is not None:
                self.game_state.update_from_action(action)
                actions.append(action)

        return actions

    def __get_action(self, vehicle: Vehicle) -> Optional[Action]:
        possible_actions = self.__get_possible_actions(vehicle)
        if possible_actions:
            return possible_actions[0]

        return None

    def __get_possible_actions(self, actor: Vehicle) -> list[Action]:
        actions = self.actions_generator(actor)

        actions.sort(key=lambda step: self.action_estimator(step), reverse=False)

        return actions
