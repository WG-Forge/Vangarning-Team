from dataclasses import dataclass

from game_client.vehicle import AtSpg, HeavyTank, MediumTank, Vehicle
from utility.singleton import SingletonMeta


class Hex:
    pass


@dataclass(frozen=True)
class StaticHex(Hex, metaclass=SingletonMeta):
    can_go_through: bool = True
    can_stay: bool = True


@dataclass()
class UsableHex(Hex):
    can_go_through: bool = True
    can_stay: bool = True
    uses_left: int = 3


class EmptyHex(StaticHex):
    can_go_through: bool = True
    can_stay: bool = True


class Obstacle(StaticHex):
    can_go_through: bool = False
    can_stay: bool = False


class Base(StaticHex):
    can_go_through: bool = True
    can_stay: bool = True


class LightRepair(StaticHex):
    can_go_through: bool = True
    can_stay: bool = True
    served_classes: tuple[Vehicle] = (MediumTank,)


class HardRepair(StaticHex):
    can_go_through: bool = True
    can_stay: bool = True
    served_classes: tuple[Vehicle] = (HeavyTank, AtSpg, )


class Catapult(UsableHex):
    can_go_through: bool = True
    can_stay: bool = True
    uses_left: int = 3


CONTENT_CLASSES = {
    "base": Base,
    "obstacle": Obstacle,
    "light_repair": LightRepair,
    "hard_repair": HardRepair,
    "catapult": Catapult,
}
