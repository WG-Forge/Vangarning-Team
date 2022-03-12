from typing import Iterator

from game_client.game_state import GameState
from game_client.custom_typings import MapDictTyping
from game_client.state_hex import GSHex
from utility.coordinates import Coords
from game_client.action import Action
from game_client.server_interaction import ActionCode
from game_client.vehicle import Vehicle
from game_client.map_hexes import Catapult, LightRepair, HardRepair, Base

DIRECTIONS = (
    Coords((1, -1, 0)),
    Coords((1, 0, -1)),
    Coords((0, 1, -1)),
    Coords((-1, 1, 0)),
    Coords((-1, 0, 1)),
    Coords((0, -1, 1)),
)


class BotGameState(GameState):
    def __init__(self, game_map: MapDictTyping):
        super().__init__(game_map)

    def update_from_action(self, action: Action) -> None:
        if action.action_code == ActionCode.MOVE:
            self.__apply_move_action(action)

        if action.action_code == ActionCode.SHOOT:
            self.__apply_shoot_action(action)

        if action.action_code == ActionCode.TURN:
            self.__apply_turn_action()

    def get_hexes_on_dist(self, position: Coords, dist: int) -> Iterator[GSHex]:
        """
        Creates iterator with hexes at given distance from the position.

        """
        if dist == 0:
            yield self.get_hex(position)

        else:
            # Starting from bottom-left diagonal hex
            hex_on_dist = position + DIRECTIONS[4] * dist
            for i in range(6):  # going anticlockwise
                for j in range(dist):
                    if self.game_map.are_valid_coords(hex_on_dist):
                        yield hex_on_dist
                    hex_on_dist = hex_on_dist + DIRECTIONS[i]

    def is_hex_reachable(self, actor: Vehicle, target: GSHex) -> bool:

        """
        Tells if there is any path from position to target with given max_len.

        """
        if actor.position.straight_dist_to(target.coords) > actor.speed_points:
            return False

        visited: set[Coords] = set()
        visited.add(actor.position)
        fringes: list[list[Coords]] = [[actor.position]]

        for k in range(1, actor.speed_points + 1):
            fringes.append([])
            for visited_hex in fringes[k - 1]:
                for neighbour in self.get_hexes_on_dist(visited_hex, 1):
                    if neighbour == target:
                        return True
                    if neighbour not in visited and neighbour.can_go_through:
                        visited.add(neighbour.coords)
                        fringes[k].append(neighbour.coords)

        return False

    def can_move(self, actor: Vehicle, target: GSHex) -> bool:
        """
        Tells if actor can move to a given position.

        """
        if not target.can_stay(actor):
            return False

        return self.is_hex_reachable(actor, target)

    def can_shoot(self, actor: Vehicle, target: GSHex) -> bool:
        if not actor.target_in_shoot_range(target.coords):
            return False
        if target.vehicle is None:
            return False
        actor_player = self.players[actor.player_id]
        if target.vehicle.player_id not in actor_player.can_attack_ids:
            return False
        if target.vehicle.hp <= 0:
            return False
        if actor.shoots_flat and self.__shooting_path_has_obstacles(
                actor.position, target.coords
        ):
            return False

        return True

    def __shooting_path_has_obstacles(
            self, position: Coords, target: Coords
    ) -> bool:
        """
        Tells if there is something on the shot line.

        Has reason to be used only if the shot line is a straight line
        (dx, dy, or dz between position and target equals 0).
        """
        normal = position.unit_vector(target)
        for i in range(1, position.straight_dist_to(target) + 1):
            if not self.get_hex(position + normal * i).can_shoot_through:
                return True
        return False

    def __apply_shoot_action(self, action: Action) -> None:
        action.actor.shoot()
        acting_player = self.players[action.actor.player_id]
        for vehicle in action.affected_vehicles:
            acting_player.win_points["kill"] += vehicle.receive_damage(
                action.actor.damage)

    def __apply_move_action(self, action: Action) -> None:
        self.__update_vehicle_pos(action.actor, action.target)

    def __apply_turn_action(self) -> None:
        for vehicle in self.vehicles.values():
            gshex = self.get_hex(vehicle.position)
            player = self.players[vehicle.player_id]
            map_hex_type = type(gshex.map_hex)

            # Send back to spawn
            if vehicle.hp <= 0:
                self.__update_vehicle_pos(vehicle, vehicle.spawn_position)
                vehicle.hp = vehicle.max_hp

            # Repair vehicle
            elif map_hex_type in (LightRepair, HardRepair):
                if vehicle.__class__ in gshex.map_hex.served_classes:
                    vehicle.hp = vehicle.max_hp

            # Apply shooting range bonus
            elif map_hex_type is Catapult:
                vehicle.shoot_range_bonus = gshex.map_hex.use()

            # Add/remove capture points
            if map_hex_type is Base:
                vehicle.capture_points += 1
                player.win_points["capture"] += 1
            else:
                vehicle.capture_points = 0
                player.win_points["capture"] -= vehicle.capture_points

    def __update_vehicle_pos(self, vehicle: Vehicle, new_position: Coords) -> None:
        del (self.vehicles[vehicle.position])
        self.vehicles[new_position] = vehicle
        vehicle.update_position(new_position)
