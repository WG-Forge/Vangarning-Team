"""
Classes to describe different tank types.

NOT USED ANYWHERE YET
"""

class Vehicle:
    def __init__(self, player_id, health, spawn_position, position, capture_points):
        self.player_id = player_id
        self.health_points = health
        self.spawn_position = spawn_position
        self.current_position = position
        self.capture_points = capture_points
        self.damage_points = 1

    def get_player_id(self):
        return self.player_id

    def move(self, new_position):
        if not new_position.capture_position():
            return False
        self.current_position.free_position()
        self.current_position = new_position
        self.current_position.capture_position()
        return True

    def update(self, new_position, capture_points, health_points):
        if self.current_position is not None:
            self.current_position.free_position()
        self.current_position = new_position
        self.current_position.capture_position()
        self.capture_points = capture_points
        self.health_points = health_points

    def update_data(self, data):
        if self.current_position is not None:
            self.current_position.free_position()
        self.current_position = data["position"]
        self.current_position.capture_position()
        self.capture_points = data["capture_points"]
        self.health_points = data["health"]

    def shoot(self, vehicle):
        if self.opponent(vehicle):
            return vehicle.shoot_down(self.damage_points)
        return 0

    def opponent(self, vehicle):
        return self.player_id != vehicle.player_id

    def spawn_position(self, spawn_position):
        self.spawn_position = spawn_position
        self.current_position = self.spawn_position

    def get_spawn_position(self):
        return self.spawn_position.get_position()

    def get_current_position(self):
        return self.current_position.get_position()
    
    def repeat_spawn_position(self):
        if not self.move(self.spawn_position):
            raise RuntimeError("spawn position already occupied")
        self.health_points = self.max_health
        self.capture_points = 0

    def shoot_down(self, damage_points=1):
        self.health_points -= damage_points
        if self.health_points <= 0:
            return self.destruction_points
        return 0


class AtSpg(Vehicle):
    def __init__(self, player_id, health, spawn_position, position, capture_points):
        super().__init__(player_id, health, spawn_position, position, capture_points)
        self.max_health = 2
        self.speedPoints = 1
        self.destruction_points = 2


class MediumTank(Vehicle):
    def __init__(self, player_id, health, spawn_position, position, capture_points):
        super().__init__(player_id, health, spawn_position, position, capture_points)
        self.max_health = 2
        self.speedPoints = 2
        self.destruction_points = 2


class LightTank(Vehicle):
    def __init__(self, player_id, health, spawn_position, position, capture_points):
        super().__init__(player_id, health, spawn_position, position, capture_points)
        self.max_health = 1
        self.speedPoints = 3
        self.destruction_points = 1


class HeavyTank(Vehicle):
    def __init__(self, player_id, health, spawn_position, position, capture_points):
        super().__init__(player_id, health, spawn_position, position, capture_points)
        self.max_health = 3
        self.speedPoints = 1
        self.destruction_points = 2


class Spg(Vehicle):
    def __init__(self, player_id, health, spawn_position, position, capture_points):
        super().__init__(player_id, health, spawn_position, position, capture_points)
        self.max_health = 1
        self.speedPoints = 1
        self.destruction_points = 1
