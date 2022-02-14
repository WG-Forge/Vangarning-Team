import struct

from server_interaction import ActionCode

# temporary solution
TANK_TYPE = {
    "light_tank": {
        "speed": 3,
        "min_shooting_range": 2,
        "max_shooting_range": 2,
    },
    "medium_tank": {
        "speed": 2,
        "min_shooting_range": 2,
        "max_shooting_range": 2,
    },
    "heavy_tank": {
        "speed": 1,
        "min_shooting_range": 1,
        "max_shooting_range": 2,
    },
    "spg": {"speed": 1, "min_shooting_range": 3, "max_shooting_range": 3},
    "at_spg": {"speed": 1, "min_shooting_range": 1, "max_shooting_range": 3},
}

TYPE_ORDER = ("spg", "light_tank", "heavy_tank", "medium_tank", "at_spg")


class Bot:
    def __init__(self, game_map):
        self.map = game_map

    def get_actions(self, game_state: dict):
        raise NotImplementedError

    def _get_vehicles_in_action_order(self, game_state: dict) -> list[tuple[int, dict]]:
        """
        Returns list of current player's vehicles corresponding to their action order.

        :param game_state: Current game state
        :return: List of tuples (vehicle_id, vehicle_info)
        """

        vehicles = game_state["vehicles"]
        player_id = game_state["current_player_idx"]

        return sorted(
            [i for i in vehicles.items() if i[1]["player_id"] == player_id],
            key=lambda vehicle: TYPE_ORDER.index(vehicle[1]["vehicle_type"]),
        )

    def _get_enemy_vehicles(self, game_state: dict) -> list[tuple[int, dict]]:
        vehicles = game_state["vehicles"]
        player_id = game_state["current_player_idx"]

        return sorted(
            [i for i in vehicles.items() if i[1]["player_id"] != player_id],
            key=lambda vehicle: TYPE_ORDER.index(vehicle[1]["vehicle_type"]),
        )

    def _dist(self, pos1, pos2):
        """
        Calculates distance between two hexes

        """
        return (
            abs(pos1["x"] - pos2["x"])
            + abs(pos1["y"] - pos2["y"])
            + abs(pos1["z"] - pos2["z"])
        ) / 2


