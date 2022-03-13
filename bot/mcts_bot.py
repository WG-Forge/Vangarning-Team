import time
from os import cpu_count
from multiprocessing import Pool
from queue import Queue

from bot.bot import Bot
from bot.mcst_bot_game_state import MCSTBotGameState
from bot.mcst import MonteCarloSearchTree, MCSTNode, action_to_bytestring, bytestr_to_action
from game_client.actions import Action




# TODO: async
class MCTSBot(Bot):
    def __init__(self, game_map, simulation_bot: Bot, time_limit):
        super().__init__(game_map)
        self.simulation_bot = simulation_bot
        self.time_limit = time_limit
        self.tree: MonteCarloSearchTree = MonteCarloSearchTree(None, simulation_bot)
        self.queue = Queue(maxsize=cpu_count())
        self.pool = Pool(initializer=self.__worker)
        self.produce = False

    def __worker(self):
        while True:
            task = self.queue.get()
            task()

    def __producer(self):
        while self.produce:
            self.queue.put(item=self.__research_node)

    def start_researching(self):
        self.produce = True
        self.queue.put(self.__producer())

    def stop_researching(self):
        self.produce = False

    def get_actions(self, game_state: MCSTBotGameState, previous_actions=None):
        if previous_actions is not None:
            self.advance_tree(previous_actions)

        if self.tree.root is None:
            self.tree.game_state = game_state
            self.tree.root = MCSTNode(None, bytes())
        if self.tree.game_state != game_state:
            pass
            # TODO: exception

        single_vehicle_time_limit = self.time_limit / len(list(game_state.current_player.ordered_vehicle_iter))

        actions: list[Action] = []
        for vehicle in self.tree.game_state.current_player.ordered_vehicle_iter:
            action = self.__get_action(vehicle, single_vehicle_time_limit)
            self.__advance_tree(action)
            actions.append(bytestr_to_action(action, game_state))
        return actions

    def __get_action(self, actor, time_limit):
        end_time = time.time_ns() + time_limit
        while time.time_ns() < end_time:
            self.queue.put(item=self.__research_node)

        recommended_action_node = max(
            self.tree.root.children(), key=lambda node: node.am_visited
        )
        return recommended_action_node.action

    def __research_node(self):
        node, game_state = self.tree.selection()
        if not game_state.finished:
            node, game_state = self.tree.expansion(game_state, node)
        winner_id = self.tree.playout(game_state)
        self.tree.backpropagation(node, winner_id)

    def advance_tree(self, actions: list[Action], game_state: MCSTBotGameState):
        for action in actions:
            game_state.update_from_action(action)
            bytestr_action = action_to_bytestring(action, game_state)
            self.__advance_tree(bytestr_action)
            if self.tree.root is None:
                break

    def __advance_tree(self, action: bytearray):
        new_root = None
        for node in self.tree.root.children():
            if node.action == action:
                new_root = node
                break
        self.tree.root = new_root
