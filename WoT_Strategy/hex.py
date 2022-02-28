"""
Simple functions to deal with hex coordinates transformations
in a cubic coordinates system.
"""
from settings import CoordsDict, CoordsTuple
from vehicle import Vehicle


class Hex:
    def __init__(self, pos: CoordsTuple):
        self.x = pos[0]
        self.y = pos[1]
        self.z = pos[2]


class HexWithVehicle(Hex):
    def __init__(self, pos: CoordsTuple, vehicle: Vehicle):
        super().__init__(pos)
        self.vehicle = vehicle


class Base(Hex):
    def __init__(self, pos: CoordsTuple):
        super().__init__(pos)


class Obstacle(Hex):
    def __init__(self, pos: CoordsTuple):
        super().__init__(pos)


class LightRepair(Hex):
    def __init__(self, pos: CoordsTuple):
        super().__init__(pos)


class HardRepair(Hex):
    def __init__(self, pos: CoordsTuple):
        super().__init__(pos)


class Catapult(Hex):
    def __init__(self, pos: CoordsTuple):
        super().__init__(pos)


def tuple_to_dict(pos: CoordsTuple) -> CoordsDict:
    """
    Converts tuple of coordinates (x, y, z) to dictionary where components are named.

    :param pos: coordinates of hex (x, y, z)
    :return: dict with coordinates in a server format
    """
    return {
        "x": pos[0],
        "y": pos[1],
        "z": pos[2],
    }


def dict_to_tuple(pos: CoordsDict) -> CoordsTuple:
    """
    Converts coordinates in a server format to tuple (x, y, z).

    :param pos: coordinates in a dict {"x": x, "y": y, "z": z}
    :return: tuple (x, y, z)
    """
    return tuple(pos.values())


def straight_dist(pos1: CoordsTuple, pos2: CoordsTuple) -> int:
    """
    Calculates distance between two hexes.

    :param pos1: coordinates of first hex (x, y, z)
    :param pos2: coordinates of second hex (x, y, z)
    :return: distance between pos1 and pos2
    """
    return int(sum(map(lambda i: abs(i[0] - i[1]), zip(pos1, pos2))) / 2)


# def is_hex_reachable(
#         position: CoordsTuple,
#         target: CoordsTuple,
#         max_len: int,
#         obstacles: Optional[set] = None
# ) -> bool:
#     if obstacles is None:
#         return straight_dist(position, target) <= max_len
#
#     visited = set()
#     visited.add(position)
#     fringes = [[position]]
#
#     for k in range(1, max_len + 1):
#         fringes.append([])
#         for visited_hex in fringes[k-1]:

def delta(pos1: CoordsTuple, pos2: CoordsTuple) -> CoordsTuple:
    """

    :param pos1: coordinates of first hex (x, y, z)
    :param pos2: coordinates of second hex (x, y, z)
    :return: vector of deltas between pos1 and pos2
    """
    return tuple(map(lambda c: abs(c[0] - c[1]), zip(pos1, pos2)))


def unit_vector(pos1: CoordsTuple, pos2: CoordsTuple) -> tuple:
    """
    Calculates the unit vector (normalized vector) based on two hexes.
    ORDER MATTERS

    :param pos1: coordinates of first hex (x, y, z)
    :param pos2: coordinates of second hex (x, y, z)
    :return: unit vector directed from pos2 to pos1
    """
    return tuple(
        map(
            lambda x: x[0] - x[1]
            if x[0] - x[1] == 0
            else (x[0] - x[1]) / abs(x[0] - x[1]),
            zip(pos1, pos2),
        )
    )


def multiply(c: int, pos: CoordsTuple) -> CoordsTuple:
    """
    Multiplies coordinates of given hex.

    :param c: multiplier
    :param pos: coordinates of hex (x, y, z)
    :return: coordinates of hex (c * x, c * y, c * z)
    """
    return tuple(map(lambda x: c * x, pos))


def summarize(pos1: CoordsTuple, pos2: CoordsTuple) -> CoordsTuple:
    """
    Returns sum of coordinates of given hexes.

    :param pos1: coordinates of first hex (x, y, z)
    :param pos2: coordinates of second hex (x, y, z)
    :return: coordinates (x1 + x2, y1 + y2, z1 + z2)
    """
    return tuple(map(sum, zip(pos1, pos2)))
