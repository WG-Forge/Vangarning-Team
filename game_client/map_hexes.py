"""
Contains classes to describe different hex types.

"""
# pylint: disable=too-few-public-methods
# No methods needed, just dataclasses.
# pylint: disable=missing-class-docstring
# Classes are reasonably described by their names
from dataclasses import dataclass

from game_client.vehicles import AtSpg, HeavyTank, MediumTank
from utility.singleton import SingletonMeta


class Hex:
    """
    Base class, mostly needed for typing purposes.

    """


@dataclass(frozen=True)
class StaticHex(Hex, metaclass=SingletonMeta):
    """
    Base singleton class for hexes that can't change their state.

    """

    can_go_through: bool = True
    can_shoot_through: bool = True
    can_stay: bool = True
    can_use: bool = False


@dataclass
class LimitedBonusHex(Hex):
    """
    Base class for hexes that can change their state.
    """

    uses_left: int = 3
    bonus: int = 0
    can_go_through: bool = True
    can_shoot_through: bool = True
    can_stay: bool = True

    def use(self) -> int:
        """
        Returns bonus if there is any uses left else 0.

        """
        if self.uses_left > 0:
            self.uses_left -= 1
            return self.bonus

        return 0


@dataclass(frozen=True)
class EmptyHex(StaticHex):
    can_go_through: bool = True
    can_shoot_through: bool = True
    can_stay: bool = True


@dataclass(frozen=True)
class Obstacle(StaticHex):
    can_go_through: bool = False
    can_shoot_through: bool = False
    can_stay: bool = False


@dataclass(frozen=True)
class Base(StaticHex):
    can_go_through: bool = True
    can_shoot_through: bool = True
    can_stay: bool = True


@dataclass(frozen=True)
class LightRepair(StaticHex):
    can_go_through: bool = True
    can_shoot_through: bool = True
    can_stay: bool = True
    served_classes: tuple = (MediumTank,)


@dataclass(frozen=True)
class HardRepair(StaticHex):
    can_go_through: bool = True
    can_shoot_through: bool = True
    can_stay: bool = True
    served_classes: tuple = (
        HeavyTank,
        AtSpg,
    )


@dataclass
class Catapult(LimitedBonusHex):
    can_go_through: bool = True
    can_shoot_through: bool = True
    can_stay: bool = True
    uses_left: int = 3


CONTENT_CLASSES = {
    "base": Base,
    "obstacle": Obstacle,
    "light_repair": LightRepair,
    "hard_repair": HardRepair,
    "catapult": Catapult,
}
