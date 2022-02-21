from queue import PriorityQueue
from typing import Union

import hex
from bot import Bot
from server_interaction import ActionCode, GameSession
from settings import NEIGHBOURS_OFFSETS, TYPE_ORDER, HexCode
from vehicle import AtSpg, HeavyTank, LightTank, MediumTank, Spg, Vehicle

TYPES_TO_CLASSES = {
    "at_spg": AtSpg,
    "heavy_tank": HeavyTank,
    "light_tank": LightTank,
    "medium_tank": MediumTank,
    "spg": Spg,
}


class Action:
    def __init__(
        self,
        action_code: ActionCode,
        actor: Vehicle,
        target: tuple[int, int, int],
        *affected_vehicles: Vehicle,
    ):
        self.action_code: ActionCode = action_code
        self.actor: Vehicle = actor
        self.target: tuple[int, int, int] = target
        self.affected_vehicles = affected_vehicles

    @property
    def server_format(self):
        return self.action_code, self.actor.pid, hex.tuple_to_dict(self.target)


# TODO: Replace a_star_search in can_move method to smth faster
#  but less universal

# TODO: Use logging instead of printing in game_loop function
# TODO: Add going back to spawn at the next turn if hp == 0 to
#  update_from_action
# TODO: Try to prune vehicles, vehicles to players into one data structure
# TODO: Maybe it will be a good idea to change NEIGHBOURS_OFFSETS to smth else