class SimpleBot(Bot):
    def __init__(self, game_map):
        super().__init__(game_map)
        self.actions = []
        self.base = []

    def get_actions(self, game_state: dict):
        """
        Calculates action for current player's vehicles

        :param game_state: Current state of game
        :return: List of lists. Inner list structure: 0: ActionCode, 1: vehicle id, 2: data
        """
        self.actions = []

        self.base = self.map["content"]["base"].copy()

        # Gets order of vehicle actions and calculates action for every current player's vehicle
        for vehicle_id, vehicle in self._get_vehicles_in_action_order(game_state):
            # Shoot at vehicle with 1 hp
            if self.__try_shoot_any_enemy(
                vehicle_id,
                game_state["vehicles"],
                game_state["attack_matrix"],
                lambda shooter, target: target["health"] == 1,
            ):
                continue

            # Try to move towards the base or shoot at obstacle
            if self.__try_move_to_base(
                vehicle_id, game_state["vehicles"], game_state["attack_matrix"]
            ):
                continue

            # Vehicle is already on base, try to shoot any vehicle
            self.__try_shoot_any_enemy(
                vehicle_id, game_state["vehicles"], game_state["attack_matrix"]
            )

        return self.actions

    def __shoot(self, shooter_id, target_id, vehicles):
        """
        Makes a shot at target vehicle from shooter vehicle

        :param shooter_id: Shooter vehicle's id
        :param target_id: Target vehicle's id
        :param vehicles: dict of all vehicles
        """
        shooter = vehicles[shooter_id]
        target = vehicles[target_id]
        # Shooter is at_spg type
        if shooter["vehicle_type"] == "at_spg":
            dx = target["position"]["x"] - shooter["position"]["x"]
            dy = target["position"]["y"] - shooter["position"]["y"]
            dz = target["position"]["z"] - shooter["position"]["z"]
            # Shot normal
            sx = 0 if dx == 0 else dx / abs(dx)
            sy = 0 if dy == 0 else dy / abs(dy)
            sz = 0 if dz == 0 else dz / abs(dz)
            self.actions.append(
                [
                    ActionCode.SHOOT,
                    shooter_id,
                    {
                        "x": sx + shooter["position"]["x"],
                        "y": sy + shooter["position"]["y"],
                        "z": sz + shooter["position"]["z"],
                    },
                ]
            )
            # Hexes affected by shot
            aoe = [
                {
                    "x": sx + shooter["position"]["x"],
                    "y": sy + shooter["position"]["y"],
                    "z": sz + shooter["position"]["z"],
                },
                {
                    "x": 2 * sx + shooter["position"]["x"],
                    "y": 2 * sy + shooter["position"]["y"],
                    "z": 2 * sz + shooter["position"]["z"],
                },
                {
                    "x": 3 * sx + shooter["position"]["x"],
                    "y": 3 * sy + shooter["position"]["y"],
                    "z": 3 * sz + shooter["position"]["z"],
                },
            ]
            # Vehicles at affected hexes
            for vehicle in vehicles.values():
                if shooter["player_id"] == vehicle["player_id"]:
                    continue
                if vehicle["position"] in aoe:
                    vehicle["health"] -= 1
        else:
            self.actions.append([ActionCode.SHOOT, shooter_id, target["position"]])
            target["health"] -= 1

    def __try_shoot_any_enemy(
        self,
        shooter_id,
        vehicles,
        attack_matrix,
        function=lambda shooter, target: True,
    ):
        """
        Tries to shoot any enemy vehicle in the game

        :param shooter_id: id of shooter vehicle
        :param vehicles: dict of all vehicles
        :param attack_matrix:
        :param function: Optional condition
        :return: True if the shot was successful, False if not
        """

        # Gets generator for all possible targets
        shoot_targets = filter(
            lambda target_id: self.__can_shoot(
                vehicles[shooter_id], vehicles[target_id], attack_matrix
            )
            and function(vehicles[shooter_id], vehicles[target_id]),
            vehicles,
        )

        shoot_target_id = next(shoot_targets, None)
        # No possible targets found
        if shoot_target_id is None:
            return False

        self.__shoot(shooter_id, shoot_target_id, vehicles)
        return True

    def __try_move_to_base(self, vehicle_id, vehicles, attack_matrix):
        """
        Tries to move vehicle towards the base, if not possible, shoots at obstacle
        :param vehicle_id: Moving vehicle
        :param vehicles: dict of all vehicles
        :param attack_matrix:
        :return: True if action was made, False if not
        """
        vehicle = vehicles[vehicle_id]

        # Closest base hex to the vehicle

        closest_base = min(
            self.base, key=lambda base_hex: self._dist(base_hex, vehicle["position"])
        )
        self.base.remove(closest_base)

        # Vehicle is already at the base hex
        if closest_base == vehicle["position"]:
            return False

        # Finds closest reachable hex to the base hex
        closest_hex_to_base = vehicle["position"]
        min_dist = self.map["size"]
        for hex in self.__get_hexes(
            vehicle["position"], 0, TANK_TYPE[vehicle["vehicle_type"]]["speed"]
        ):
            dist = self._dist(hex, closest_base)
            if dist >= min_dist:
                continue

            hex_is_blocked = False
            for other_vehicle in vehicles.values():
                # Hex is blocked, can't shoot
                if other_vehicle["position"] == hex and not self.__can_shoot(
                    vehicle, other_vehicle, attack_matrix
                ):
                    hex_is_blocked = True
                    break

            if not hex_is_blocked:
                min_dist = dist
                closest_hex_to_base = hex

        # Found hex is blocked, shoot at blocking vehicle
        for other_vehicle_id, other_vehicle in vehicles.items():
            if other_vehicle["position"] == closest_hex_to_base:
                self.__shoot(vehicle_id, other_vehicle_id, vehicles)
                return True

        # Hex is free, vehicle moving to it
        if vehicle["position"] != closest_hex_to_base:
            self.actions.append(
                [ActionCode.MOVE, vehicle_id, closest_hex_to_base.copy()]
            )
            vehicle["position"] = closest_hex_to_base
            return True
        return False

    def __get_hexes(self, origin, min_dist, max_dist):
        """
        Generator that yields hexes at given distance from given hex

        :param origin: hex at a distance from which other hexes are generated
        :param min_dist: minimal distance from origin
        :param max_dist: maximum distance from origin
        :return:
        """
        for x in range(-max_dist, max_dist + 1):
            for y in range(
                max(-max_dist, -max_dist - x), min(max_dist + 1, max_dist - x + 1)
            ):
                z = -x - y
                hex_pos = {
                    "x": origin["x"] + x,
                    "y": origin["y"] + y,
                    "z": origin["z"] + z,
                }

                if self._dist(hex_pos, {"x": 0, "y": 0, "z": 0}) > self.map["size"]:
                    continue
                if self._dist(hex_pos, origin) < min_dist:
                    continue
                yield hex_pos

    def __can_shoot(self, shooter, target, attack_matrix):
        """
        Checks if it possible to shoot at given target

        :param shooter: Shooting vehicle
        :param target: Target vehicle
        :param attack_matrix:
        :return: True if possible, False if not
        """
        # Both vehicles belong to the same player
        if shooter["player_id"] == target["player_id"]:
            return False
        # Target is already destroyed
        if target["health"] <= 0:
            return False
        # Target out of range
        if not self.__distance_check(shooter, target):
            return False

        # Neutrality check
        return self.__neutrality_check(shooter, target, attack_matrix)

    def __distance_check(self, shooter, target):
        """
        Check if target vehicle is in shooting range of shooter vehicle

        :param shooter: Shooter vehicle
        :param target: Target vehicle
        :return: True if in range, False if not
        """
        # Regular vehicle check
        dist = self._dist(shooter["position"], target["position"])
        min_shooting_range = TANK_TYPE[shooter["vehicle_type"]]["min_shooting_range"]
        max_shooting_range = TANK_TYPE[shooter["vehicle_type"]]["max_shooting_range"]

        if not (min_shooting_range <= dist <= max_shooting_range):
            return False

        # AT_SPG range check
        if shooter["vehicle_type"] == "at_spg":
            dx = target["position"]["x"] - shooter["position"]["x"]
            dy = target["position"]["y"] - shooter["position"]["y"]
            dz = target["position"]["z"] - shooter["position"]["z"]
            if dx != 0 and dy != 0 and dz != 0:
                return False

        return True

    def __neutrality_check(self, shooter, target, attack_matrix):
        """
        Checks if shooter vehicle can't shoot at target vehicle due to neutrality rule

        :param shooter: Shooter vehicle
        :param target: Target vehicle
        :param attack_matrix:
        :return: True if shot is possible, False if not
        """
        shooter_pid = shooter["player_id"]
        target_pid = target["player_id"]

        # Shooter wasn't attacked by target on the last turn
        if shooter_pid not in attack_matrix[str(target_pid)]:
            # Target was attacked by other player on the last turn
            for player_id, prev_targets in attack_matrix.items():
                if player_id != str(shooter_pid) and target_pid in prev_targets:
                    return False
        return True
