"""
Classes to describe different vehicle types.
"""
from utility.coordinates import Coords
from game_client.custom_typings import VehicleDictTyping


class Vehicle:
    """
    Base class for vehicles.

    """

    # pylint: disable=too-many-instance-attributes
    # 12 is reasonable in this case.
    def __init__(self, vehicle_id: int, data: VehicleDictTyping):
        """
        :param vehicle_id: actor id
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
        self.shoot_range_bonus: int = data["shoot_range_bonus"]
        # Type-described data
        self.damage: int = 0
        self.shoot_range: tuple[int, int] = (1, 1)
        self.max_hp: int = 1
        self.speed_points: int = 0
        self.shoots_flat = False

    def update(self, data: VehicleDictTyping) -> None:
        """
        Updates object from dictionary.

        """
        self.update_position(Coords(data["position"]))
        self.capture_points = data["capture_points"]
        self.hp = data["health"]
        self.shoot_range_bonus = data["shoot_range_bonus"]

    def update_position(self, new_position: Coords):
        self.position = new_position

    def target_in_shoot_range(self, target: Coords) -> bool:
        """
        Tells if target is in shooting range, ignores obstacles.

        :param target: coordinates of the target
        :return:
        """
        dist: int = self.position.straight_dist_to(target)
        return self.shoot_range[0] <= dist <= (self.shoot_range[1]
                                               + self.shoot_range_bonus)

    @property
    def distances_to_check(self) -> list:
        """
        Calculates distances that can be affected by vehicle.

        Based on static info about speed points, shoot range and bonuses.
        Is used to check hexes that are both in moving range
        and shoot range only once.

        :return: distances that the vehicle can potentially affect
        """
        return list({
            self.speed_points,
            *range(
                self.shoot_range[0],
                self.shoot_range[1] + self.shoot_range_bonus + 1
            )
        })

    def shoot(self) -> None:
        self.shoot_range_bonus = 0

    def move(self, target: Coords) -> None:
        self.position = target

    def receive_damage(self, damage: int) -> int:
        """
        Applies damage to the vehicle and returns win points generated.

        If hp of the vehicle became 0 after taking damage returns
        vehicle's max hp as the amount of generated win points, else 0.

        :param damage: amount of damage to be taken
        :return: amount of win points generated by applying the damage.
        """
        self.hp = self.hp - damage if damage <= self.hp else 0
        if self.hp == 0:
            return self.max_hp
        return 0

    def __str__(self):
        return str(f"{self.player_id}, {self.__class__}")


class AtSpg(Vehicle):
    """
    Class to describe AtSpg actor type.

    """

    def __init__(self, vehicle_id: int, data: VehicleDictTyping):
        super().__init__(vehicle_id, data)
        # Type-described data
        self.damage: int = 1
        self.max_hp: int = 2
        self.speed_points: int = 1
        self.shoot_range: tuple[int, int] = (1, 3)
        self.shoots_flat = True

    def target_in_shoot_range(self, target: Coords):
        if 0 not in self.position.delta(target):
            return False

        return super().target_in_shoot_range(target)


class MediumTank(Vehicle):
    """
    Class to describe Medium Tank actor type.

    """

    def __init__(self, vehicle_id: int, data: VehicleDictTyping):
        super().__init__(vehicle_id, data)
        # Type-described data
        self.damage: int = 1
        self.max_hp: int = 2
        self.speed_points: int = 2
        self.shoot_range: tuple[int, int] = (2, 2)
        self.shoots_flat = False


class LightTank(Vehicle):
    """
    Class to describe Light Tank actor type.

    """

    def __init__(self, vehicle_id: int, data: VehicleDictTyping):
        super().__init__(vehicle_id, data)
        # Type-described data
        self.damage: int = 1
        self.max_hp: int = 1
        self.speed_points: int = 3
        self.shoot_range: tuple[int, int] = (2, 2)
        self.shoots_flat = False


class HeavyTank(Vehicle):
    """
    Class to describe Heavy Tank actor type.

    """

    def __init__(self, vehicle_id: int, data: VehicleDictTyping):
        super().__init__(vehicle_id, data)
        # Type-described data
        self.damage: int = 1
        self.max_hp: int = 3
        self.speed_points: int = 1
        self.shoot_range: tuple[int, int] = (1, 2)
        self.shoots_flat = False


class Spg(Vehicle):
    """
    Class to describe Spg actor type.

    """

    def __init__(self, vehicle_id: int, data: VehicleDictTyping):
        super().__init__(vehicle_id, data)
        # Type-described data
        self.damage: int = 1
        self.max_hp: int = 1
        self.speed_points: int = 1
        self.shoot_range: tuple[int, int] = (3, 3)
        self.shoots_flat = False


VEHICLE_CLASSES = {
    "at_spg": AtSpg,
    "medium_tank": MediumTank,
    "light_tank": LightTank,
    "heavy_tank": HeavyTank,
    "spg": Spg,
}

TYPE_ORDER = (Spg, LightTank, HeavyTank, MediumTank, AtSpg)
