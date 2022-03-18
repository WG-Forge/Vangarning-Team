"""
Contains class for the bot that uses action estimation for picking action.

"""

from typing import Optional

from bot.action_estimator import ActionEstimator
from bot.actions_generator import ActionsGenerator
from bot.bot import Bot
from bot.bot_game_state import BotGameState
from game_client.actions import Action
from game_client.server_interaction import ActionCode
from game_client.vehicles import Vehicle
from utility.custom_typings import GameStateDictTyping, MapDictTyping

OPTIMAL_WEIGHTS = [
    -11.057281755495081,
    31.319257045898585,
    -8.514396386536838,
    -18.00125116578524,
    -0.6392295531874146,
]


# pylint: disable=too-few-public-methods
# Only one method is needed here
class StepScoreBot(Bot):
    """
    Bot that uses formula to choose actions.

    :param self.game_state: BotGameState object
    """

    def __init__(
        self,
        game_map: MapDictTyping,
        estimator_weights=None,
        estimator_class=ActionEstimator,
        game_state_class=BotGameState,
    ):
        super().__init__(game_map, game_state_class)
        if estimator_weights is None:
            estimator_weights = OPTIMAL_WEIGHTS
        self.actions_generator = ActionsGenerator(self.game_state)
        self.action_estimator: ActionEstimator = estimator_class(
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
        idle_action = Action(ActionCode.MOVE, vehicle, vehicle.position)
        # No need to send action if it is idle
        if possible_actions[0] != idle_action:
            return possible_actions[0]
        return None

    def __get_possible_actions(self, actor: Vehicle) -> list[Action]:
        actions = self.actions_generator(actor)
        idle_action = Action(ActionCode.MOVE, actor, actor.position)
        actions.append(idle_action)
        # Sort by action score first, than SHOOT actions have higher priority
        actions.sort(
            key=lambda x: (self.action_estimator(x), -x.action_code),
            reverse=False
        )

        return actions
