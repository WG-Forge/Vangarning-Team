# pylint: skip-file
# Still work in progress
import math
from struct import pack, unpack

from bot.actions_generator import ActionsGenerator
from bot.bot import Bot
from bot.mcst.mcst_bot_game_state import MCSTBotGameState
from game_client.actions import Action, ActionCode
from utility.coordinates import Coords


def action_to_bytestring(action: Action, game_state: MCSTBotGameState):
    return pack(
        "cccccccccc",
        action.action_code.value,
        action.actor.vehicle_id,
        action.target,
        0,
        # TODO: get vehicle count
        game_state.current_player.idx,
        action.affected_vehicles,
    )


def bytestr_to_action(bytestr: bytes, game_state: MCSTBotGameState):
    unpacked = unpack("cccccccccc", bytestr)
    affected_vehicles = []
    for i in range(7, len(unpacked)):
        affected_vehicles.append(find_vehicle(game_state.vehicles, unpacked[i]))
    return Action(
        ActionCode(unpacked[0]),
        find_vehicle(game_state.vehicles, unpacked[1]),
        Coords((unpacked[2], unpacked[3], unpacked[4])),
        affected_vehicles,
    )


def get_current_player(bytestr: bytes):
    return bytestr[6]


def get_next_vehicle(bytestr: bytes):
    return (bytestr[5] + 1) % 5


def find_vehicle(vehicles, id):
    return next(
        filter(lambda vehicle: vehicle.vehicle_id == id, vehicles.values()), None
    )


class MCSTNode:
    def __init__(self, parent, action: bytes, child=None, sibling=None):
        self.parent: MCSTNode = parent
        self.child: MCSTNode = child
        self.sibling: MCSTNode = sibling
        self.am_visited = 0
        self.am_wins = 0
        self.action: bytes = action

    def children(self):
        node = self.child
        while node is not None:
            yield node
            node = node.sibling

    def have_all_children(self):
        return all((child.am_visited > 0 for child in self.children()))

    def get_new_child(self):
        # returns random children
        return next(filter(lambda child: child.am_visited == 0, self.children()))

    def get_most_valuable_child(self):
        return max(self.children(), key=lambda node: node.get_uct())

    def get_uct(self):
        result = self.am_wins / self.am_visited
        result += math.sqrt(2 * math.log(self.parent.am_visited) / self.am_visited)
        return result


class MonteCarloSearchTree:
    def __init__(self, game_state: MCSTBotGameState, bot: Bot):
        self.root: MCSTNode = MCSTNode(None, bytes())
        self.bot: Bot = bot
        self.game_state: MCSTBotGameState = game_state
        self.action_generator = ActionsGenerator(game_state)

    def selection(self) -> (MCSTNode, MCSTBotGameState):
        node = self.root
        game_state = self.game_state  # TODO: copy game_state
        while not game_state.finished and node.have_all_children():
            node = node.get_most_valuable_child()

            action = bytestr_to_action(node.action, game_state)
            game_state.update_from_action(action)  # TODO: update from action
        return node, game_state

    def expansion(self, node: MCSTNode, game_state: MCSTBotGameState):
        new_node = node.get_new_child()

        action = bytestr_to_action(node.action, game_state)
        game_state.update_from_action(action)  # TODO: update_from_action

        self.action_generator.game_state = game_state
        vehicles = game_state.current_player.ordered_vehicle_iter
        vehicle = next(vehicles)
        for i in range(get_next_vehicle(node.action)):
            vehicle = next(vehicles)

        possible_steps = self.action_generator(vehicle)  # TODO: get possible steps
        child = None
        for action in possible_steps:
            bytestr = action_to_bytestring(action)
            child = MCSTNode(new_node, bytestr, sibling=child)
        new_node.child = child
        return new_node, game_state

    def playout(self, game_state: MCSTBotGameState):
        while not game_state.finished:
            for action in self.bot.get_actions(game_state):  # TODO: change interface
                game_state.update_from_action(action)  # TODO: update from action
        return game_state.winner  # TODO: get winner

    def backpropagation(self, node: MCSTNode, winner):
        while node.parent is not None:
            node.am_visited += 1
            if (
                get_current_player(node.action) == winner
            ):  # TODO: determine which player made a move
                node.am_wins += 1
