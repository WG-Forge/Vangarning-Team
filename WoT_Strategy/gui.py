"""
Handles graphic interface
"""

import os

os.environ["KIVY_NO_ARGS"] = "1"
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import (
    ListProperty,
    NumericProperty,
    ObjectProperty,
    ReferenceListProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scatter import Scatter
from kivy.uix.widget import Widget

from settings import CoordsTuple, CoordsDict
from game_client import game_tick
from hex import tuple_to_dict, dict_to_tuple

COLORS = {
    "black": (0, 0, 0),
    "grey": (0.5, 0.5, 0.5),
    "white": (1, 1, 1),
    "red": (1, 0, 0),
    "green": (0, 1, 0),
    "blue": (0, 0, 1),
}
VEHICLE_TYPES_TO_SPRITES = {
    "at_spg": "assets/AT_SPG.png",
    "heavy_tank": "assets/HT.png",
    "light_tank": "assets/LT.png",
    "medium_tank": "assets/MT.png",
    "spg": "assets/SPG.png",
}
SPECIAL_HEXES_TO_SPRITES = {
    "light_repair": "assets/light_repair.png",
    "hard_repair": "assets/hard_repair.png",
    "catapult": "assets/catapult.png",
}
CONSUMABLES_MAX_USES = {"light_repair": -1, "hard_repair": -1, "catapult": 3}


def cube_to_cartesian(coords: CoordsTuple) -> tuple[float, float]:
    """
    Translates hex coordinates from cube to cartesian
    :param coords: cube coordinates tuple
    :return: cartesian coordinates tuple
    """
    return coords[0] * 1.5, (coords[1] - coords[2]) * 0.866025


class SingleHPBar(Widget):
    """
    Hp widget
    """


class HPBar(Widget):
    """
    Hp bar widget
    """

    max_hp = NumericProperty(0)
    hp = NumericProperty(0)
    offset = NumericProperty(0)
    layout = BoxLayout()

    def on_max_hp(self, _instance, value):
        """
        Callback for creating hp widgets in hp bar
        :param _instance: Event dispatcher, not used
        :param value: new max_hp value
        :return:
        """
        self.layout.clear_widgets()
        for _ in range(value):
            self.layout.add_widget(SingleHPBar())

    def on_hp(self, _instance, value):
        """
        Callback for changing displayed hp widgets in hp bar

        :param _instance: Event dispatcher, not used
        :param value: new hp value
        :return:
        """
        i = self.max_hp
        for bar in self.layout.children:
            bar.opacity = 1 if i <= value else 0
            i -= 1


class Entity(Widget):
    """
    Widget for independently positioned entity
    """

    x_coord = NumericProperty(0)
    y_coord = NumericProperty(0)
    coords = ReferenceListProperty(x_coord, y_coord)
    color = ListProperty([0, 0, 0])


class Vehicle(Entity):
    """
    Vehicle widget
    """

    file: str
    hp_bar = ObjectProperty(0)


class Hex(Entity):
    """
    Hex widget
    """

    side = NumericProperty(0)


class SpecialHex(Entity):
    """
    Special hex widget
    """

    file: str
    uses = NumericProperty(0)
    type = ""

    def on_uses(self, _instance, value):
        """
        Callback for updating consumable
        :param _instance:
        :param value:
        :return:
        """
        max_uses = CONSUMABLES_MAX_USES[self.type]
        if max_uses == -1:
            return

        if value >= max_uses:
            self.color = COLORS["black"]
            self.opacity = 0.2
        else:
            self.color = COLORS["white"]
            self.opacity = 1


def create_hexes(map_data: dict):
    """
    Hex widgets generator
    :param map_data: Map dict
    :return:
    """
    for cube_x in range(-map_data["size"], map_data["size"] + 1):
        for cube_y in range(
            max(-map_data["size"], -map_data["size"] - cube_x),
            min(map_data["size"] + 1, map_data["size"] - cube_x + 1),
        ):
            cube_coords_tuple = (cube_x, cube_y, -cube_x - cube_y)
            new_hex = Hex()

            new_hex.coords = cube_to_cartesian(cube_coords_tuple)

            color = COLORS["grey"]
            cube_coords_dict = tuple_to_dict(cube_coords_tuple)
            if cube_coords_dict in map_data["content"]["base"]:
                color = COLORS["white"]
            if cube_coords_dict in map_data["content"]["obstacle"]:
                color = COLORS["black"]
            new_hex.color = color

            yield new_hex


def create_special_hex(cube_coords: CoordsDict, hex_type: str):
    """
    Creates special hex widget
    :param cube_coords: Cube coordinates of hex in dict
    :param hex_type: Type of hex
    :return:
    """
    new_hex = SpecialHex()
    new_hex.file = SPECIAL_HEXES_TO_SPRITES[hex_type]
    new_hex.coords = cube_to_cartesian(dict_to_tuple(cube_coords))
    new_hex.type = hex_type
    return new_hex


class WoTStrategyRoot(Widget):
    """
    Root widget for app
    """

    vehicles: dict[int, Vehicle] = {}
    consumables: dict[tuple[int, int, int], SpecialHex] = {}
    not_used_colors = [COLORS["red"], COLORS["green"], COLORS["blue"]]
    ids_to_colors: dict[int, tuple[int, int, int]] = {}
    scatter = Scatter()

    def add_vehicle(self, vehicle_id, vehicle_data):
        """
        Creates vehicle widget
        :param vehicle_id:
        :param vehicle_data: Vehicle dict
        :return:
        """
        if vehicle_data["player_id"] not in self.ids_to_colors:
            self.ids_to_colors[vehicle_data["player_id"]] = self.not_used_colors[0]
            self.not_used_colors.remove(self.not_used_colors[0])

        vehicle = Vehicle()
        # TODO: get max hp from local files, not server response
        vehicle.hp_bar.max_hp = vehicle_data["health"]
        vehicle.hp_bar.hp = vehicle_data["health"]
        vehicle.color = self.ids_to_colors[vehicle_data["player_id"]]
        vehicle.file = VEHICLE_TYPES_TO_SPRITES[vehicle_data["vehicle_type"]]

        self.vehicles[vehicle_id] = vehicle
        self.scatter.add_widget(vehicle)

    def create_map(self, map_data: dict):
        """
        Creates hex widgets

        :param map_data: Map dict
        :return:
        """
        for new_hex in create_hexes(map_data):
            self.scatter.add_widget(new_hex)

        for light_repair_cube_coords in map_data["content"]["light_repair"]:
            self.scatter.add_widget(
                create_special_hex(light_repair_cube_coords, "light_repair")
            )
        for hard_repair_cube_coords in map_data["content"]["hard_repair"]:
            self.scatter.add_widget(
                create_special_hex(hard_repair_cube_coords, "hard_repair")
            )
        for catapult_cube_coords in map_data["content"]["catapult"]:
            self.scatter.add_widget(
                create_special_hex(catapult_cube_coords, "catapult")
            )

    def size_setter(self, _instance, width, height):
        """
        Callback for setting position of the scatter widget depending on the size of the window
        :param _instance: Event dispatcher
        :param width: Window width
        :param height: Window height
        :return:
        """
        self.scatter.pos = (width / 2, height / 2)

    def update(self, game_state: dict):
        """
        Updates gui
        :param game_state: Game state dict
        :return:
        """
        self.update_vehicles(game_state["vehicles"])
        self.update_special_hexes(game_state)

    def update_vehicles(self, vehicles_data: dict):
        """
        Updates vehicle widgets

        :param vehicles_data: List of vehicle dicts
        :return:
        """
        for id_string, vehicle_data in vehicles_data.items():
            vehicle_id = int(id_string)
            if vehicle_id not in self.vehicles:
                self.add_vehicle(vehicle_id, vehicle_data)
            vehicle = self.vehicles[vehicle_id]

            pos_x, pos_y = cube_to_cartesian(dict_to_tuple(vehicle_data["position"]))
            vehicle.x_coord = pos_x
            vehicle.y_coord = pos_y

            vehicle.hp_bar.hp = vehicle_data["health"]

    def update_special_hexes(self, game_state: dict):
        """
        Updates special hexes
        :param game_state: Game state dict
        :return:
        """
        for consumable in self.consumables.values():
            consumable.uses = 0
        for hex_cube_coords in game_state["catapult_usage"]:
            hex_cube_coords_tuple = dict_to_tuple(hex_cube_coords)
            self.consumables[hex_cube_coords_tuple].uses += 1


class WoTStrategyApp(App):
    """
    To run game with gui: WotStrategyApp(...).run()
    """

    def __init__(self, map_data, bot, game_session):
        """

        :param map_data: Map dict from server
        :param bot: Bot that will be used to choose actions
        :param game_session:
        """
        super().__init__()
        self.map_data = map_data
        self.bot = bot
        self.game_session = game_session

    def build(self):
        root = WoTStrategyRoot()
        Window.bind(on_resize=root.size_setter)
        root.scatter.x = Window.width / 2
        root.scatter.y = Window.height / 2

        root.create_map(self.map_data)

        Clock.schedule_once(self.tick, 0)
        return root

    def tick(self, _dt):
        """
        Performs single tick with gui

        :param _dt: Time since last frame, not used
        :return:
        """
        new_state = game_tick(self.bot, self.game_session)
        if new_state is None:
            return
        self.root.update(new_state)
        Clock.schedule_once(self.tick, 0)
