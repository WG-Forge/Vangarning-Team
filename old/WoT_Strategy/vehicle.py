"""
Classes to describe different vehicle types.
"""
import hexes
from settings import CoordsTuple


class Vehicle:
    def __init__(self, player_id, pid, hp, spawn_position, position, capture_points):
        # Can change throughout game session
        self.player_id: int = int(player_id)
        self.pid: int = int(pid)
        self.hp: int = int(hp)
        self.spawn_position: tuple[int, int, int] = spawn_position
        self.position: tuple[int, int, int] = position
        self.capture_points: int = capture_points
        # Can't change throughout game session
        self.damage: int = 0
        self.shooting_range: tuple[int, int] = (1, 1)
        self.max_hp: int = 1
        self.speed_points: int = 0
        self.distances_to_check: tuple[int, ...] = tuple(
            {
                self.speed_points,
                *range(self.shooting_range[0], self.shooting_range[1] + 1),
            }
        )

    def update(self, data: dict) -> None:
        """
        Updates object from dictionary.

        """
        self.position = hexes.dict_to_tuple(data["position"])
        self.capture_points = data["capture_points"]
        self.hp = data["health"]

    def target_in_shooting_range(self, target: CoordsTuple, obstacles: set):
        dist: int = hexes.straight_dist(self.position, target)
        return self.shooting_range[0] <= dist <= self.shooting_range[1]

    def __str__(self):
        return str(self.pid)


class AtSpg(Vehicle):
    def __init__(self, player_id, pid, hp, spawn_position, position, capture_points):
        super().__init__(player_id, pid, hp, spawn_position, position, capture_points)
        self.damage: int = 1
        self.max_hp = 2
        self.speed_points = 1
        self.shooting_range = (1, 3)

    def target_in_shooting_range(self, target: CoordsTuple, obstacles: set):
        if 0 not in hexes.delta(self.position, target):
            return False

        return super().target_in_shooting_range(target, obstacles)


class MediumTank(Vehicle):
    def __init__(self, player_id, pid, hp, spawn_position, position, capture_points):
        super().__init__(player_id, pid, hp, spawn_position, position, capture_points)
        self.damage: int = 1
        self.max_hp = 2
        self.speed_points = 2
        self.shooting_range = (2, 2)


class LightTank(Vehicle):
    def __init__(self, player_id, pid, hp, spawn_position, position, capture_points):
        super().__init__(player_id, pid, hp, spawn_position, position, capture_points)
        self.damage: int = 1
        self.max_hp = 1
        self.speed_points = 3
        self.shooting_range = (2, 2)


class HeavyTank(Vehicle):
    def __init__(self, player_id, pid, hp, spawn_position, position, capture_points):
        super().__init__(player_id, pid, hp, spawn_position, position, capture_points)
        self.damage: int = 1
        self.max_hp = 3
        self.speed_points = 1
        self.shooting_range = (1, 2)


class Spg(Vehicle):
    def __init__(self, player_id, pid, hp, spawn_position, position, capture_points):
        super().__init__(player_id, pid, hp, spawn_position, position, capture_points)
        self.damage: int = 1
        self.max_hp = 1
        self.speed_points = 1
        self.shooting_range = (3, 3)
