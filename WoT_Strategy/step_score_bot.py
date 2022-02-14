import struct
from queue import PriorityQueue

from bot import TANK_TYPE, TYPE_ORDER, Bot
from server_interaction import ActionCode
from settings import HexCode
from vehicle import AtSpg, HeavyTank, LightTank, MediumTank, Spg, Vehicle

NEIGHBOURS_OFFSETS = (
    (
        (0, -1, 1),
        (1, -1, 0),
        (1, 0, -1),
        (0, 1, -1),
        (-1, 1, 0),
        (-1, 0, 1),
    ),
    (
        (0, -2, 2),
        (1, -2, 1),
        (2, -2, 0),
        (2, -1, -1),
        (2, 0, -2),
        (1, 1, -2),
        (0, 2, -2),
        (-1, 2, -1),
        (-2, 2, 0),
        (-2, 1, 1),
        (-2, 0, 2),
        (-1, -1, 2),
    ),
    (
        (0, -3, 3),
        (1, -3, 2),
        (2, -3, 1),
        (3, -3, 0),
        (3, -2, -1),
        (3, -1, -2),
        (3, 0, -3),
        (2, 1, -3),
        (1, 2, -3),
        (0, 3, -3),
        (-1, 3, -2),
        (-2, 3, -1),
        (-3, 3, 0),
        (-3, 2, 1),
        (-3, 1, 2),
        (-3, 0, 3),
        (-2, -1, 3),
        (-1, -2, 3),
    ),
)

TYPES_TO_CLASSES = {
    "at_spg": AtSpg,
    "heavy_tank": HeavyTank,
    "light_tank": LightTank,
    "medium_tank": MediumTank,
    "spg": Spg,
}


