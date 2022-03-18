"""
Handles graphic interface.

"""
# pylint: disable=too-few-public-methods, import-error
# pylint: disable=attribute-defined-outside-init
# Pylint doesn't get along with kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import (
    ListProperty,
    NumericProperty,
    ObjectProperty,
    ReferenceListProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.effectwidget import EffectWidget
from kivy.uix.label import Label
from kivy.uix.scatter import Scatter
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget

from game_client.vehicles import VEHICLE_CLASSES
from utility.coordinates import Coords
from utility.custom_typings import CoordsDictTyping, CoordsTupleTyping

COLORS = {
    "black": (0, 0, 0),
    "grey": (0.5, 0.5, 0.5),
    "white": (1, 1, 1),
    "red": (1, 0, 0),
    "green": (0, 1, 0),
    "blue": (0, 0, 1),
}
VEHICLE_TYPES_TO_SPRITES = {
    "at_spg": "gui/assets/AT_SPG.png",
    "heavy_tank": "gui/assets/HT.png",
    "light_tank": "gui/assets/LT.png",
    "medium_tank": "gui/assets/MT.png",
    "spg": "gui/assets/SPG.png",
}
SPECIAL_HEXES_TO_SPRITES = {
    "light_repair": "gui/assets/light_repair.png",
    "hard_repair": "gui/assets/hard_repair.png",
    "catapult": "gui/assets/catapult.png",
}
CONSUMABLES_MAX_USES = {"light_repair": -1, "hard_repair": -1, "catapult": 3}
HEX_SIZE = NumericProperty(25)


def dict_to_tuple(coord_dict):
    """
    Transforms coordinates from dict representation to tuple representation.
    :param coord_dict: Coordinates dict
    :return: Coordinates tuple
    """
    return coord_dict["x"], coord_dict["y"], coord_dict["z"]


def cube_to_cartesian(coords: CoordsTupleTyping) -> tuple[float, float]:
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

    hex_size = NumericProperty(25)
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
        # pylint: disable=C0104
        # Meant not as name placeholder but literal bar
        for bar in self.layout.children:
            bar.opacity = 1 if i <= value else 0
            i -= 1


class Entity(Widget):
    """
    Widget for independently positioned entity
    """

    hex_size = NumericProperty(25)
    x_coord = NumericProperty(0)
    y_coord = NumericProperty(0)
    coords = ReferenceListProperty(x_coord, y_coord)
    color = ListProperty([0, 0, 0])

    def on_hex_size(self, _instance, value):
        """
        Callback which updates child widgets hex_size property

        :param _instance: Event dispatcher
        :param value: new hex_size value
        :return:
        """
        for child in self.children:
            child.hex_size = value


class Vehicle(Entity):
    """
    Vehicle widget
    """

    hp_bar = ObjectProperty(0)
    file: str


class Hex(Entity):
    """
    Hex widget
    """

    side = NumericProperty(0)


class SpecialHex(Entity):
    """
    Special hex widget
    """

    uses = NumericProperty(0)
    type = ""
    file: str

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

    size_without_center = map_data["size"] - 1
    for cube_x in range(-size_without_center, size_without_center + 1):
        for cube_y in range(
            max(-size_without_center, -size_without_center - cube_x),
            min(size_without_center + 1, size_without_center - cube_x + 1),
        ):
            cube_coords_tuple = (cube_x, cube_y, -cube_x - cube_y)
            new_hex = Hex()

            new_hex.coords = cube_to_cartesian(cube_coords_tuple)

            color = COLORS["grey"]
            cube_coords_dict = Coords(cube_coords_tuple).server_format
            if cube_coords_dict in map_data["content"]["base"]:
                color = COLORS["white"]
            if cube_coords_dict in map_data["content"]["obstacle"]:
                color = COLORS["black"]
            new_hex.color = color

            yield new_hex


def create_special_hex(cube_coords: CoordsDictTyping, hex_type: str):
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


class MyScatter(Scatter):
    """
    Custom scatter class width hex_size property attribute
    """

    hex_size = NumericProperty(25)

    def on_hex_size(self, _instance, value):
        """
        Callback which updates child widgets hex_size property

        :param _instance: Event dispatcher
        :param value: new hex_size value
        :return:
        """
        for child in self.children:
            child.hex_size = value


class PlayerLayout(BoxLayout):
    player_id = NumericProperty(0)
    player_name = StringProperty()
    capture_points = NumericProperty(0)
    kill_points = NumericProperty(0)
    color = ListProperty([0, 0, 0])


class MyLabel(Label):
    color = ListProperty([0, 0, 0, 1])
    back_color = ListProperty([1, 1, 1, 1])


