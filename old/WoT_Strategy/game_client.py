"""
Contains class for Game state and functions to play the game.
"""
from typing import Iterator, Union

import hexes
from server_interaction import ActionCode, GameSession
from settings import (NEIGHBOURS_OFFSETS, TYPE_ORDER, CoordsDict, CoordsTuple,
                      HexCode)
from vehicle import AtSpg, HeavyTank, LightTank, MediumTank, Spg, Vehicle

TYPES_TO_CLASSES = {
    "at_spg": AtSpg,
    "heavy_tank": HeavyTank,
    "light_tank": LightTank,
    "medium_tank": MediumTank,
    "spg": Spg,
}


class Action:
    """
    Class containing information and methods for game action.
    """

    def __init__(
        self,
        action_code: ActionCode,
        actor: Vehicle,
        target: CoordsTuple,
        *affected_vehicles: Vehicle,
    ):
        self.action_code: ActionCode = action_code
        self.actor: Vehicle = actor
        self.target: CoordsTuple = target
        self.__affected_vehicles = affected_vehicles

    @property
    def server_format(self) -> tuple[ActionCode, int, CoordsDict]:
        """
        Returns action in server format: ActionCode + actor id + target hex.
        """
        return self.action_code, self.actor.pid, hexes.tuple_to_dict(self.target)

    @property
    def affected_vehicles(self):
        """
        Returns list of affected vehicles objects.
        """
        return self.__affected_vehicles


class GameMap:
    """
    Contains static information about game map.


    """

    def __init__(self, game_map: dict):
        self.map_radius: int = game_map["size"]
        self.map_name: str = game_map["name"]
        self.base: list[CoordsTuple] = ...
        self.obstacles = ...
        self.light_repairs: list[CoordsTuple] = ...
        self.hard_repairs: list[CoordsTuple] = ...
        self.catapults: list[CoordsTuple] = ...
        self.spawn_positions: list[CoordsTuple] = []

    def is_obstacle(self, position: CoordsTuple):
        return position in self.obstacles

    def is_base(self, position: CoordsTuple):
        return position in self.base

    def is_light_repair(self, position: CoordsTuple):
        return position in self.light_repairs

    def is_hard_repair(self, position: CoordsTuple):
        return position in self.hard_repairs

    def is_catapult(self, position: CoordsTuple):
        return position in self.catapults

    def is_spawn_position(self, position: CoordsTuple):
        return position in self.spawn_positions

    def are_valid_coords(self, coords: CoordsTuple) -> bool:
        """
        Tells if hex with given coordinates is in map boundaries.

        """
        return max(map(abs, coords)) < self.map_radius

    def get_hexes_on_dist(
        self, position: CoordsTuple, dist: int
    ) -> Iterator[CoordsTuple]:
        """
        Creates iterator with hexes at given distance from the position.

        """
        return filter(
            lambda pos: self.are_valid_coords(pos), hexes.get_ring(position, dist)
        )


class BotGameState:
    """
    Keeps info about game map and state that can be useful for bot.

    """

    def __init__(self, game_map: dict):
        """
        :param game_map: MAP response from the server
        """
        self.map = GameMap(game_map)

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
                spawn_position=hexes.dict_to_tuple(vehicle["spawn_position"]),
                position=hexes.dict_to_tuple(vehicle["position"]),
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
            if self.vehicles[vehicle_id].position in self.vehicles_positions:
                del self.vehicles_positions[self.vehicles[vehicle_id].position]
            self.vehicles[vehicle_id].update(vehicle)
            self.vehicles_positions[tuple(vehicle["position"].values())] = vehicle_id

    def get_hex_value(self, coords: CoordsTuple) -> Union[HexCode, int]:
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
            if coords in self.obstacles:
                return HexCode.OBSTACLE
            return HexCode.EMPTY

    def get_vehicle_by_id(self, vehicle_id: int) -> Vehicle:
        """
        Returns vehicle with given id.

        """
        return self.vehicles[vehicle_id]

    def is_vehicle(self, position: CoordsTuple) -> bool:
        """
        Tells if given hex value corresponds to any vehicle.

        """
        return position in self.vehicles_positions

    def is_enemy_vehicle(self, position: CoordsTuple) -> bool:
        """
        Tells if object at the given hex is enemy tank for current player.

        :param position: position of hex
        :return:
        """
        if not self.is_vehicle(position):
            return False
        if (
            self.get_hex_value(position)
            not in self.vehicles_to_players[self.current_player_idx]
        ):
            return True

        return False

    def can_move(self, actor: Vehicle, target: CoordsTuple) -> bool:
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
        if self.is_vehicle(target):
            return False

        return self.is_hex_reachable(actor, target)

    def can_shoot(self, actor: Vehicle, target: CoordsTuple) -> bool:
        """
        Tells if actor can and have reason to shoot given hex.

        :param actor: vehicle that needs to be checked
        :param target: coordinates of target hex
        :return: can actor shoot or not
        """
        if not self.is_vehicle(target):
            return False

        if not actor.target_in_shooting_range(target, self.obstacles):
            return False

        target_vehicle = self.get_vehicle_by_id(self.get_hex_value(target))
        if target_vehicle in self.current_player_vehicles:
            return False
        if target_vehicle.hp <= 0:
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

    def get_close_enemies(self, position: CoordsTuple) -> list[Vehicle]:
        """
        Returns enemies which can shoot hex with given position.

        :param position: coordinates of hex
        :return: list of enemies
        """
        enemies = []
        for dist in NEIGHBOURS_OFFSETS:
            for offset in dist:
                neighbour_pos = hexes.summarize(position, offset)
                if self.is_vehicle(neighbour_pos):
                    enemy = self.vehicles[self.vehicles_positions[neighbour_pos]]
                    if self.can_shoot(enemy, position):
                        enemies.append(enemy)

        return enemies

    @property
    def current_player_vehicles(self) -> list[Vehicle]:
        """
        Returns list of vehicle objects with player_id == current_player_id.
        """
        return [
            self.vehicles[i] for i in self.vehicles_to_players[self.current_player_idx]
        ]


def game_loop(bot, game: GameSession):
    """
    Plays the given game with the given bot.

    :param bot:
    :param game:
    :return:
    """
    while game_tick(bot, game) is not None:
        pass


def game_tick(bot, game: GameSession):
    """
    Performs full turn in the game
    :param bot:
    :param game:
    :return:
    """
    game_state = game.game_state()

    if game_state["finished"]:
        print("You won" if game_state["winner"] == game.player_id else "You lost")
        print(f"Winner: {game_state['winner']}")
        return None

    if game_state["current_player_idx"] == game.player_id:
        print(f'Round: {game_state["current_turn"]}, ' f"player: {game.player_name}")
        for action in bot.get_actions(game_state):
            game.action(*action.server_format)
            print(
                f"  Action: "
                f'{"shoot" if action.action_code == ActionCode.SHOOT else "move"}'
                f" Actor: {action.actor} Target: {action.target}"
            )

    game.turn()

    return game_state
