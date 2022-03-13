"""
Contains class with methods to estimate actions.

"""
from bot.bot_game_state import BotGameState
from game_client.actions import Action
from game_client.map_hexes import Base
from game_client.server_interaction import ActionCode
from game_client.vehicles import Vehicle
from utility.coordinates import Coords


class ActionEstimator:
    def __init__(self, game_state: BotGameState, weights: list[int, int, int, int]):
        self.game_state = game_state
        self.weights = weights

    def __call__(self, action: Action) -> float:
        result = 0.0
        position = (
            action.target if action.action_code == ActionCode else action.actor.position
        )

        result += self.weights[0] * self.enemy_atk_to_hp_ratio(action.actor, position)
        result += self.weights[1] * self.straight_distance_to_base(position)
        if action.action_code == ActionCode.MOVE:
            result += self.weights[2] * self.gained_capture_points(
                action.actor, action.target
            )
        if action.action_code == ActionCode.SHOOT:
            result += self.weights[2] * self.gained_capture_points(
                action.actor, action.actor.position
            )
            result += self.weights[3] * self.estimate_targets(
                action.actor.damage, action.affected_vehicles
            )

        return result

    def enemy_atk_to_hp_ratio(self, actor: Vehicle, position: Coords) -> float:
        close_enemies = self.__get_potential_shooters(position)
        return sum(enemy.damage for enemy in close_enemies) / actor.hp

    @staticmethod
    def straight_distance_to_base(position: Coords) -> float:
        return position.straight_dist_to(Coords((0, 0, 0)))

    @staticmethod
    def estimate_targets(damage: int, affected_vehicles: list[Vehicle]) -> float:
        result = 0
        for vehicle in affected_vehicles:
            hp_after_shot_modifier = damage / vehicle.hp
            if vehicle.hp <= damage:
                result += vehicle.max_hp
            result += vehicle.capture_points * hp_after_shot_modifier

        return result

    def gained_capture_points(self, actor: Vehicle, new_pos: Coords) -> int:
        prev_pos_hex_type = type(self.game_state.get_hex(actor.position).map_hex)
        new_pos_hex_type = type(self.game_state.get_hex(new_pos).map_hex)
        if prev_pos_hex_type is Base and new_pos_hex_type is not Base:
            return -actor.capture_points
        if prev_pos_hex_type is Base and new_pos_hex_type is Base:
            return 1
        return 0

    def __get_potential_shooters(self, position: Coords) -> list[Vehicle]:
        result = []
        actor_gshex = self.game_state.get_hex(position)
        for vehicle in self.game_state.vehicles.values():
            if self.game_state.can_shoot(vehicle, actor_gshex):
                result.append(vehicle)

        return result
