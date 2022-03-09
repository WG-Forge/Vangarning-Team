"""
Contains class for game state's get_hex method's return value.
"""
from game_client.coordinates import Coords
from game_client.map_hexes import Hex


class GSHex:
    """
    Class to describe hex of a game state.

    Contains info about location, type and vehicle located on the hex.
    """
    __slots__ = ("coords", "map_hex", "vehicle")

    def __init__(self, coords, map_hex, vehicle=None):
        """
        :param coords: coordinates of the hex
        :param map_hex: type of the hex
        :param vehicle: vehicle located on the hex (if there is any)
        """
        self.coords: Coords = coords
        self.map_hex: Hex = map_hex
        self.vehicle = vehicle

    @property
    def can_stay(self) -> bool:
        """
        Tells if vehicle can stay on the hex.

        """
        if self.vehicle is not None:
            return False
        return self.map_hex.can_stay

    @property
    def can_go_through(self) -> bool:
        """
        Tells if vehicle can go through the hex.

        """
        return self.map_hex.can_go_through
