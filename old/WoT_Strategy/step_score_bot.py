from typing import Optional

import hexes
from bot import Bot
from game_client import Action
from server_interaction import ActionCode
from settings import NEIGHBOURS_OFFSETS, HexCode, CoordsTuple
from vehicle import AtSpg, Vehicle


class StepScoreBot(Bot):
    """
    Bot that uses formula to choose actions.

    :param self.game_state: BotGameState object
    """

    def __init__(self, game_map: dict):
        super().__init__(game_map)

    def get_actions(self, game_state: dict) -> list:
        actions = []

        self.game_state.update(game_state)
        for vehicle in self.game_state.current_player_vehicles:
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

    # Will be moved to Vehicles classes
    def _get_possible_non_atspg_steps(self, actor: Vehicle) -> list:
        steps = []
        for distance in actor.distances_to_check:
            for neighbour_hex in self._generate_valid_neighbours_coords(
                actor.position, distance
            ):
                step = self._get_step(actor, neighbour_hex)
                if step is not None:
                    steps.append(step)

        return steps

    # TODO: awful method, must be rewritten
    # Will be moved to Vehicles classes
    def _get_possible_atspg_steps(self, actor: AtSpg) -> list:
        steps = []

        for neighbour in self.game_state.get_neighbours(actor.position):

            if self.game_state.can_move(actor, neighbour):
                steps.append(Action(ActionCode.MOVE, actor, neighbour))

            normal = hexes.unit_vector(actor.position, neighbour)

            affected_vehicles: list[Vehicle] = []

            for i in range(1, 4):
                target = hexes.summarize(actor.position, hexes.multiply(i, normal))
                if self.game_state.get_hex_value(target) == HexCode.OBSTACLE:
                    break
                if self.game_state.can_shoot(actor, target):
                    vehicle_id = self.game_state.get_hex_value(target)
                    affected_vehicles.append(
                        self.game_state.get_vehicle_by_id(vehicle_id)
                    )

            if affected_vehicles:
                steps.append(
                    Action(ActionCode.SHOOT, actor, neighbour, *affected_vehicles)
                )

        return steps

    def _generate_valid_neighbours_coords(self, position, distance) -> list:
        result = []
        for offset in NEIGHBOURS_OFFSETS[distance - 1]:
            coords: tuple[int, int, int] = hexes.summarize(offset, position)
            if self.game_state.are_valid_coords(coords):
                result.append(coords)

        return result

    def _get_step(self, actor: Vehicle, coords: CoordsTuple):
        if self.game_state.can_shoot(actor, coords):
            affected_vehicle = self.game_state.get_vehicle_by_id(
                self.game_state.get_hex_value(coords)
            )
            return Action(ActionCode.SHOOT, actor, coords, affected_vehicle)

        if self.game_state.can_move(actor, coords):
            return Action(ActionCode.MOVE, actor, coords)

        return None

    def get_step_score(self, actor: Vehicle, step: Action):
        position = (
            step.target if step.action_code == ActionCode.MOVE else step.actor.position
        )

        close_enemies = self.game_state.get_close_enemies(actor.position)

        ntd = len(close_enemies) / actor.hp
        dbc = 1 / (1 + hexes.straight_dist(position, (0, 0, 0)))

        result = ntd + dbc

        if step.action_code == ActionCode.SHOOT:
            result += sum(
                enemy.max_hp * actor.damage / enemy.hp
                for enemy in step.affected_vehicles
            )

        return result
