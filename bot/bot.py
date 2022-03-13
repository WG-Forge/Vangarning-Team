from bot.bot_game_state import BotGameState
from game_client.actions import Action
from utility.custom_typings import GameStateDictTyping


class Bot:
    def __init__(self, game_map):
        self.game_state: BotGameState = BotGameState(game_map)

    def get_actions(self, game_state: GameStateDictTyping) -> list[Action]:
        raise NotImplementedError


# class SimpleBot(Bot):
#     def __init__(self, game_map):
#         super().__init__(game_map)
#         self.actions = []
#         self.base = []
#
#     def get_actions(self, game_state: dict):
#         """
#         Calculates action for current player's vehicles
#
#         :param game_state: Current state of game
#         :return: List of lists. Inner list structure: 0: ActionCode, 1: actor id, 2: data
#         """
#         self.actions = []
#
#         self.base = self.map["content"]["base"].copy()
#
#         # Gets order of actor actions and calculates action for every current player's actor
#         for vehicle_id, actor in self._get_vehicles_in_action_order(game_state):
#             # Shoot at actor with 1 hp
#             if self.__try_shoot_any_enemy(
#                 vehicle_id,
#                 game_state["vehicles"],
#                 game_state["attack_matrix"],
#                 lambda shooter, target: target["health"] == 1,
#             ):
#                 continue
#
#             # Try to move towards the base or shoot at obstacle
#             if self.__try_move_to_base(
#                 vehicle_id, game_state["vehicles"], game_state["attack_matrix"]
#             ):
#                 continue
#
#             # Vehicle is already on base, try to shoot any actor
#             self.__try_shoot_any_enemy(
#                 vehicle_id, game_state["vehicles"], game_state["attack_matrix"]
#             )
#
#         return self.actions
#
#     def __shoot(self, shooter_id, target_id, vehicles):
#         """
#         Makes a shot at target actor from shooter actor
#
#         :param shooter_id: Shooter actor's id
#         :param target_id: Target actor's id
#         :param vehicles: dict of all vehicles
#         """
#         shooter = vehicles[shooter_id]
#         target = vehicles[target_id]
#         # Shooter is at_spg type
#         if shooter["vehicle_type"] == "at_spg":
#             dx = target["position"]["x"] - shooter["position"]["x"]
#             dy = target["position"]["y"] - shooter["position"]["y"]
#             dz = target["position"]["z"] - shooter["position"]["z"]
#             # Shot normal
#             sx = 0 if dx == 0 else dx / abs(dx)
#             sy = 0 if dy == 0 else dy / abs(dy)
#             sz = 0 if dz == 0 else dz / abs(dz)
#             self.actions.append(
#                 [
#                     ActionCode.SHOOT,
#                     shooter_id,
#                     {
#                         "x": sx + shooter["position"]["x"],
#                         "y": sy + shooter["position"]["y"],
#                         "z": sz + shooter["position"]["z"],
#                     },
#                 ]
#             )
#             # Hexes affected by shot
#             aoe = [
#                 {
#                     "x": sx + shooter["position"]["x"],
#                     "y": sy + shooter["position"]["y"],
#                     "z": sz + shooter["position"]["z"],
#                 },
#                 {
#                     "x": 2 * sx + shooter["position"]["x"],
#                     "y": 2 * sy + shooter["position"]["y"],
#                     "z": 2 * sz + shooter["position"]["z"],
#                 },
#                 {
#                     "x": 3 * sx + shooter["position"]["x"],
#                     "y": 3 * sy + shooter["position"]["y"],
#                     "z": 3 * sz + shooter["position"]["z"],
#                 },
#             ]
#             # Vehicles at affected hexes
#             for actor in vehicles.values():
#                 if shooter["player_id"] == actor["player_id"]:
#                     continue
#                 if actor["position"] in aoe:
#                     actor["health"] -= 1
#         else:
#             self.actions.append([ActionCode.SHOOT, shooter_id, target["position"]])
#             target["health"] -= 1
#
#     def __try_shoot_any_enemy(
#         self,
#         shooter_id,
#         vehicles,
#         attack_matrix,
#         function=lambda shooter, target: True,
#     ):
#         """
#         Tries to shoot any enemy actor in the game
#
#         :param shooter_id: id of shooter actor
#         :param vehicles: dict of all vehicles
#         :param attack_matrix:
#         :param function: Optional condition
#         :return: True if the shot was successful, False if not
#         """
#
#         # Gets generator for all possible targets
#         shoot_targets = filter(
#             lambda target_id: self.__can_shoot(
#                 vehicles[shooter_id], vehicles[target_id], attack_matrix
#             )
#             and function(vehicles[shooter_id], vehicles[target_id]),
#             vehicles,
#         )
#
#         shoot_target_id = next(shoot_targets, None)
#         # No possible targets found
#         if shoot_target_id is None:
#             return False
#
#         self.__shoot(shooter_id, shoot_target_id, vehicles)
#         return True
#
#     def __try_move_to_base(self, vehicle_id, vehicles, attack_matrix):
#         """
#         Tries to move actor towards the base, if not possible, shoots at obstacle
#         :param vehicle_id: Moving actor
#         :param vehicles: dict of all vehicles
#         :param attack_matrix:
#         :return: True if action was made, False if not
#         """
#         actor = vehicles[vehicle_id]
#
#         # Closest base hex to the actor
#
#         closest_base = min(
#             self.base, key=lambda base_hex: self._dist(base_hex, actor["position"])
#         )
#         self.base.remove(closest_base)
#
#         # Vehicle is already at the base hex
#         if closest_base == actor["position"]:
#             return False
#
#         # Finds closest reachable hex to the base hex
#         closest_hex_to_base = actor["position"]
#         min_dist = self.map["size"]
#         for hex in self.__get_hexes(
#             actor["position"], 0, TANK_TYPE[actor["vehicle_type"]]["speed"]
#         ):
#             dist = self._dist(hex, closest_base)
#             if dist >= min_dist:
#                 continue
#
#             hex_is_blocked = False
#             for other_vehicle in vehicles.values():
#                 # Hex is blocked, can't shoot
#                 if other_vehicle["position"] == hex and not self.__can_shoot(
#                     actor, other_vehicle, attack_matrix
#                 ):
#                     hex_is_blocked = True
#                     break
#
#             if not hex_is_blocked:
#                 min_dist = dist
#                 closest_hex_to_base = hex
#
#         # Found hex is blocked, shoot at blocking actor
#         for other_vehicle_id, other_vehicle in vehicles.items():
#             if other_vehicle["position"] == closest_hex_to_base:
#                 self.__shoot(vehicle_id, other_vehicle_id, vehicles)
#                 return True
#
#         # Hex is free, actor moving to it
#         if actor["position"] != closest_hex_to_base:
#             self.actions.append(
#                 [ActionCode.MOVE, vehicle_id, closest_hex_to_base.copy()]
#             )
#             actor["position"] = closest_hex_to_base
#             return True
#         return False
#
#     def __get_hexes(self, origin, min_dist, max_dist):
#         """
#         Generator that yields hexes at given distance from given hex
#
#         :param origin: hex at a distance from which other hexes are generated
#         :param min_dist: minimal distance from origin
#         :param max_dist: maximum distance from origin
#         :return:
#         """
#         for x in range(-max_dist, max_dist + 1):
#             for y in range(
#                 max(-max_dist, -max_dist - x), min(max_dist + 1, max_dist - x + 1)
#             ):
#                 z = -x - y
#                 hex_pos = {
#                     "x": origin["x"] + x,
#                     "y": origin["y"] + y,
#                     "z": origin["z"] + z,
#                 }
#
#                 if self._dist(hex_pos, {"x": 0, "y": 0, "z": 0}) > self.map["size"]:
#                     continue
#                 if self._dist(hex_pos, origin) < min_dist:
#                     continue
#                 yield hex_pos
#
#     def __can_shoot(self, shooter, target, attack_matrix):
#         """
#         Checks if it possible to shoot at given target
#
#         :param shooter: Shooting actor
#         :param target: Target actor
#         :param attack_matrix:
#         :return: True if possible, False if not
#         """
#         # Both vehicles belong to the same player
#         if shooter["player_id"] == target["player_id"]:
#             return False
#         # Target is already destroyed
#         if target["health"] <= 0:
#             return False
#         # Target out of range
#         if not self.__distance_check(shooter, target):
#             return False
#
#         # Neutrality check
#         return self.__neutrality_check(shooter, target, attack_matrix)
#
#     def __distance_check(self, shooter, target):
#         """
#         Check if target actor is in shooting range of shooter actor
#
#         :param shooter: Shooter actor
#         :param target: Target actor
#         :return: True if in range, False if not
#         """
#         # Regular actor check
#         dist = self._dist(shooter["position"], target["position"])
#         min_shooting_range = TANK_TYPE[shooter["vehicle_type"]]["min_shooting_range"]
#         max_shooting_range = TANK_TYPE[shooter["vehicle_type"]]["max_shooting_range"]
#
#         if not (min_shooting_range <= dist <= max_shooting_range):
#             return False
#
#         # AT_SPG range check
#         if shooter["vehicle_type"] == "at_spg":
#             dx = target["position"]["x"] - shooter["position"]["x"]
#             dy = target["position"]["y"] - shooter["position"]["y"]
#             dz = target["position"]["z"] - shooter["position"]["z"]
#             if dx != 0 and dy != 0 and dz != 0:
#                 return False
#
#         return True
#
#     def __neutrality_check(self, shooter, target, attack_matrix):
#         """
#         Checks if shooter actor can't shoot at target actor due to neutrality rule
#
#         :param shooter: Shooter actor
#         :param target: Target actor
#         :param attack_matrix:
#         :return: True if shot is possible, False if not
#         """
#         shooter_pid = shooter["player_id"]
#         target_pid = target["player_id"]
#
#         # Shooter wasn't attacked by target on the last turn
#         if shooter_pid not in attack_matrix[str(target_pid)]:
#             # Target was attacked by other player on the last turn
#             for player_id, prev_targets in attack_matrix.items():
#                 if player_id != str(shooter_pid) and target_pid in prev_targets:
#                     return False
#         return True
