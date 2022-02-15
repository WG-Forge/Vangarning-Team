from time import perf_counter_ns

import hex
from bot import Bot
from game_client import BotGameState
from server_interaction import ActionCode
from settings import NEIGHBOURS_OFFSETS, HexCode
from vehicle import AtSpg, HeavyTank, LightTank, MediumTank, Spg, Vehicle


def time_ns(func):
    def wrapper(*args, **kwargs):
        a = perf_counter_ns()
        result = func(*args, **kwargs)
        b = perf_counter_ns()
        print(func.__name__, b - a)
        return result

    return wrapper


class StepScoreBot(Bot):
    """
    Bot that uses formula to choose actions.

    :param self.game_state: BotGameState object
    """

    def __init__(self, game_map: dict):
        super().__init__(game_map)
        self.game_state = BotGameState(game_map)

    def get_actions(self, game_state: dict) -> list:
        actions = []

        self.game_state.update(game_state)
        for vehicle in self.game_state.current_player_vehicles:
            action = self._get_action(vehicle)
            if action is not None:
                self.game_state.update_from_action(action)
                actions.append(action)

        return actions

    def _get_action(self, vehicle: Vehicle) -> tuple[ActionCode, int, dict]:
        possible_steps = self._get_possible_steps(vehicle)
        action = None
        if possible_steps:
            action = possible_steps[-1]
        return action

    def _get_possible_steps(self, actor: Vehicle) -> list:
        if isinstance(actor, AtSpg):
            steps = self._get_possible_atspg_steps(actor)
        else:
            steps = self._get_possible_non_atspg_steps(actor)

        steps.sort(key=lambda step: self.get_step_score(actor, step))

        return steps

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
    def _get_possible_atspg_steps(self, actor: AtSpg) -> list:
        steps = []

        for i, offset in enumerate(NEIGHBOURS_OFFSETS[0]):
            coords = hex.summarize(offset, actor.position)
            if not self.game_state.are_valid_coords(coords):
                continue

            if self.game_state.can_move(actor, coords):
                steps.append((ActionCode.MOVE, actor.pid, self._coords_to_dict(coords)))

            if self.game_state.is_enemy_tank(coords):
                steps.append(
                    (ActionCode.SHOOT, actor.pid, self._coords_to_dict(coords))
                )

            for diag_offset in range(1, 3):
                diag_coords = hex.summarize(
                    NEIGHBOURS_OFFSETS[diag_offset][diag_offset + 1 * i],
                    actor.position,
                )
                if not self.game_state.are_valid_coords(coords):
                    break

                if self.game_state.get_hex_value(coords) == HexCode.OBSTACLE:
                    break

                if self.game_state.is_enemy_tank(diag_coords):
                    steps.append(
                        (ActionCode.SHOOT, actor.pid, self._coords_to_dict(coords))
                    )

        return steps

    def _generate_valid_neighbours_coords(self, position, distance) -> list:
        result = []
        for offset in NEIGHBOURS_OFFSETS[distance - 1]:
            coords = hex.summarize(offset, position)
            if self.game_state.are_valid_coords(coords):
                result.append(coords)

        return result

    def _coords_to_dict(self, coords: tuple[int, int, int]):
        x, y, z = coords
        return {"x": x, "y": y, "z": z}

    def _get_step(self, actor: Vehicle, coords: tuple):
        if self.game_state.can_shoot(actor, coords):
            print("_______________________________________________________________")
            return ActionCode.SHOOT, actor.pid, self._coords_to_dict(coords)

        if self.game_state.can_move(actor, coords):
            return ActionCode.MOVE, actor.pid, self._coords_to_dict(coords)

        return None

    # TODO: awful method (Ctrl+C Ctrl+V was its sponsor), must be rewritten
    def get_step_score(self, actor: Vehicle, step: tuple):
        action, _, target = step
        position = tuple(target.values()) if action == ActionCode.MOVE else actor.position

        close_enemies = self.game_state.get_close_enemies(actor)

        ntd = (len(close_enemies) / actor.hp)
        dbc = 1 / (1 + hex.straight_dist(position, (0, 0, 0)))

        result = ntd + dbc

        if action == ActionCode.SHOOT:
            enemy = self.game_state.vehicles[
                self.game_state.vehicles_positions[position]
            ]
            enemies = []
            if not isinstance(enemy, AtSpg):
                enemies.append(enemy)
            else:
                normal = hex.normal(enemy.position, tuple(target.values()))

                for i in range(1, 4):
                    offset_coords = hex.multiply(i, normal)
                    if offset_coords in self.game_state.obstacles:
                        break

                    offset_value = self.game_state.get_hex_value(offset_coords)
                    if int(offset_value) >= 1:
                        enemies.append(self.game_state.get_vehicle(offset_value))

            result += sum(
                enemy.max_hp * actor.damage / enemy.hp for enemy in enemies
            )

        return result
