"""
Classes to describe different vehicle types.
"""
from game_client.coordinates import Coords
from game_client.custom_typings import VehicleDictTyping


class Vehicle:
    """
    Base class for vehicles.

    """

    # pylint: disable=too-many-instance-attributes
    # Eleven is reasonable in this case.
    def __init__(self, vehicle_id: int, data: VehicleDictTyping):
        """
        :param vehicle_id: vehicle id
        :param data: part of GAME_STATE response from the server
        """
        # Data updated from game_state
        self.player_id: int = data["player_id"]
        self.vehicle_id: int = vehicle_id
        # pylint: disable=invalid-name
        # hp is a valid snake-case name.
        self.hp: int = data["health"]
        self.spawn_position: Coords = Coords(data["spawn_position"])
        self.position: Coords = Coords(data["position"])
        self.capture_points: int = data["capture_points"]
        # Type-described data
        self.damage: int = 0
        self.shooting_range: tuple[int, int] = (1, 1)
        self.max_hp: int = 1
        self.speed_points: int = 0
        self.distances_to_check: tuple[int, ...] = (1,)

    def update(self, data: VehicleDictTyping) -> None:
        """
        Updates object from dictionary.

        """
        self.position = Coords(data["position"])
        self.capture_points = data["capture_points"]
        self.hp = data["health"]

    def target_in_shooting_range(self, target: Coords) -> bool:
        """
        Tells if target is in shooting range, ignores obstacles.

        :param target: coordinates of the target
        :return:
        """
        dist: int = self.position.straight_dist_to(target)
        return self.shooting_range[0] <= dist <= self.shooting_range[1]

    def __str__(self):
        return str(f"{self.player_id}, {self.__class__}")


class AtSpg(Vehicle):
    """
    Class to describe AtSpg vehicle type.

    """

    def __init__(self, vehicle_id: int, data: VehicleDictTyping):
        super().__init__(vehicle_id, data)
        # Type-described data
        self.damage: int = 1
        self.max_hp: int = 2
        self.speed_points: int = 1
        self.shooting_range: tuple[int, int] = (1, 3)
        self.distances_to_check: tuple[int, ...] = (1, 2, 3)

    def target_in_shooting_range(self, target: Coords):
        if 0 not in self.position.delta(target):
            return False

        return super().target_in_shooting_range(target)


class MediumTank(Vehicle):
    """
    Class to describe Medium Tank vehicle type.

    """

    def __init__(self, vehicle_id: int, data: VehicleDictTyping):
        super().__init__(vehicle_id, data)
        # Type-described data
        self.damage: int = 1
        self.max_hp: int = 2
        self.speed_points: int = 2
        self.shooting_range: tuple[int, int] = (2, 2)
        self.distances_to_check: tuple[int, ...] = (1, 2)


class LightTank(Vehicle):
    """
    Class to describe Light Tank vehicle type.

    """

    def __init__(self, vehicle_id: int, data: VehicleDictTyping):
        super().__init__(vehicle_id, data)
        # Type-described data
        self.damage: int = 1
        self.max_hp: int = 1
        self.speed_points: int = 3
        self.shooting_range: tuple[int, int] = (2, 2)
        self.distances_to_check: tuple[int, ...] = (1, 2, 3)


class HeavyTank(Vehicle):
    """
    Class to describe Heavy Tank vehicle type.

    """

    def __init__(self, vehicle_id: int, data: VehicleDictTyping):
        super().__init__(vehicle_id, data)
        # Type-described data
        self.damage: int = 1
        self.max_hp: int = 3
        self.speed_points: int = 1
        self.shooting_range: tuple[int, int] = (1, 2)
        self.distances_to_check: tuple[int, ...] = (1, 2)


class Spg(Vehicle):
    """
    Class to describe Spg vehicle type.

    """

    def __init__(self, vehicle_id: int, data: VehicleDictTyping):
        super().__init__(vehicle_id, data)
        # Type-described data
        self.damage: int = 1
        self.max_hp: int = 1
        self.speed_points: int = 1
        self.shooting_range: tuple[int, int] = (3, 3)
        self.distances_to_check: tuple[int, ...] = (1, 3)


VEHICLE_CLASSES = {
    "at_spg": AtSpg,
    "medium_tank": MediumTank,
    "light_tank": LightTank,
    "heavy_tank": HeavyTank,
    "spg": Spg,
}

TYPE_ORDER = (Spg, LightTank, HeavyTank, MediumTank, AtSpg)