class StepScoreBot(Bot):
    """
    Bot that uses formula to choose actions.

    :param self.map_radius: radius of the map
    :param self.dict_game_state: map stored in a format: (x, y, z): item_id
    :param self.game_state: game state in a server format
    :param self.vehicles_to_players: dict of players' ids as keys
        and dict[vehicle_id, Vehicle] as values
    :param self.spawn_positions: dict of spawn positions with vehicle_id as key
        and (x, y, z) as value
    """

    def __init__(self, game_map: dict):
        super().__init__(game_map)
        self.map_radius: int = game_map["size"]
        self.dict_game_state: dict = self._map_to_dict(game_map)
        self.game_state: dict = {}
        self.vehicles_to_players: dict = {}
        self.spawn_positions: dict[str, tuple[int, int, int]] = {}

    def _map_to_dict(self, game_map) -> dict:
        """
        Converts map into dict with tuples (x, y, z) as keys and int as values.

        values:
        -2 obstacle
        -1 base
        0 empty hex
        1-15 vehicles ids

        Even though, map in a form of a dict takes 9312 bytes
        (if all hexes are listed) instead of 248 bytes in a list for
        a map with radius equals to 11, time to pick random value is
        on average more than two times faster: 347 ns in list
        and 158 ns in dict.

        :param game_map:
        :return:
        """
        result = {}
        for map_hex in self.map["content"]["base"]:
            result[map_hex.values()] = HexCode.BASE

        for map_hex in self.map["content"]["obstacle"]:
            result[map_hex.values()] = HexCode.OBSTACLE

        return result

    def _get_order_sorted_vehicles(
        self, vehicles: dict[str, dict]
    ) -> list[tuple[str, dict]]:
        """
        Sorts vehicles by type in the following order: SPG, LT, HT, MT, AT SPG.

        :param vehicles: dict with vehicle id as key and its' data as value
        :return: sorted list of tuples (vehicle_id, vehicle_data)
        """
        return sorted(
            vehicles.items(),
            key=lambda vehicle: TYPE_ORDER.index(vehicle[1]["vehicle_type"]),
        )

    def _create_vehicles(self, vehicles: list[tuple[str, dict]]) -> None:
        """
        Creates Vehicle objects and stores in self.vehicles_to_players.

        :param vehicles: sorted by step order list of tuples (vehicle_id, vehicle_data)
        :return: None
        """
        for vid, vehicle in vehicles:
            vehicle_obj = TYPES_TO_CLASSES[vehicle["vehicle_type"]](
                vehicle["player_id"],
                vid,
                vehicle["health"],
                tuple(vehicle["spawn_position"].values()),
                tuple(vehicle["position"].values()),
                vehicle["capture_points"],
            )
            self.vehicles_to_players[vehicle_obj.player_id][vid] = vehicle_obj
            self.dict_game_state[vehicle_obj.position] = vid
            self.spawn_positions[vid] = vehicle["spawn_position"]

    def _update_vehicles(self, vehicles: dict[str, dict]) -> None:
        """
        Updates information in self.vehicles_to_players.

        :param vehicles: "vehicles" part of GAME_STATE response from the server
        :return: None
        """
        if self.vehicles_to_players:
            for vid, vehicle in self.game_state["vehicles"].items():
                vehicle_obj: Vehicle = self.vehicles_to_players[vehicle["player_id"]][
                    vid
                ]

                self.dict_game_state[vehicle_obj.position] = 0
                new_pos = tuple(vehicles[vid]["position"].values())
                self.dict_game_state[new_pos] = vid
                vehicle_obj.update(vehicle)

    def _update_game_state(self, game_state: dict) -> None:
        """
        Updates self.game_state, self.dict_game_state and self.vehicles_to_players from game_state.

        :param game_state: GAME_STATE response from the server
        :return: None
        """
        if not self.game_state:
            for player in game_state["players"]:
                self.vehicles_to_players[player["idx"]] = {}
            self._create_vehicles(
                self._get_order_sorted_vehicles(game_state["vehicles"])
            )

        else:
            self._update_vehicles(game_state["vehicles"])
        self.game_state = game_state

    def get_actions(self, game_state: dict) -> list:
        actions = []

        self._update_game_state(game_state)
        for vehicle in self.vehicles_to_players[
            game_state["current_player_idx"]
        ].values():
            actions.append(self._get_action(vehicle))

        return actions

    def _get_action(self, vehicle: Vehicle) -> tuple[ActionCode, int, dict]:
        return self._get_all_possible_steps(vehicle)[0]

    def _are_valid_coords(self, coords):
        return max(map(abs, coords)) < self.map_radius

    def _get_all_possible_steps(self, actor: Vehicle) -> list:
        steps = []
        if isinstance(actor, AtSpg):
            steps = self._get_all_possible_atspg_steps(actor)

        else:
            for distance in actor.distances_to_check:
                for offset in NEIGHBOURS_OFFSETS[distance - 1]:
                    coords = tuple(map(sum, zip(offset, actor.position)))
                    if self._are_valid_coords(coords):
                        step = self._get_step(actor, coords)
                        if step is not None:
                            steps.append(step)

        # steps.sort(key=lambda step: self.get_step_score(actor, step))

        return steps

    def _get_all_possible_atspg_steps(self, actor: AtSpg) -> list:
        actions = []
        for i, offset in enumerate(NEIGHBOURS_OFFSETS[0]):
            coords = tuple(map(sum, zip(offset, actor.position)))
            if not self._are_valid_coords(coords):
                continue

            try:
                hex_status = self.dict_game_state[coords]
            except KeyError:
                hex_status = HexCode.EMPTY

            if hex_status == HexCode.EMPTY:
                actions.append(
                    (ActionCode.MOVE, actor.pid, self._coords_to_dict(coords))
                )

            if self._is_enemy_tank(self._get_hex_value(coords)):
                actions.append(
                    (ActionCode.SHOOT, actor.pid, self._coords_to_dict(coords))
                )

            for diag_offset in range(1, 3):
                diag_coords = tuple(
                    map(
                        sum,
                        zip(
                            NEIGHBOURS_OFFSETS[diag_offset][diag_offset + 1 * i],
                            actor.position,
                        ),
                    )
                )
                if not self._are_valid_coords(coords):
                    break

                if self._is_enemy_tank(self._get_hex_value(diag_coords)):
                    actions.append(
                        (ActionCode.SHOOT, actor.pid, self._coords_to_dict(coords))
                    )

        return actions

    def _coords_to_dict(self, coords: tuple[int, int, int]):
        x, y, z = coords
        return {"x": x, "y": y, "z": z}

    def _get_neighbours(self, coords):
        neighbours = []

        for offset in NEIGHBOURS_OFFSETS[0]:
            neighbour = tuple(map(sum, zip(coords, offset)))
            if self._are_valid_coords(neighbour):
                neighbours.append(neighbour)

        return neighbours

    def _get_hex_value(self, coords):
        try:
            hex_status = self.dict_game_state[coords]
        except KeyError:
            hex_status = HexCode.EMPTY

        return hex_status

    def _can_reach(self, max_len, start, target):
        frontier = PriorityQueue()
        frontier.put(start, False)
        came_from = {start: None}
        cost_so_far = {start: 0}

        while not frontier.empty():
            current = frontier.get()

            if current == target:
                break

            for next in self._get_neighbours(current):
                new_cost = cost_so_far[current] + (
                    1 if self._get_hex_value(next) != -2 else 2000000
                )
                if next not in cost_so_far or new_cost < cost_so_far[next]:
                    cost_so_far[next] = new_cost
                    priority = new_cost + (
                        sum(map(lambda x: x[0] - x[1], zip(next, target)))
                    )
                    frontier.put(next, priority)
                    came_from[next] = current

        return cost_so_far[target] <= max_len

    def _get_step(self, actor: Vehicle, coords: tuple):
        try:
            hex_status = self.dict_game_state[coords]
        except KeyError:
            hex_status = HexCode.EMPTY

        if hex_status == HexCode.EMPTY:
            if self._can_reach(actor.speed_points, actor.position, coords):
                return ActionCode.MOVE, actor.pid, self._coords_to_dict(coords)

        if self._is_enemy_tank(hex_status) and actor.is_target_in_shooting_range(
            coords
        ):
            return ActionCode.SHOOT, actor.pid, self._coords_to_dict(coords)

        return None

    def _is_enemy_tank(self, hex_id):
        return (
            int(hex_id) >= 1
            and hex_id
            not in self.vehicles_to_players[self.game_state["current_player_idx"]]
        )

    def get_step_score(self, actor: Vehicle, step: bytes):
        step = struct.unpack("<bb3b3b", step)
        position = step[2:5]
        close_enemies = get_close_enemies(position)

        result = (len(close_enemies) / actor.health_points) + (
            1 / (1 + get_dist_to_base(position))
        )
        if step[0] == ActionCode.SHOOT:
            result += sum(
                enemy["max_hp"] * actor.damage / enemy["health"] for enemy in step[5:8]
            )

        return result
