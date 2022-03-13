"""
Contains class for map coordinates.

"""
from __future__ import annotations

from typing import Union

from utility.custom_typings import CoordsDictTyping, CoordsTupleTyping


class Coords:
    """
    Class for describing hex position in cubic coordinates system.

    """

    def __init__(self, coordinates: Union[CoordsDictTyping, CoordsTupleTyping]):
        if isinstance(coordinates, dict):
            coordinates = (coordinates["x"], coordinates["y"], coordinates["z"])

        self.x, self.y, self.z = coordinates
        self.max_dimension: int = max([abs(self.x), abs(self.y), abs(self.z)])

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __hash__(self):
        return hash((self.x, self.y, self.z))

    def __iter__(self):
        for i in (self.x, self.y, self.z):
            yield i

    def __abs__(self):
        return Coords((abs(self.x), abs(self.y), abs(self.z)))

    def __add__(self, other: Coords) -> Coords:
        if isinstance(other, Coords):
            return Coords((self.x + other.x, self.y + other.y, self.z + other.z))

        raise TypeError("Can only add Coords instance")

    def __sub__(self, other: Coords) -> Coords:
        if isinstance(other, Coords):
            return Coords((self.x - other.x, self.y - other.y, self.z - other.z))

        raise TypeError("Can only subtract Coords instance")

    def __mul__(self, other) -> Coords:
        if isinstance(other, int):
            return Coords((self.x * other, self.y * other, self.z * other))

        if isinstance(other, float):
            if other.is_integer():
                return Coords(
                    (self.x * int(other), self.y * int(other), self.z * int(other))
                )
            raise TypeError("Float must satisfy .is_integer() method")

        raise TypeError(
            "Cannot multiply coordinates by an instance "
            f"of {other.__class__.__name__}"
        )

    def __str__(self):
        return f"Coords({self.x}, {self.y}, {self.z})"

    def __repr__(self):
        return f"Coords(({self.x}, {self.y}, {self.z}))"

    def delta(self, other: Coords) -> Coords:
        """
        Calculates delta vector between self and other coordinates.

        :param other: any other Coords object
        :return: Coords object representing delta vector
        """
        return abs(self - other)

    def straight_dist_to(self, other: Coords) -> int:
        """
        Calculates distance from self to other Coords

        :param other: any other Coords object
        :return: distance (in hexes) between two Coords' objects
        """
        return int(sum(self.delta(other)) / 2)

    def unit_vector(self, other: Coords) -> Coords:
        """
        Calculates the unit vector (normalized vector) directed
        to given coordinates.

        :param other: any other Coords object
        :return: Coords object representing unit vector directed
        to given coordinates
        """
        # noinspection PyTypeChecker
        tuple_generator = map(
            lambda x: 0
            if x[0] - x[1] == 0
            else int((x[0] - x[1]) / abs(x[0] - x[1])),
            zip(other, self),
        )
        return Coords((
            next(tuple_generator),
            next(tuple_generator),
            next(tuple_generator)
            )
        )

    @property
    def server_format(self) -> CoordsDictTyping:
        """
        Converts coordinates to the server format
        with named dimensions as keys.
        :return: coordinates dictionary
        """
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
        }
