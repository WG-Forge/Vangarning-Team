from queue import PriorityQueue

import hex
from bot import Bot
from server_interaction import ActionCode, GameSession
from settings import NEIGHBOURS_OFFSETS, TYPE_ORDER, HexCode
from vehicle import AtSpg, HeavyTank, LightTank, MediumTank, Spg, Vehicle

TYPES_TO_CLASSES = {
    "at_spg": AtSpg,
    "heavy_tank": HeavyTank,
    "light_tank": LightTank,
    "medium_tank": MediumTank,
    "spg": Spg,
}

from time import perf_counter_ns


def time_ns(func):
    def wrapper(*args, **kwargs):
        a = perf_counter_ns()
        result = func(*args, **kwargs)
        b = perf_counter_ns()
        print(func.__name__, b - a)
        return result

    return wrapper


class BotGameState:
    """
    Keeps info about game map and state that can be useful for bot.

    """

    def __init__(self, game_map: dict):
        # Map info
        self.map_radius: int = game_map["size"]
        self.map_name: str = game_map["name"]
        self.base, self.obstacles = self.__parse_map_content(game_map)
        self.spawn_positions: set = set()

        # Game state info
        self.players: list[dict] = []
        self.num_turns: int = -1
        self.current_turn: int = -1
        self.current_player_idx: int = -1
        self.win_points: dict[str, dict] = {}
        self.vehicles: dict[str, Vehicle] = {}
        self.vehicles_to_players: dict = {}
        self.vehicles_positions: dict[tuple, str] = {}

    def update(self, game_state: dict) -> None:
        """
        Updates instance from game_state.

        :param game_state: GAME_STATE response from the server
        :return: None
        """
        # if game state info is not populated
        if not self.vehicles_to_players:
            self.num_turns = game_state["num_turns"]
            self.players = [
                player for player in game_state["players"] if not player["is_observer"]
            ]

            for player in self.players:
                self.vehicles_to_players[player["idx"]] = []

            self.__create_vehicles(
                self.__get_order_sorted_vehicles(game_state["vehicles"])
            )

        else:
            self.__update_vehicles(game_state["vehicles"])

        self.current_turn = game_state["current_turn"]
        self.current_player_idx = game_state["current_player_idx"]
        self.win_points = game_state["win_points"]

    def update_from_action(self, action: tuple):
        action_code, vehicle_id, target = action
        target = tuple(target.values())
        actor: Vehicle = self.get_vehicle(vehicle_id)
        if action_code == ActionCode.MOVE:
            del self.vehicles_positions[actor.position]
            actor.position = tuple(target)
            self.vehicles_positions[actor.position] = actor.pid

        elif action_code == ActionCode.SHOOT:
            if not isinstance(actor, AtSpg):
                enemy = self.get_vehicle(self.get_hex_value(target))
                enemy.health_points -= actor.damage
            else:
                normal = hex.normal(actor.position, tuple(target))

                for i in range(1, 4):
                    offset_coords = hex.multiply(i, normal)
                    if offset_coords in self.obstacles:
                        break

                    offset_value = self.get_hex_value(offset_coords)
                    if int(offset_value) >= 1:
                        self.get_vehicle(offset_value).health_points -= actor.damage

    def get_vehicle(self, vehicle_id: str) -> Vehicle:
        return self.vehicles[vehicle_id]

    # noinspection PyTypeChecker
    def __get_order_sorted_vehicles(
        self, vehicles: dict[str, dict]
    ) -> list[tuple[str, dict]]:
        """
        Sorts vehicles by type in the following order: SPG, LT, HT, MT, AT SPG.

        :param vehicles: dict with vehicle id as key and its' data as value
        :return: sorted list of tuples (vehicle_id, vehicle_data)
        """
        return sorted(
            vehicles.items(),
            key=lambda vehicle: TYPE_ORDER.index(vehicle[1]["vehicle_type"]),
        )

    def __create_vehicles(self, vehicles: list[tuple[str, dict]]) -> None:
        """
        Creates Vehicle objects and stores info about them in instance's attributes.

        :param vehicles: sorted by step order list of tuples (vehicle_id, vehicle_data)
        :return: None
        """
        for vid, vehicle in vehicles:
            vehicle_obj = TYPES_TO_CLASSES[vehicle["vehicle_type"]](
                vehicle["player_id"],
                vid,
                vehicle["health"],
                tuple(vehicle["spawn_position"].values()),
                tuple(vehicle["position"].values()),
                vehicle["capture_points"],
            )
            self.vehicles_to_players[vehicle_obj.player_id].append(vid)
            self.vehicles_positions[vehicle_obj.position] = vid
            self.vehicles[vid] = vehicle_obj
            self.spawn_positions.add(vehicle_obj.spawn_position)

    def __update_vehicles(self, vehicles: dict[str, dict]) -> None:
        """
        Updates information about vehicles.

        :param vehicles: "vehicles" part of GAME_STATE response from the server
        :return: None
        """
        for vid, vehicle in vehicles.items():
            del self.vehicles_positions[self.vehicles[vid].position]
            self.vehicles[vid].update(vehicle)
            self.vehicles_positions[tuple(vehicle["position"].values())] = vid

    def a_star_search(self, start, target):
        frontier = PriorityQueue()
        frontier.put(start, False)
        came_from = {start: None}
        cost_so_far = {start: 0}

        while not frontier.empty():
            current = frontier.get()

            if current == target:
                break

            for next_hex in self._get_neighbours(current):
                new_cost = cost_so_far[current] + (
                    1 if next_hex not in self.obstacles else 2000000
                )
                if next_hex not in cost_so_far or new_cost < cost_so_far[next_hex]:
                    cost_so_far[next_hex] = new_cost
                    priority = new_cost + (
                        sum(map(lambda x: x[0] - x[1], zip(next_hex, target)))
                    )
                    frontier.put(next_hex, priority)
                    came_from[next_hex] = current

        return cost_so_far[target]

    def _can_reach(self, max_len, start, target):
        if hex.straight_dist(start, target) > max_len:
            return False

        # delta = hex.delta(start, target)
        return self.a_star_search(start, target) <= max_len

    def __parse_map_content(self, game_map: dict) -> tuple[set[tuple], set[tuple]]:
        obstacles = set(tuple(i.values()) for i in game_map["content"]["obstacle"])
        base = set(tuple(i.values()) for i in game_map["content"]["base"])

        return base, obstacles

    def are_valid_coords(self, coords):
        return max(map(abs, coords)) < self.map_radius

    def is_enemy_tank(self, position):
        hex_id = self.get_hex_value(position)
        return (
            int(hex_id) >= 1
            and hex_id not in self.vehicles_to_players[self.current_player_idx]
        )

    def can_move(self, actor: Vehicle, target: tuple):
        # target is someone else's spawn position
        if target in self.spawn_positions and target != actor.spawn_position:
            return False
        # target is obstacle
        if target in self.obstacles:
            return False
        # target is occupied by another vehicle
        if int(self.get_hex_value(target)) >= 1:
            return False

        return self._can_reach(actor.speed_points, actor.position, target)

    def can_shoot(self, actor, coords):
        hex_status = self.get_hex_value(coords)
        # if not self.is_enemy_tank(hex_status):
        #     print("_____________is enemy____________")
        #     return False
        # if not actor.is_target_in_shooting_range(coords):
        #     print("_____________in range____________")
        #     return False
        # if not self.get_vehicle(hex_status).health_points > 0:
        #     print("_____________has hp____________")
        #     return False
        #
        # return True
        return (
            self.is_enemy_tank(hex_status)
            and actor.is_target_in_shooting_range(coords)
            and self.get_vehicle(hex_status).health_points > 0
        )

    def get_hex_value(self, coords):
        try:
            hex_status = self.vehicles_positions[coords]
        except KeyError:
            if coords in self.base:
                hex_status = HexCode.BASE
            elif coords in self.obstacles:
                hex_status = HexCode.OBSTACLE
            else:
                hex_status = HexCode.EMPTY

        return hex_status

    def _get_neighbours(self, coords):
        neighbours = []

        for offset in NEIGHBOURS_OFFSETS[0]:
            neighbour = hex.summarize(coords, offset)
            if self.are_valid_coords(neighbour):
                neighbours.append(neighbour)

        return neighbours

    def get_close_enemies(self, actor):
        enemies = []
        for dist in NEIGHBOURS_OFFSETS:
            for offset in dist:
                hex_value = self.get_hex_value(hex.summarize(actor.position, offset))
                if int(hex_value) >= 1:
                    enemy = self.vehicles[hex_value]
                    if self.can_shoot(enemy, actor.position):
                        enemies.append(enemy)

        return enemies

    @property
    def current_player_vehicles(self):
        return [
            self.vehicles[i] for i in self.vehicles_to_players[self.current_player_idx]
        ]


def game_loop(bot: Bot, game: GameSession):
    """
    Plays the given game with the given bot.

    :param bot:
    :param game:
    :return:
    """
    while game_tick(bot, game) is not None:
        pass


def game_tick(bot: Bot, game: GameSession):
    """
    Performs full turn in the game
    :param bot:
    :param game:
    :return:
    """
    game_state = game.game_state()

    if game_state["finished"]:
        print("You won" if game_state["winner"] == game.player_id else "You lost")
        print(f"Winner: {game_state['winner']}")
        return None

    if game_state["current_player_idx"] == game.player_id:
        print(f'Round: {game_state["current_turn"]}, ' f"player: {game.player_name}")
        for action in bot.get_actions(game_state):
            game.action(*action)
            print(
                f"  Action: "
                f'{"shoot" if action[0] == ActionCode.SHOOT else "move"}'
                f" Actor: {action[1]} Target: {action[2]}"
            )

    game.turn()
    return game_state


if __name__ == "__main__":
    from step_score_bot import StepScoreBot

    g = GameSession(name="Boris")
    bot = StepScoreBot(g.map)
    game_loop(bot, g)
