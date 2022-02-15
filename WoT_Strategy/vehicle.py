"""
Classes to describe different tank types.

NOT USED ANYWHERE YET
"""
import hex
from settings import HexCode


class Vehicle:
    def __init__(
        self, player_id, pid, health, spawn_position, position, capture_points
    ):
        # Can change throughout game session
        self.player_id: int = player_id
        self.pid = pid
        self.hp: int = health
        self.spawn_position: tuple[int, int, int] = spawn_position
        self.position: tuple[int, int, int] = position
        self.capture_points: int = capture_points
        # Can't change throughout game session
        self.damage: int = 0
        self.shooting_range = (1, 1)
        self.max_hp: int = 1
        self.speed_points: int = 0
        self.distances_to_check = tuple(
            {
                self.speed_points,
                *range(self.shooting_range[0], self.shooting_range[1] + 1),
            }
        )

    def update(self, data):
        self.position = tuple(data["position"].values())
        self.capture_points = data["capture_points"]
        self.health_points = data["health"]

    def is_target_in_shooting_range(self, target):
        print(self.shooting_range)
        dist = hex.straight_dist(self.position, target)
        return self.shooting_range[0] <= dist <= self.shooting_range[1]


class AtSpg(Vehicle):
    def __init__(
        self, player_id, pid, health, spawn_position, position, capture_points
    ):
        super().__init__(
            player_id, pid, health, spawn_position, position, capture_points
        )
        self.damage: int = 1
        self.max_health = 2
        self.speed_points = 1
        self.shooting_range = (1, 3)

    def is_target_in_shooting_range(self, target):
        # If none of dx, dy, dz equals to 0
        if 0 not in hex.delta(self.position, target):
            return False

        return super().is_target_in_shooting_range(target)


class MediumTank(Vehicle):
    def __init__(
        self, player_id, pid, health, spawn_position, position, capture_points
    ):
        super().__init__(
            player_id, pid, health, spawn_position, position, capture_points
        )
        self.damage: int = 1
        self.max_health = 2
        self.speed_points = 2
        self.shooting_range = (1, 2)


class LightTank(Vehicle):
    def __init__(
        self, player_id, pid, health, spawn_position, position, capture_points
    ):
        super().__init__(
            player_id, pid, health, spawn_position, position, capture_points
        )
        self.damage: int = 1
        self.max_health = 1
        self.speed_points = 3
        self.shooting_range = (2, 2)


class HeavyTank(Vehicle):
    def __init__(
        self, player_id, pid, health, spawn_position, position, capture_points
    ):
        super().__init__(
            player_id, pid, health, spawn_position, position, capture_points
        )
        self.damage: int = 1
        self.max_health = 3
        self.speed_points = 1
        self.shooting_range = (1, 2)


class Spg(Vehicle):
    def __init__(
        self, player_id, pid, health, spawn_position, position, capture_points
    ):
        super().__init__(
            player_id, pid, health, spawn_position, position, capture_points
        )
        self.damage: int = 1
        self.max_health = 1
        self.speed_points = 1
        self.shooting_range = (3, 3)
