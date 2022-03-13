from typing import Optional

from bot.actions_generator import ActionsGenerator
from bot.bot import Bot
from game_client.actions import Action
from game_client.server_interaction import ActionCode
from game_client.vehicles import Vehicle
from utility.coordinates import Coords
from utility.custom_typings import GameStateDictTyping, MapDictTyping


class StepScoreBot(Bot):
    """
    Bot that uses formula to choose actions.

    :param self.game_state: BotGameState object
    """

    def __init__(self, game_map: MapDictTyping):
        super().__init__(game_map)
        self.actions_generator = ActionsGenerator(self.game_state)

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
        possible_steps = self.__get_possible_actions(vehicle)
        if possible_steps:
            return possible_steps[0]

        return None

    def __get_possible_actions(self, actor: Vehicle) -> list[Action]:
        steps = self.actions_generator(actor)

        steps.sort(key=lambda step: self.get_step_score(actor, step), reverse=True)

        return steps

    def __get_potential_shooters(self, actor: Vehicle) -> list[Vehicle]:
        result = []
        actor_gshex = self.game_state.get_hex(actor.position)
        for vehicle in self.game_state.vehicles.values():
            if self.game_state.can_shoot(vehicle, actor_gshex):
                result.append(vehicle)

        return result

    def get_step_score(self, actor: Vehicle, step: Action):
        position: Coords = (
            step.target if step.action_code == ActionCode.MOVE else step.actor.position
        )

        close_enemies = self.__get_potential_shooters(actor)

        ntd = len(close_enemies) / actor.hp
        dbc = 1 / (1 + position.straight_dist_to(Coords((0, 0, 0))))

        result = ntd + dbc

        if step.action_code == ActionCode.SHOOT:
            result += sum(
                enemy.max_hp * actor.damage / enemy.hp
                for enemy in step.affected_vehicles
            )

        return result
