import os

os.environ["KIVY_NO_ARGS"] = "1"
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.properties import ListProperty, NumericProperty, ObjectProperty
from kivy.uix.widget import Widget

from game_client import game_tick

COLORS = {
    "black": [0, 0, 0],
    "grey": [0.5, 0.5, 0.5],
    "white": [1, 1, 1],
    "red": [1, 0, 0],
    "green": [0, 1, 0],
    "blue": [0, 0, 1],
}
HEX_SIZE = 15
VEHICLE_TYPES_TO_SPRITES = {
    "at_spg": "assets/AT_SPG.png",
    "heavy_tank": "assets/HT.png",
    "light_tank": "assets/LT.png",
    "medium_tank": "assets/MT.png",
    "spg": "assets/SPG.png",
}


def cube_to_cartesian(x, y, z):
    return x * 1.5, (y - z) * 0.866025


class HPBar(Widget):
    max_hp = NumericProperty(0)
    hp = NumericProperty(0)

    def update(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(1, 1, 1, 0.5)
            Rectangle(pos=self.pos, size=self.size)
            Color(0, 1, 0, 1)
            for i in range(self.hp):
                Rectangle(
                    pos=(
                        self.x
                        + self.outline_width
                        + i * (self.single_bar_size[0] + self.outline_width),
                        self.y + self.outline_width,
                    ),
                    size=self.single_bar_size,
                )


class Vehicle(Widget):
    hp_bar = ObjectProperty(0)
    color = ListProperty([0, 0, 0])

    def __init__(self):
        super(Vehicle, self).__init__()
        self.hp_bar.bind(hp=self.hp_bar.update)
        self.bind(center=self.hp_bar.update)
        self.property("hp_bar").dispatch(self)


class Hex(Widget):
    side = NumericProperty(0)
    color = ListProperty([0, 0, 0])


class WoTStrategyRoot(Widget):
    hexes = []
    vehicles = {}
    not_used_colors = [COLORS["red"], COLORS["green"], COLORS["blue"]]
    ids_to_colors = {}

    def add_vehicle(self, id, vehicle_data):
        if vehicle_data["player_id"] not in self.ids_to_colors.keys():
            self.ids_to_colors[vehicle_data["player_id"]] = self.not_used_colors[0]
            self.not_used_colors.remove(self.not_used_colors[0])
        vehicle = Vehicle()
        # TODO: get max hp from local files, not server response
        vehicle.hp_bar.max_hp = vehicle_data["health"]
        vehicle.color = self.ids_to_colors[vehicle_data["player_id"]]

        vehicle.file = VEHICLE_TYPES_TO_SPRITES[vehicle_data["vehicle_type"]]

        pos_dict = vehicle_data["position"]
        pos_x, pos_y = cube_to_cartesian(pos_dict["x"], pos_dict["y"], pos_dict["z"])
        pos_x, pos_y = pos_x * HEX_SIZE, pos_y * HEX_SIZE
        self.vehicles[id] = [pos_x, pos_y, vehicle]
        vehicle.center = self.width / 2 + pos_x, self.height / 2 + pos_y

        self.add_widget(vehicle)

    def create_map(self, map_data: dict):
        for x in range(-map_data["size"], map_data["size"] + 1):
            for y in range(
                    max(-map_data["size"], -map_data["size"] - x),
                    min(map_data["size"] + 1, map_data["size"] - x + 1),
            ):
                z = -x - y
                hex = Hex()

                pos_x, pos_y = cube_to_cartesian(x, y, z)
                pos_x, pos_y = pos_x * hex.side, pos_y * hex.side
                hex.center = self.width / 2 + pos_x, self.height / 2 + pos_y

                color = COLORS["grey"]
                hex_cube = {"x": x, "y": y, "z": z}
                if hex_cube in map_data["content"]["base"]:
                    color = COLORS["white"]
                if hex_cube in map_data["content"]["obstacle"]:
                    color = COLORS["black"]
                hex.color = color
                self.hexes.append((pos_x, pos_y, hex))
                self.add_widget(hex)

    def size_setter(self, instance, width, height):
        self.pos = (width, height)
        for pos_x, pos_y, hex in self.hexes:
            hex.center = pos_x + self.width / 2, pos_y + self.height / 2
        for pos_x, pos_y, vehicle in self.vehicles.values():
            vehicle.center = pos_x + self.width / 2, pos_y + self.height / 2
            vehicle.hp_bar.update()

    def update_vehicles(self, vehicles_data):
        for id, vehicle_data in vehicles_data.items():
            if id not in self.vehicles:
                self.add_vehicle(id, vehicle_data)
            pos_dict = vehicle_data["position"]
            pos_x, pos_y = cube_to_cartesian(
                pos_dict["x"], pos_dict["y"], pos_dict["z"]
            )
            pos_x, pos_y = pos_x * HEX_SIZE, pos_y * HEX_SIZE
            x_y_vehicle = self.vehicles[id]
            x_y_vehicle[0] = pos_x
            x_y_vehicle[1] = pos_y
            x_y_vehicle[2].center = pos_x + self.width / 2, pos_y + self.height / 2
            x_y_vehicle[2].hp_bar.hp = vehicle_data["health"]
            x_y_vehicle[2].hp_bar.update()


class WoTStrategyApp(App):
    """
    To run game with gui: WotStrategyApp(...).run()
    """

    def __init__(self, map_data, bot, game_session):
        """

        :param map_data: map dict from server
        :param bot: bot that will be used to choose actions
        :param game_session:
        """
        super().__init__()
        self.map_data = map_data
        self.bot = bot
        self.game_session = game_session

    def build(self):
        root = WoTStrategyRoot()
        Window.bind(on_resize=root.size_setter)
        root.size = Window.size

        root.create_map(self.map_data)

        Clock.schedule_once(self.tick, 0)
        return root

    def tick(self, dt):
        new_state = game_tick(self.bot, self.game_session)
        if new_state is None:
            return
        self.root.update_vehicles(new_state["vehicles"])
        Clock.schedule_once(self.tick, 0)
