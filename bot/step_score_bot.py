from typing import Optional

from game_client.custom_typings import GameStateDictTyping, MapDictTyping
from bot.bot import Bot
from game_client.action import Action
from game_client.server_interaction import ActionCode
from game_client.vehicle import AtSpg, Vehicle
from game_client.state_hex import GSHex
from game_client.coordinates import Coords


class StepScoreBot(Bot):
    """
    Bot that uses formula to choose actions.

    :param self.game_state: BotGameState object
    """

    def __init__(self, game_map: MapDictTyping):
        super().__init__(game_map)

    def get_actions(self, game_state: GameStateDictTyping) -> list[Action]:
        actions: list[Action] = []

        self.game_state.update(game_state)
        for vehicle in self.game_state.current_player.ordered_vehicle_iter:
            action = self._get_action(vehicle)
            if action is not None:
                self.game_state.update_from_action(action)
                actions.append(action)

        return actions

    def _get_action(self, vehicle: Vehicle) -> Optional[Action]:
        possible_steps = self._get_possible_steps(vehicle)
        if possible_steps:
            return possible_steps[0]

        return None

    def _get_possible_steps(self, actor: Vehicle) -> list:
        if isinstance(actor, AtSpg):
            steps = self._get_possible_atspg_steps(actor)
        else:
            steps = self._get_possible_non_atspg_steps(actor)

        steps.sort(key=lambda step: self.get_step_score(actor, step), reverse=True)

        return steps

    def _get_step(self, actor: Vehicle, target: GSHex) -> Optional[Action]:
        if self.game_state.can_shoot(actor, target):
            return Action(
                ActionCode.SHOOT, actor, target.coords, [target.vehicle]
            )

        if self.game_state.can_move(actor, target):
            return Action(ActionCode.MOVE, actor, target.coords)

        return None

    def get_step_score(self, actor: Vehicle, step: Action):
        position: Coords = (
            step.target if step.action_code == ActionCode.MOVE else step.actor.position
        )

        close_enemies = self.get_potential_shooters(actor.position)

        ntd = len(close_enemies) / actor.hp
        dbc = 1 / (1 + position.straight_dist_to(Coords((0, 0, 0))))

        result = ntd + dbc

        if step.action_code == ActionCode.SHOOT:
            result += sum(
                enemy.max_hp * actor.damage / enemy.hp
                for enemy in step.affected_vehicles
            )

        return result
