from bot.bot_game_state import BotGameState
from game_client.actions import Action
from game_client.map_hexes import Base, Catapult, HardRepair, LightRepair
from game_client.server_interaction import ActionCode
from utility.custom_typings import MapDictTyping


class MCSTBotGameState(BotGameState):
    def __init__(self, game_map: MapDictTyping):
        super().__init__(game_map)

    def update_from_action(self, action: Action) -> None:
        if action.action_code == ActionCode.MOVE:
            self.__apply_move_action(action)

        if action.action_code == ActionCode.SHOOT:
            self.__apply_shoot_action(action)

        if action.action_code == ActionCode.TURN:
            self.__apply_turn_action()

    def __apply_turn_action(self) -> None:
        for vehicle in self.vehicles.values():
            gshex = self.get_hex(vehicle.position)
            player = self.players[vehicle.player_id]
            map_hex_type = type(gshex.map_hex)

            # Send back to spawn
            if vehicle.hp <= 0:
                self.__update_vehicle_pos(vehicle, vehicle.spawn_position)
                vehicle.hp = vehicle.max_hp

            # Repair vehicle
            elif map_hex_type in (LightRepair, HardRepair):
                if vehicle.__class__ in gshex.map_hex.served_classes:
                    vehicle.hp = vehicle.max_hp

            # Apply shooting range bonus
            elif map_hex_type is Catapult:
                vehicle.shoot_range_bonus = gshex.map_hex.use()

            # Add/remove capture points
            if map_hex_type is Base:
                vehicle.capture_points += 1
                player.win_points["capture"] += 1
            else:
                vehicle.capture_points = 0
                player.win_points["capture"] -= vehicle.capture_points
