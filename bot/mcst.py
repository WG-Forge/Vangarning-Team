import math
import random
from timeit import default_timer as timer

from bot import SimpleBot
from settings import TYPE_ORDER


def get_possible_actions(game_state, vehicle_id):
    # return possible actions of the actor
    pass


def apply_action(game_state, action) -> dict:
    # apply action to game_state
    pass


def switch_turn(game_state) -> dict:
    # switch turn to the next player
    pass


class MCSTNode:
    def __init__(self, game_state, parent, vehicles_id_already_moved: set):
        self.game_state = game_state
        self.parent = parent
        self.children = None
        self.visits = 0
        # stores the vehicles of the current player that already made an action
        self.vehicles_id_already_moved = vehicles_id_already_moved
        if (
            parent is not None
            and parent.game_state["current_player_idx"]
            != game_state["current_player_idx"]
        ):
            self.vehicles_id_already_moved = set()
            self.game_state = switch_turn(self.game_state)
        self.my_vehicle_id = self._get_my_vehicle_id()
        self.wins = 0

    def is_terminal(self):
        # returns True if this state doesn't have children
        return self.game_state["finished"]

    def _get_my_vehicle_id(self):
        # gets the id of actor for which you should choose action
        vehicles = self.game_state["vehicles"]
        player_id = self.game_state["current_player_idx"]
        all_vehicles = sorted(
            [i for i in vehicles.items() if i[1]["player_id"] == player_id],
            key=lambda vehicle: TYPE_ORDER.index(vehicle[1]["vehicle_type"]),
        )
        for vehicle_id, vehicle in all_vehicles:
            if vehicle_id not in self.vehicles_id_already_moved:
                return vehicle_id
        return None

    def _init_children(self):
        # lazy initialization of children
        if self.children is not None:
            return
        for_child_already_moved = self.vehicles_id_already_moved.copy()
        for_child_already_moved.add(self.my_vehicle_id)
        possible_actions = get_possible_actions(self.game_state, self.my_vehicle_id)
        for action in possible_actions:
            child = MCSTNode(
                apply_action(self.game_state, action), self, for_child_already_moved
            )
            self.children.append((action, child))

    def have_all_children(self):
        # checks that we have visited all children
        self._init_children()
        return all((child.visits > 0 for action, child in self.children))

    def get_random_child(self):
        # returns random children
        self._init_children()
        return random.choice(self.children)[1]

    def get_most_valuable_child(self):
        # gets child with the most UCT score
        self._init_children()
        best_action, best_child = self.children[0]
        for action, child in self.children:
            if child.visits == 0:
                continue
            if best_child.visits == 0 or best_child.get_UCT() < child.get_UCT():
                best_action, best_child = action, child
        return best_action, best_child

    def get_uct(self):
        assert self.visits > 0
        result = self.wins / self.visits
        if self.parent is not None:
            result += math.sqrt(2 * math.log(self.parent.visits) / self.visits)
        return result

    def backpropagation(self, winner_id):
        # propagate winner_id to parents
        if self.parent is None:
            return
        self.visits += 1
        if self.parent.game_state["current_player_idx"] == winner_id:
            self.wins += 1


# creates new root every turn, because game_state not hashable
class MonteCarloSearchTree:
    def __init__(self, game_state, bot):
        self.root = MCSTNode(game_state, None, set())
        self.bot = bot

    def choice(self):
        # go down the tree before met terminal node or node which has unvisited child
        node = self.current_node
        while not node.is_terminal() and node.have_all_children():
            node = node.get_most_valuable_child()
        if not node.is_terminal():
            return node.get_random_child()
        return node

    def simulation(self, node):
        # get actions from the bot for the rest of actor of current player
        # switch turn, and determine the winner
        game_state = node.game_state
        vehicles = game_state["vehicles"]
        player_id = game_state["current_player_idx"]
        all_vehicles = sorted(
            [i for i in vehicles.items() if i[1]["player_id"] == player_id],
            key=lambda vehicle: TYPE_ORDER.index(vehicle[1]["vehicle_type"]),
        )
        for vehicle_id, vehicle in all_vehicles:
            if vehicle_id not in node.vehicles_id_already_moved:
                action = self.bot.get_action_for_vehicle(game_state, vehicle_id)
                game_state = apply_action(game_state, action)
        game_state = switch_turn(game_state)
        while not game_state["finished"]:
            for action in self.bot.get_actions(game_state):
                game_state = apply_action(game_state, action)
        game_state = switch_turn(game_state)
        return game_state["winner"]

    def get_move(self, timeout):
        # do choice and simulation before timeout
        time_elapsed = 0
        while time_elapsed < timeout:
            start = timer()
            node = self.choice()
            winner_id = self.simulation(node)
            node.back_propagation(winner_id)
            time_elapsed += timer() - start
        action, child = self.current_node.get_most_valuable_child()
        self.current_node = child
        return action


class AdvancedBot:
    def __init__(self, game_map):
        self.simple_bot = SimpleBot(game_map)

    def get_actions(self, game_state: dict, timeout):
        tree = MonteCarloSearchTree(game_state, self.simple_bot)
        actions = []
        vehicles = game_state["vehicles"]
        player_id = game_state["current_player_idx"]
        all_vehicles = sorted(
            [i for i in vehicles.items() if i[1]["player_id"] == player_id],
            key=lambda vehicle: TYPE_ORDER.index(vehicle[1]["vehicle_type"]),
        )
        for i in range(len(all_vehicles)):
            actions.append(tree.get_action(), timeout / len(all_vehicles))

        return actions
