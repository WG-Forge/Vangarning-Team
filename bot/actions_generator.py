"""
Contains class for possible steps generation.

"""

from typing import Optional

from bot.bot_game_state import BotGameState
from game_client.actions import Action
from game_client.server_interaction import ActionCode
from game_client.state_hex import GSHex
from game_client.vehicles import AtSpg, Vehicle


# pylint: disable=too-few-public-methods
# Only __call__ is needed here
class ActionsGenerator:
    """
    Provides methods for generating actions based on current game state.

    """

    def __init__(self, game_state: BotGameState):
        self.game_state = game_state

    def __call__(self, actor: Vehicle) -> list[Action]:
        """
        Generates list with all possible actions for the given actor.

        :param actor: Vehicle instance
        :return: list of all possible actions.
        """
        if isinstance(actor, AtSpg):
            return self.__get_possible_atspg_actions(actor)
        return self.__get_possible_non_atspg_actions(actor)

    def __get_possible_non_atspg_actions(self, actor: Vehicle) -> list[Action]:
        possible_actions: list[Action] = []
        for distance in actor.distances_to_check:
            for gshex in self.game_state.get_hexes_on_dist(actor.position, distance):
                possible_action = self._get_possible_action(actor, gshex)
                if possible_action is not None:
                    possible_actions.append(possible_action)

        return possible_actions

    def _get_possible_action(self, actor: Vehicle, target: GSHex) -> Optional[Action]:
        if self.game_state.can_shoot(actor, target):

            return Action(
                ActionCode.SHOOT,
                actor,
                target.coords,
                [
                    target.vehicle,
                ],
            )

        if self.game_state.can_move(actor, target):
            return Action(ActionCode.MOVE, actor, target.coords)

        return None

    def __get_possible_atspg_actions(self, actor: AtSpg) -> list[Action]:
        possible_actions: list[Action] = []
        for direction in self.game_state.get_hexes_on_dist(actor.position, 1):
            if self.game_state.can_move(actor, direction):
                possible_actions.append(
                    Action(ActionCode.MOVE, actor, direction.coords)
                )

            affected_vehicles = self.__get_atpsg_shoot_afected_vehicles(
                actor, direction
            )
            if affected_vehicles:
                possible_actions.append(
                    Action(ActionCode.SHOOT, actor, direction.coords, affected_vehicles)
                )

        return possible_actions

    def __get_atpsg_shoot_afected_vehicles(self, actor: AtSpg, direction):
        affected_vehicles: list[Vehicle] = []
        offset = actor.position.unit_vector(direction.coords)
        for distance in actor.distances_to_check:
            potential_target_coords = actor.position + (offset * distance)
            if self.game_state.game_map.are_valid_coords(potential_target_coords):
                potential_target = self.game_state.get_hex(potential_target_coords)
            else:
                continue
            if not potential_target.can_shoot_through:
                break
            if self.game_state.can_shoot(actor, potential_target):
                affected_vehicles.append(potential_target.vehicle)

        return affected_vehicles
