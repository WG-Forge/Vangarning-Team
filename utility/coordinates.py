"""
Contains class for map coordinates.

"""
from __future__ import annotations

from typing import Union

from game_client.custom_typings import CoordsDictTyping, CoordsTupleTyping


class Coords:
    """
    Class for describing hex position in cubic coordinates system.

    """

    def __init__(self, coordinates: Union[CoordsDictTyping, CoordsTupleTyping]):
        if isinstance(coordinates, dict):
            # noinspection PyTypeChecker
            coordinates: CoordsTupleTyping = tuple(coordinates.values())

        self.coordinates = coordinates
        self.max_dimension: int = max([abs(i) for i in self.coordinates])

    def __eq__(self, other):
        return self.coordinates == other.coordinates

    def __hash__(self):
        return self.coordinates.__hash__()

    def __iter__(self):
        return self.coordinates.__iter__()

    def __abs__(self):
        # noinspection PyTypeChecker
        return Coords(tuple(abs(i) for i in self.coordinates))

    def __add__(self, other: Coords) -> Coords:
        if isinstance(other, Coords):
            # noinspection PyTypeChecker
            return Coords(
                tuple(map(lambda x1, x2: x1 + x2, self.coordinates, other.coordinates))
            )

        raise TypeError("Can only add Coords instance")

    def __sub__(self, other: Coords) -> Coords:
        if isinstance(other, Coords):
            # noinspection PyTypeChecker
            return Coords(
                tuple(map(lambda x1, x2: x1 - x2, self.coordinates, other.coordinates))
            )

        raise TypeError("Can only subtract Coords instance")

    def __mul__(self, other) -> Coords:
        if isinstance(other, int):
            # noinspection PyTypeChecker
            return Coords(tuple(map(lambda x: other * x, self.coordinates)))

        if isinstance(other, float):
            if other.is_integer():
                # noinspection PyTypeChecker
                return Coords(tuple(map(lambda x: int(other) * x, self.coordinates)))
            raise TypeError("Float must satisfy .is_integer() method")

        raise TypeError(
            f"Cannot multiply coordinates by an instance of {other.__class__}"
        )

    def __str__(self):
        return self.coordinates.__str__()

    def __repr__(self):
        return self.coordinates.__repr__()

    def delta(self, other: Coords) -> Coords:
        """
        Calculates delta vector between self and other coordinates.

        :param other: any other Coords object
        :return: Coords object representing delta vector
        """
        return abs(self - other)

    def straight_dist_to(self, coords: Coords) -> int:
        """
        Calculates distance from self to other Coords

        :param coords: any other Coords object
        :return: distance (in hexes) between two Coords' objects
        """
        return int(sum(self.delta(coords).coordinates) / 2)

    def unit_vector(self, other: Coords) -> Coords:
        """
        Calculates the unit vector (normalized vector) to given coordinates.

        :param other: any other Coords object
        :return: Coords object representing unit vector to given coordinates
        """
        # noinspection PyTypeChecker
        return Coords(
            tuple(
                map(
                    lambda x: 0
                    if x[0] - x[1] == 0
                    else int((x[0] - x[1]) / abs(x[0] - x[1])),
                    zip(other.coordinates, self.coordinates),
                )
            )
        )

    @property
    def server_format(self) -> CoordsDictTyping:
        """
        Converts coordinates to the server format with named dimensions as keys.
        :return: coordinates dictionary
        """
        return {
            "x": self.coordinates[0],
            "y": self.coordinates[1],
            "z": self.coordinates[2],
        }
