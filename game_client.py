from bot import Bot
from server_interaction import ActionCode, Session

HOST = "wgforge-srv.wargaming.net"
PORT = 443

TYPES_TO_CLASSES = {
    "at_spg": None,  # TODO: AT SPG class
    "heavy_tank": None,  # TODO: Heavy Tank class
    "light_tank": None,  # TODO: Light Tank class
    "medium_tank": None,  # TODO: Medium Tank class
    "spg": None,  # TODO: SPG class
}


class WrongPayloadFormatException(Exception):
    pass


class GameState:
    """
    Keeps info about game state.
    """

    def __init__(self, player_id: int, data: dict):
        self.__player_id = player_id
        self.current_player_id = data["current_player_idx"]
        self.finished = data["finished"]
        self.winner = data["winner"]
        self.enemy_tanks: dict[str, Tank] = {}
        self.allied_tanks: dict[str, Tank] = {}

        for vehicle_id, data in data["vehicles"].items():
            if data["player_id"] == self.__player_id:
                self.allied_tanks[vehicle_id] = self.__get_vehicle(data)
            else:
                self.enemy_tanks[vehicle_id] = self.__get_vehicle(data)

    def update(self, data: dict) -> None:
        self.current_player_id = data["current_player_idx"]
        self.finished = data["finished"]
        self.winner = data["winner"]

        for vehicle_id, data in data["vehicles"].items():
            if data["player_id"] == self.__player_id:
                self.allied_tanks[vehicle_id].update(data)
            else:
                self.enemy_tanks[vehicle_id].update(data)

    def __get_vehicle(self, data):
        return TYPES_TO_CLASSES[data["vehicle_type"]](
            player_id=data["id"],
            health=data["health"],
            spawn_position=data["spawn_position"],
            position=data["position"],
            capture_points=data["capture_points "],
        )


class GameSession:
    """
    Handles interaction with server throughout one game session.

    """

    def __init__(self, **login_info):
        """

        Login info is expected to have:
        :param name: player's name

        Also following values are not required:
        :param password: player's password used to verify the connection,
            if player with the same name tries to connect with another
            password login will be rejected.
        :param game: game's name (use it to connect to existing game
            or to create a new one with defined name).
        :param num_turns: number of game turns to be played. If not provided,
            the default (45 as for now) amount will be used.
        :param num_players: number of players in the game. Default: 1.
        :param is_observer: defines if player connect to server just for
            watching. Default: false.
        """
        self.__validate_login_info(login_info)

        self.server = Session(HOST, PORT)
        login_response = self.server.get(ActionCode.LOGIN, login_info)

        self.player_id = login_response["idx"]
        self.player_name = login_response["name"]
        self.map = self.server.get(ActionCode.MAP)
        self.__game_state = None

    def __validate_login_info(self, login_info: dict):
        valid_fields = (
            "name",
            "password",
            "game",
            "num_turns",
            "num_players",
            "is_observer",
        )

        if "name" not in login_info:
            raise WrongPayloadFormatException("Field 'name' is required.")

        for var in login_info.keys():
            if var not in valid_fields:
                raise WrongPayloadFormatException(
                    f"Field {var}: {login_info[var]} is not valid login field."
                )

    def get_game_state(self) -> GameState:
        game_state_raw = self.server.get(ActionCode.GAME_STATE)

        if self.__game_state is None:
            self.__game_state = GameState(self.player_id, game_state_raw)
        else:
            self.__game_state.update(game_state_raw)

        return self.__game_state

    def game_actions(self) -> dict:
        return self.server.get(ActionCode.GAME_ACTIONS)

    def turn(self) -> dict:
        return self.server.get(ActionCode.TURN)

    def chat(self, message: str) -> dict:
        return self.server.get(ActionCode.CHAT, {"message": message})

    def action(self, action: (ActionCode, int), vehicle_id: int, target: dict) -> dict:
        # TODO: Add validation for vehicle_id and target
        payload = {
            "vehicle_id": vehicle_id,
            "target": target,
        }
        return self.server.get(action, payload)

    def logout(self) -> dict:
        return self.server.get(ActionCode.LOGOUT)


def game_loop(bot: Bot, game: GameSession):
    """
    Plays the given game with the given bot.

    :param bot:
    :param game:
    :return:
    """
    is_finished = False
    while not is_finished:
        game_state = game.get_game_state()

        is_finished = game_state["finished"]

        if is_finished:
            print("You won" if game_state["winner"] == game.player_id else "You lost")
            break

        if game_state["current_player_idx"] == game.player_id:
            print(
                f'Round: {game_state["current_turn"]}, ' f"player: {game.player_name}"
            )
            for action in bot.get_actions(game_state):
                game.action(*action)
                print(
                    f"  Action: "
                    f'{"shoot" if action[0] == ActionCode.SHOOT else "move"}'
                    f" Actor: {action[1]} Target: {action[2]}"
                )

        game.turn()
