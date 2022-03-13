"""
Contains class for game state's get_hex method's return value.
"""
from typing import Union

from utility.coordinates import Coords
from game_client.map_hexes import LimitedBonusHex, StaticHex
from game_client.vehicles import Vehicle


class GSHex:
    """
    Class to describe hex of a game state.

    Contains info about location, type and actor located on the hex.
    """

    __slots__ = ("coords", "map_hex", "is_spawn_point", "vehicle")

    def __init__(self, coords, map_hex, is_spawn_point, vehicle=None):
        """
        :param coords: coordinates of the hex
        :param map_hex: type of the hex
        :param vehicle: actor located on the hex (if there is any)
        :param is_spawn_point: if hex with given coords is a spawn point
        """
        self.coords: Coords = coords
        self.map_hex: Union[StaticHex, LimitedBonusHex] = map_hex
        self.is_spawn_point = is_spawn_point
        self.vehicle: Vehicle = vehicle

    def can_stay(self, actor: Vehicle) -> bool:
        """
        Tells if actor can stay on the hex.

        """
        if self.vehicle is not None:
            return False
        if self.is_spawn_point and actor.spawn_position != self.coords:
            return False
        return self.map_hex.can_stay

    @property
    def can_go_through(self) -> bool:
        """
        Tells if actor can go through the hex.

        """
        return self.map_hex.can_go_through

    @property
    def can_shoot_through(self) -> bool:
        """
        Tells if vehicle (AtSpg to be exact) can shoot through the hex.

        """
        return self.map_hex.can_shoot_through

    def __eq__(self, other):
        return self.coords == other.coords
