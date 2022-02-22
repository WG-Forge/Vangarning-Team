import time

from bot import Bot
from game_client import BotGameState


# TODO: asynchronous programming
class MCTSBot(Bot):
    def __init__(self, game_map, simulation_bot: Bot, time_limit):
        super().__init__(game_map)
        self.simulation_bot = simulation_bot
        self.time_limit = time_limit
        self.allied_vehicles = []
        self.enemy_vehicles = []  # TODO: remove?
        self.game_state = None
        self.tree = None

    def get_actions(self, game_state: BotGameState, previous_actions=None):
        if previous_actions is not None:
            self.advance_tree(previous_actions)
        if self.tree.root is None or self.game_state != game_state:
            self.game_state = game_state
            # TODO: create tree
        self.allied_vehicles = list(
            filter(
                lambda vehicle: vehicle.player_id == game_state.current_player_idx,
                game_state.vehicles,
            )
        )
        self.enemy_vehicles = list(
            filter(
                lambda vehicle: vehicle.player_id != game_state.current_player_idx,
                game_state.vehicles,
            )
        )

        single_vehicle_time_limit = self.time_limit / len(self.allied_vehicles)

        actions = []
        for vehicle in self.allied_vehicles:
            action = self.__get_action(vehicle, single_vehicle_time_limit)
            self.__advance_tree(action)
            actions.append(action)
        # TODO: transform actions
        return actions

    # TODO: multithreading
    def __get_action(self, actor, time_limit):
        end_time = time.time_ns() + time_limit
        while time.time_ns() < end_time:
            self.__research_node()
        recommended_action_node = max(
            self.tree.root.children, key=lambda node: node.am_visited
        )
        return recommended_action_node.data

    def __research_node(self):
        node = self.tree.choice(self.tree.root)  # TODO: return game_state?
        if node.child is not None:
            self.tree.expansion(node)  # TODO: pass game_state?
        winner_id = self.tree.simulation(
            node, self.simulation_bot
        )  # TODO: pass game_state?
        self.tree.back_propagation(node, winner_id)

    def advance_tree(self, actions: list):
        for action in actions:
            # TODO: transform action
            self.__advance_tree(action)
            if self.tree.root is None:
                break

    def __advance_tree(self, action):
        node = self.tree.root.child
        new_root = None
        while node is not None:
            if node.data == action:
                new_root = node
                break
            node = node.sibling
        self.tree.root = new_root