class BotGameState:
    """
    Keeps info about game map and state that can be useful for bot.

    """

    def __init__(self, game_map: dict):
        """
        :param game_map: MAP response from the server
        """
        # Map info
        self.map_radius: int = game_map["size"]
        self.map_name: str = game_map["name"]
        self.base, self.obstacles = self.__parse_map_content(game_map)
        self.spawn_positions: set = set()

        # Game state info
        self.is_game_state_populated = False
        self.players: list[dict] = []
        self.num_turns: int = -1
        self.current_turn: int = -1
        self.current_player_idx: int = -1
        self.win_points: dict[int, dict] = {}
        self.vehicles: dict[int, Vehicle] = {}
        self.vehicles_to_players: dict[int, list[int]] = {}
        self.vehicles_positions: dict[tuple, int] = {}
        self.attack_matrix: dict[int, list] = {}

    # Update-or-create methods
    def update(self, game_state: dict) -> None:
        """
        Updates instance from game_state.

        :param game_state: GAME_STATE response from the server
        :return: None
        """
        if not self.is_game_state_populated:
            self.__populate_game_state(game_state)
        else:
            self.__update_vehicles(game_state["vehicles"])

        self.current_turn = game_state["current_turn"]
        self.current_player_idx = game_state["current_player_idx"]
        self.win_points = game_state["win_points"]
        self.attack_matrix = {
            int(player_id): value
            for player_id, value in game_state["attack_matrix"].items()
        }

    def update_from_action(self, action: Action) -> None:
        """
        Updates instance from given action

        :param action: tuple(ActionCode, actor_id, target)
        :return: None
        """
        if action.action_code == ActionCode.MOVE:
            del self.vehicles_positions[action.actor.position]
            action.actor.position = action.target
            self.vehicles_positions[action.actor.position] = action.actor.pid

        elif action.action_code == ActionCode.SHOOT:
            for enemy in action.affected_vehicles:
                enemy.hp -= action.actor.damage

    def __populate_game_state(self, game_state: dict) -> None:
        """
        Populates constant info about the game and creates vehicles.

        Only called when self.update is called for the first time.
        :param game_state: GAME_STATE response from the server
        :return: None
        """
        self.num_turns = game_state["num_turns"]
        self.players = [
            player for player in game_state["players"] if not player["is_observer"]
        ]
        for player in self.players:
            self.vehicles_to_players[int(player["idx"])] = []

        self.__create_vehicles(self.__get_order_sorted_vehicles(game_state["vehicles"]))

        self.is_game_state_populated = True

    def __get_order_sorted_vehicles(self, vehicles: dict[str, dict]) -> list:
        """
        Sorts vehicles by type in the following order: SPG, LT, HT, MT, AT SPG.

        :param vehicles: dict with vehicle id as key and its' data as value
        :return: sorted list of tuples (vehicle_id, vehicle_data)
        """
        return sorted(
            vehicles.items(),
            key=lambda vehicle: TYPE_ORDER.index(vehicle[1]["vehicle_type"]),
        )

    def __create_vehicles(self, vehicles: list[tuple[str, dict]]) -> None:
        """
        Creates Vehicle objects and stores info about them in instance's attributes.

        :param vehicles: sorted by step order list of tuples (vehicle_id, vehicle_data)
        :return: None
        """
        for vid, vehicle in vehicles:
            vehicle_id = int(vid)
            vehicle_obj = TYPES_TO_CLASSES[vehicle["vehicle_type"]](
                player_id=vehicle["player_id"],
                pid=vid,
                hp=vehicle["health"],
                spawn_position=hex.dict_to_tuple(vehicle["spawn_position"]),
                position=hex.dict_to_tuple(vehicle["position"]),
                capture_points=vehicle["capture_points"],
            )
            self.vehicles_to_players[vehicle_obj.player_id].append(vehicle_id)
            self.vehicles_positions[vehicle_obj.position] = vehicle_id
            self.vehicles[vehicle_id] = vehicle_obj
            self.spawn_positions.add(vehicle_obj.spawn_position)

    def __update_vehicles(self, vehicles: dict[str, dict]) -> None:
        """
        Updates information about vehicles.

        :param vehicles: "vehicles" part of GAME_STATE response from the server
        :return: None
        """
        for vid, vehicle in vehicles.items():
            vehicle_id = int(vid)
            del self.vehicles_positions[self.vehicles[vehicle_id].position]
            self.vehicles[vehicle_id].update(vehicle)
            self.vehicles_positions[tuple(vehicle["position"].values())] = vehicle_id

    def __parse_map_content(self, game_map: dict) -> tuple[set[tuple], set[tuple]]:
        """
        Puts info about all game content to instances attributes.

        :param game_map: MAP server response
        :return: two sets with hexes corresponding to exact content type
        """
        obstacles = set(tuple(i.values()) for i in game_map["content"]["obstacle"])
        base = set(tuple(i.values()) for i in game_map["content"]["base"])

        return base, obstacles

    def a_star_search(self, start, target):
        frontier = PriorityQueue()
        frontier.put(start, False)
        came_from = {start: None}
        cost_so_far = {start: 0}

        while not frontier.empty():
            current = frontier.get()

            if current == target:
                break

            for next_hex in self.__get_neighbours(current):
                new_cost = cost_so_far[current] + (
                    1 if next_hex not in self.obstacles else 2000000
                )
                if next_hex not in cost_so_far or new_cost < cost_so_far[next_hex]:
                    cost_so_far[next_hex] = new_cost
                    priority = new_cost + (
                        sum(map(lambda x: x[0] - x[1], zip(next_hex, target)))
                    )
                    frontier.put(next_hex, priority)
                    came_from[next_hex] = current

        return cost_so_far[target]

    def __get_neighbours(self, coords: tuple[int, int, int]):
        """
        Help function for A* search returns all 6 closest neighbours.

        :param coords:
        :return:
        """
        neighbours = []

        for offset in NEIGHBOURS_OFFSETS[0]:
            neighbour = hex.summarize(coords, offset)
            if self.are_valid_coords(neighbour):
                neighbours.append(neighbour)

        return neighbours

    # Will be moved to Vehicles classes
    def _can_reach(
        self, max_len: int, start: tuple[int, int, int], target: tuple[int, int, int]
    ) -> bool:
        """
        Tells if there is a path from start to finish with given length

        :param max_len: max length of the path
        :param start: start hex
        :param target: finish hex
        :return:
        """
        if hex.straight_dist(start, target) > max_len:
            return False

        return self.a_star_search(start, target) <= max_len

    def are_valid_coords(self, coords: tuple[int, int, int]) -> bool:
        """
        Tells if hex with given coordinates is in map boundaries.
        :param coords:
        :return:
        """
        return max(map(abs, coords)) < self.map_radius

    def get_vehicle_by_id(self, vehicle_id: int) -> Vehicle:
        """
        Returns vehicle with given id.

        :param vehicle_id:
        :return:
        """
        return self.vehicles[vehicle_id]

    def is_vehicle(self, hex_value: int) -> bool:
        """
        Tells if given hex value corresponds to any vehicle.

        :param hex_value:
        :return:
        """
        return hex_value >= 1

    def is_enemy_tank(self, position: tuple[int, int, int]) -> bool:
        """
        Tells if object at the given hex is enemy tank for current player.

        :param position: position of hex
        :return:
        """
        hex_value = self.get_hex_value(position)
        return (
            self.is_vehicle(hex_value)
            and hex_value not in self.vehicles_to_players[self.current_player_idx]
        )

    # Will be moved to Vehicles classes
    def can_move(self, actor: Vehicle, target: tuple[int, int, int]) -> bool:
        """
        Tells if actor can move to given position.

        :param actor: vehicle that needs to be checked
        :param target: coordinates of target hex
        :return: can actor move or not
        """
        # target is someone else's spawn position
        if target in self.spawn_positions and target != actor.spawn_position:
            return False
        # target is obstacle
        if target in self.obstacles:
            return False
        # target is occupied by another vehicle
        if int(self.get_hex_value(target)) >= 1:
            return False

        return self._can_reach(actor.speed_points, actor.position, target)

    # Will be moved to Vehicles classes
    def can_shoot(self, actor: Vehicle, coords: tuple[int, int, int]) -> bool:
        """
        Tells if actor can and have reason to shoot given hex.

        :param actor: vehicle that needs to be checked
        :param coords: coordinates of target hex
        :return: can actor shoot or not
        """
        hex_status = self.get_hex_value(coords)
        if not self.is_vehicle(hex_status):
            return False

        if not actor.is_target_in_shooting_range(coords):
            return False

        target_vehicle = self.get_vehicle_by_id(hex_status)
        if target_vehicle in self.current_player_vehicles:
            return False
        if target_vehicle.hp == 0:
            return False

        return self.__neutrality_check(actor, target_vehicle)

    def __neutrality_check(self, actor: Vehicle, target_vehicle: Vehicle):
        if actor.player_id in self.attack_matrix[target_vehicle.player_id]:
            return True

        for player, attacked_players in self.attack_matrix.items():
            if player not in (actor.player_id, target_vehicle.player_id):
                if target_vehicle.player_id in attacked_players:
                    return False

        return True

    def get_hex_value(self, coords: tuple[int, int, int]) -> Union[HexCode, int]:
        """
        Returns numeric representation of object at given hex.

        -2 - obstacle
        -1 - base
        0 - empty hex
        1 to 15 - vehicles

        :param coords: coordinates of a hex
        :return: numeric representation of object at given hex
        """
        try:
            return self.vehicles_positions[coords]
        except KeyError:
            if coords in self.base:
                return HexCode.BASE
            elif coords in self.obstacles:
                return HexCode.OBSTACLE
            else:
                return HexCode.EMPTY

    def get_close_enemies(self, position: tuple[int, int, int]) -> list[Vehicle]:
        """
        Returns enemies which can shoot hex with given position.

        :param position: coordinates of hex
        :return: list of enemies
        """
        enemies = []
        for dist in NEIGHBOURS_OFFSETS:
            for offset in dist:
                hex_value = self.get_hex_value(hex.summarize(position, offset))
                if int(hex_value) >= 1:
                    enemy = self.vehicles[hex_value]
                    if self.can_shoot(enemy, position):
                        enemies.append(enemy)

        return enemies

    @property
    def current_player_vehicles(self) -> list[Vehicle]:
        return [
            self.vehicles[i] for i in self.vehicles_to_players[self.current_player_idx]
        ]


def game_loop(bot: Bot, game: GameSession):
    """
    Plays the given game with the given bot.

    :param bot:
    :param game:
    :return:
    """
    while True:
        game_state = game.game_state()

        if game_state["finished"]:
            print("You won" if game_state["winner"] == game.player_id else "You lost")
            print(f"Winner: {game_state['winner']}")
            break

        if game_state["current_player_idx"] == game.player_id:
            print(
                f'Round: {game_state["current_turn"]}, ' f"player: {game.player_name}"
            )
            for action in bot.get_actions(game_state):
                game.action(*action.server_format)
                print(
                    f"  Action: "
                    f'{"shoot" if action.action_code == ActionCode.SHOOT else "move"}'
                    f" Actor: {action.actor} Target: {action.target}"
                )

        game.turn()
