"""
Contains data class describing game map.
"""

from utility.coordinates import Coords
from utility.custom_typings import ContentDictTyping, MapDictTyping
from game_client.map_hexes import CONTENT_CLASSES, EmptyHex, Hex


class InvalidContentTypeError(Exception):
    """
    Called if content type received from the server has no class
    corresponding to it.
    """


class GameMap:
    """
    Contains static information about game map.

    """

    def __init__(self, game_map: MapDictTyping):
        self.map_radius: int = game_map["size"]
        self.map_name: str = game_map["name"]

        self.content: dict[Coords, Hex] = {}

        self.__parse_content(game_map["content"])

    def __contains__(self, item: Coords):
        return item in self.content

    def __getitem__(self, item):
        if item in self.content:
            return self.content[item]
        return EmptyHex()

    def __parse_content(self, data: ContentDictTyping) -> None:
        for content_type, instances in data.items():
            if content_type in CONTENT_CLASSES:
                content_klass = CONTENT_CLASSES[content_type]
            else:
                raise InvalidContentTypeError(
                    f"No class for {content_type} content. "
                    f"Update map_hexes.py to current server version "
                    f"or add existing classes to CONTENT_CLASSES."
                )

            for item in instances:
                self.content[Coords(item)] = content_klass()

    def are_valid_coords(self, coords: Coords) -> bool:
        """
        Tells if hex with given coordinates is in map boundaries.

        """
        return abs(coords.max_dimension) < self.map_radius
