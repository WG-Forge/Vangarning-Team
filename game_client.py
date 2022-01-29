import os
from dotenv import load_dotenv

from server_interaction import Session, ActionCode
from bot import SimpleBot, Bot

# TODO: add docs for GameSession.__init__

load_dotenv()
HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))


class WrongPayloadFormatException(Exception):
    pass


class GameSession:
    """
    Handles interaction with server throughout one game session.

    """

    def __init__(self, **login_info):
        """

        Login info is expected to have:
        :param name: player's name

        Also following values are not required:
        :param password: - player's password used to verify the connection,
            if player with the same name tries to connect with another
            password - login will be rejected.
        :param game: - game's name (use it to connect to existing game
            or to create a new one with defined name).
        :param num_turns: - number of game turns to be played. If not provided,
            the default (45 as for now) amount will be used.
        :param num_players: - number of players in the game. Default: 1.
        :param is_observer: - defines if player connect to server just for
            watching. Default: false.
        """
        self.__validate_login_info(login_info)

        self.server = Session(HOST, PORT)
        login_response = self.server.get(ActionCode.LOGIN, login_info)

        self.player_id = login_response["idx"]
        self.player_name = login_response["name"]
        self.map = self.server.get(ActionCode.MAP)

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

    def get_game_state(self):
        return self.server.get(ActionCode.GAME_STATE)

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


def game_loop(bot, *games):
    is_finished = False
    while not is_finished:
        for game in games:
            game_state = game.get_game_state()

            if game_state["finished"] == "true":
                is_finished = True
                break

            if game_state["current_player_idx"] == game.player_id:
                print(
                    f'Round: {game_state["current_turn"]}, '
                    f"player: {game.player_name}"
                )
                actions = bot.get_actions(game_state)
                for action in actions:

                    print(
                        f"  Action: "
                        f'{"shoot" if action[0] == ActionCode.SHOOT else "move"}'
                        f" Actor: {action[1]} Target: {action[2]}"
                    )  # Badly written f-string just for fast check

                    game.action(*action)

            game.turn()


if __name__ == "__main__":
    game_name = "VT_test"

    game_session = GameSession(
        name="Bot_test_1", game=game_name, num_turns=20, num_players=2
    )
    game_session_1 = GameSession(
        name="Bot_test_2",
        game=game_name,
    )

    simple_bot = SimpleBot(game_session.map)
    game_loop(simple_bot, game_session, game_session_1)