class GameScreenRoot(EffectWidget):
    """
    Root widget for app
    """

    vehicles: dict[int, Vehicle] = {}
    consumables: dict[tuple[int, int, int], SpecialHex] = {}
    not_used_colors = [COLORS["red"], COLORS["green"], COLORS["blue"]]
    ids_to_colors: dict[int, tuple[int, int, int]] = {}
    scatter = MyScatter()
    players_layouts = {}
    info_layout = BoxLayout()
    turn_label = MyLabel()
    map_size = 23
    hex_size = NumericProperty(25)

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
        vehicle.hex_size = self.hex_size
        vehicle.hp_bar.max_hp = VEHICLE_CLASSES[vehicle_data["vehicle_type"]](
            vehicle_id, vehicle_data
        ).max_hp
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
        self.map_size = map_data["size"] * 2 + 1
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
            catapult = create_special_hex(catapult_cube_coords, "catapult")
            self.consumables[dict_to_tuple(catapult_cube_coords)] = catapult
            self.scatter.add_widget(catapult)

    def size_setter(self, _instance, width, height):
        """
        Callback for setting position of the scatter widget depending on the size of the window
        :param _instance: Event dispatcher
        :param width: Window width
        :param height: Window height
        :return:
        """
        self.scatter.pos = (width / 2, height / 2)
        self.hex_size = min(
            (width - 10) / (self.map_size * 1.5 + 0.5),
            (height - 10) / (self.map_size * 2 * 0.866025),
        )

    def on_hex_size(self, _instance, value):
        """
        Callback which updates child widgets hex_size property

        :param _instance: Event dispatcher
        :param value: new hex_size value
        :return:
        """
        # self.scatter.hex_size = value
        for child in self.children:
            child.hex_size = value

    def update(self, game_state: dict):
        """
        Updates gui
        :param game_state: Game state dict
        :return:
        """
        self.update_vehicles(game_state["vehicles"])
        self.update_special_hexes(game_state)
        self.update_player_info(game_state)
        self.turn_label.text = str(game_state["current_turn"])

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

            vehicle.coords = cube_to_cartesian(dict_to_tuple(vehicle_data["position"]))

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

    def add_player_info(self, player_info: dict):
        idx = player_info["idx"]

        layout = PlayerLayout()
        self.info_layout.add_widget(layout)

        self.players_layouts[idx] = layout
        layout.player_id = idx
        layout.color = tuple(self.ids_to_colors[idx]) + (1,)
        layout.player_name = player_info["name"]

    def update_player_info(self, game_state: dict):
        for id_string, win_points in game_state["win_points"].items():
            player_idx = int(id_string)
            if player_idx not in self.players_layouts:
                self.add_player_info(
                    next(
                        player
                        for player in game_state["players"]
                        if player["idx"] == player_idx
                    )
                )
            self.players_layouts[player_idx].capture_points = win_points["capture"]
            self.players_layouts[player_idx].kill_points = win_points["kill"]


class GameScreen(Screen):
    game_screen_root = GameScreenRoot()


class GameOverScreenRoot(Widget):
    message_label = Label()

    def set_message(self, game_state):
        if game_state["winner"] is None:
            self.message_label.text = "DRAW"
        elif isinstance(game_state["winner"], int):
            self.message_label.text = (
                next(
                    player["name"]
                    for player in game_state["players"]
                    if player["idx"] == game_state["winner"]
                )
                + " HAS WON"
            )
        else:
            draw_player_1 = next(
                player["name"]
                for player in game_state["players"]
                if player["idx"] == game_state["winner"][0]
            )
            draw_player_2 = next(
                player["name"]
                for player in game_state["players"]
                if player["idx"] == game_state["winner"][1]
            )
            lose_player = next(
                player["name"]
                for player in game_state["players"]
                if player["is_observer"] is False
            )
            self.message_label.text = (
                "DRAW BETWEEN "
                + draw_player_1
                + " AND "
                + draw_player_2
                + ". PLAYER "
                + lose_player
                + " LOST"
            )


class GameOverScreen(Screen):
    game_over_screen_root = GameOverScreenRoot()


class WoTStrategyApp(App):
    """
    To run game with gui: WotStrategyApp(...).run()
    """

    kv_directory = "gui/assets"

    def __init__(self, map_data, game_state_property):
        """

        :param map_data: Map dict from server
        :param game_state_property: Property to update gui on set game state
        """
        super().__init__()
        self.map_data = map_data
        self.game_state_property = game_state_property

    def update_screen(self, game_state):
        if game_state["finished"]:
            sm: ScreenManager = self.root
            game_over_screen: GameOverScreen = sm.get_screen(name="game over")
            game_over_screen.game_over_screen_root.set_message(game_state)
            sm.current = "game over"

    def build(self):
        """
        Creates root widget of the app.

        """
        sm = ScreenManager()

        game_screen = GameScreen(name="game")
        game_screen.game_screen_root.create_map(self.map_data)

        Window.bind(on_resize=game_screen.game_screen_root.size_setter)
        Window.dispatch("on_resize", Window.width, Window.height)

        self.game_state_property.bind(
            lambda game_state: Clock.schedule_once(
                lambda dt: game_screen.game_screen_root.update(game_state), 0
            )
        )

        sm.add_widget(game_screen)

        game_over_screen = GameOverScreen(name="game over")
        self.game_state_property.bind(
            lambda game_state: Clock.schedule_once(
                lambda dt: self.update_screen(game_state), 0
            )
        )

        sm.add_widget(game_over_screen)
        return sm
