"""
Classes to describe different tank types.

NOT USED ANYWHERE YET
"""
from settings import HexCode


class Vehicle:
    def __init__(self, player_id, pid, health, spawn_position, position, capture_points):
        self.player_id: int = player_id
        self.pid = pid
        self.health_points: int = health
        self.spawn_position: tuple[int, int, int] = spawn_position
        self.position: tuple[int, int, int] = position
        self.capture_points: int = capture_points
        self.damage: int = 0
        self.shooting_range = (1, 1)
        self.max_health: int = 1
        self.speed_points: int = 0

        self.distances_to_check = tuple(
            {
                self.speed_points,
                *range(self.shooting_range[0], self.shooting_range[1] + 1)
            }
        )

    # def move(self, new_position: tuple) -> None:
    #     if not new_position.capture_position():
    #         return False
    #     self.position.free_position()
    #     self.position = new_position
    #     self.position.capture_position()
    #     return True

    # def update(self, new_position, capture_points, health_points):
    #     if self.position is not None:
    #         self.position.free_position()
    #     self.position = new_position
    #     self.position.capture_position()
    #     self.capture_points = capture_points
    #     self.health_points = health_points

    def update(self, data):
        self.position = tuple(data["position"].values())
        self.capture_points = data["capture_points"]
        self.health_points = data["health"]

    def is_target_in_shooting_range(self, target):
        dist = sum(map(lambda c: abs(c[0] - c[1]), zip((1, 2, 3), (3, 2, 1)))) / 2
        return self.shooting_range[0] <= dist <= self.shooting_range[1]

    # def shoot(self, vehicle):
    #     if self.is_opponent(vehicle):
    #         return vehicle.shoot_down(self.damage)
    #     return 0

    # def is_opponent(self, vehicle):
    #     return self.player_id != vehicle.player_id
    #
    # def spawn_position(self, spawn_position):
    #     self.spawn_position = spawn_position
    #     self.position = self.spawn_position

    # def get_spawn_position(self):
    #     return self.spawn_position.get_position()
    #
    # def get_current_position(self):
    #     return self.position.get_position()

    # def repeat_spawn_position(self):
    #     if not self.move(self.spawn_position):
    #         raise RuntimeError("spawn position already occupied")
    #     self.health_points = self.max_health
    #     self.capture_points = 0
    #
    # def shoot_down(self, damage_points=1):
    #     self.health_points -= damage_points
    #     if self.health_points <= 0:
    #         return self.destruction_points
    #     return 0


class AtSpg(Vehicle):
    def __init__(self, player_id, pid, health, spawn_position, position, capture_points):
        super().__init__(player_id, pid, health, spawn_position, position, capture_points)
        self.damage: int = 1
        self.max_health = 2
        self.speed_points = 1
        self.shooting_range = (1, 3)

    def is_target_in_shooting_range(self, target):
        # If none of dx, dy, dz equals to 0
        if 0 not in map(lambda c: c[0] - c[1], zip(self.position, target)):
            return False

        return super().is_target_in_shooting_range(target)


class MediumTank(Vehicle):
    def __init__(self, player_id, pid, health, spawn_position, position, capture_points):
        super().__init__(player_id, pid, health, spawn_position, position, capture_points)
        self.damage: int = 1
        self.max_health = 2
        self.speed_points = 2
        self.shooting_range = (1, 2)


class LightTank(Vehicle):
    def __init__(self, player_id, pid, health, spawn_position, position, capture_points):
        super().__init__(player_id, pid, health, spawn_position, position, capture_points)
        self.damage: int = 1
        self.max_health = 1
        self.speed_points = 3
        self.shooting_range = (2, 2)


class HeavyTank(Vehicle):
    def __init__(self, player_id, pid, health, spawn_position, position, capture_points):
        super().__init__(player_id, pid, health, spawn_position, position, capture_points)
        self.damage: int = 1
        self.max_health = 3
        self.speed_points = 1
        self.shooting_range = (1, 2)


class Spg(Vehicle):
    def __init__(self, player_id, pid, health, spawn_position, position, capture_points):
        super().__init__(player_id, pid, health, spawn_position, position, capture_points)
        self.damage: int = 1
        self.max_health = 1
        self.speed_points = 1
        self.shooting_range = (3, 3)
