"""
Contains class to store game state.

"""


from typing import Optional

from utility.coordinates import Coords
from utility.custom_typings import (CoordsDictTyping, GameStateDictTyping,
                                    MapDictTyping, VehicleDictTyping)
from game_client.map import GameMap
from game_client.player import Player
from game_client.state_hex import GSHex
from game_client.vehicles import VEHICLE_CLASSES, Vehicle


class OutOfBoundsError(Exception):
    """
    Called when coordinates are out of map's bounds.
    """


class GameState:
    """
    Stores parsed data about game's state.

    """

    # pylint: disable=too-many-instance-attributes
    # Nine is reasonable in this case.
    def __init__(self, game_map: MapDictTyping):
        """
        :param game_map: MAP response from the server.
        """
        self.game_map: GameMap = GameMap(game_map)
        self.finished: bool = False
        self.winner: Optional[Player] = None
        self.num_turns: int = -1
        self.current_turn: int = -1
        self.current_player: Optional[Player] = None
        self.players: dict[int, Player] = {}
        self.vehicles: dict[Coords, Vehicle] = {}
        self.spawn_points: list[Coords] = []

    def update(self, data: GameStateDictTyping) -> None:
        """
        Updates data in instance from GAME_STATE response from the server.

        :param data: GAME_STATE response from the server
        """
        if not self.players:
            self.__populate_players_vehicles(data)
        else:
            self.__update_players_vehicles(data)

        self.__update_catapults(data["catapult_usage"])

        self.current_turn = data["current_turn"]
        self.current_player = self.players[data["current_player_idx"]]
        self.finished = data["finished"]
        self.winner = (
            data["winner"] if data["winner"] is None else self.players[data["winner"]]
        )

    def get_hex(self, coordinates: Coords) -> GSHex:
        """
        Generates and returns object with info about hex at the given position.

        :param coordinates: Coords object
        :return: GSHex object
        """
        if self.game_map.are_valid_coords(coordinates):
            return GSHex(
                coordinates,
                self.game_map[coordinates],
                coordinates in self.spawn_points,
                self.__get_vehicle_or_none(coordinates),
            )

        raise OutOfBoundsError(
            f"Given coordinates {coordinates} are not valid coordinates "
            f"for the game map with radius {self.game_map.map_radius}."
        )

    def __populate_players_vehicles(self, data: GameStateDictTyping) -> None:
        """
        Populates information about vehicles and players.

        Called only at the first call of self.update method
        :param data: GAME_STATE response from the server
        """
        self.num_turns = data["num_turns"]

        for player in data["players"]:
            self.players[int(player["idx"])] = Player(player)

        for vid, vehicle in data["vehicles"].items():
            vehicle_obj: Vehicle = VEHICLE_CLASSES[vehicle["vehicle_type"]](
                int(vid), vehicle
            )
            self.vehicles[vehicle_obj.position] = vehicle_obj
            self.players[vehicle_obj.player_id].add_vehicle(vehicle_obj)
            self.spawn_points.append(vehicle_obj.spawn_position)

    def __update_players_vehicles(self, data: GameStateDictTyping) -> None:
        """
        Calls update methods for each player and actor.

        :param data: GAME_STATE response from the server
        """
        for idx, player in self.players.items():
            player.update(data["win_points"][str(idx)], data["attack_matrix"])

        vehicles_buff: dict[int, Vehicle] = {}  # For the cases when there is
        # any vehicle at the new_pos
        for vid, vehicle in data["vehicles"].items():
            new_pos = Coords(vehicle["position"])
            if int(vid) in vehicles_buff:
                vehicle_obj = vehicles_buff[int(vid)]
            else:
                vehicle_obj = self.__get_vehicle_by_id(int(vid))
                self.vehicles.pop(vehicle_obj.position)

            vehicle_obj.update(vehicle)
            if new_pos in self.vehicles:
                vehicle_to_buff = self.vehicles[new_pos]
                vehicles_buff[vehicle_to_buff.vehicle_id] = vehicle_to_buff
            self.vehicles[new_pos] = vehicle_obj

    def __update_vehicle(self, vid: str, vehicle: VehicleDictTyping) -> None:
        """
        Changes actor position in self.vehicles and
        calls actor's update method.

        :param vid: actor id
        :param vehicle: part of GAME_STATE response with
        an info about the actor
        """
        new_pos = Coords(vehicle["position"])
        vehicle_obj = self.__get_vehicle_by_id(int(vid))
        self.vehicles.pop(vehicle_obj.position)
        vehicle_obj.update(vehicle)
        self.vehicles[new_pos] = vehicle_obj

    def __get_vehicle_by_id(self, vehicle_id: int) -> Vehicle:
        for vehicle in self.vehicles.values():
            if vehicle.vehicle_id == vehicle_id:
                return vehicle

        raise KeyError(
            f"There is no vehicle with id {vehicle_id}, "
            f"{type(vehicle_id)}"
        )

    def __update_catapults(self, catapult_usages: list[CoordsDictTyping]) -> None:
        """
        Updates amount of uses left for every used catapult.

        :param catapult_usages: part of GAME_STATE response
        """
        for usage in catapult_usages:
            self.game_map[Coords(usage)].uses_left -= 1

    def __get_vehicle_or_none(self, coords: Coords) -> Optional[Vehicle]:
        """
        Return actor at the given position if there is any or None.

        :param coords: Coords object
        :return: Vehicle object located at the given position or None
        """
        if coords in self.vehicles:
            return self.vehicles[coords]
        return None
