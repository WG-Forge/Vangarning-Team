import os
from dotenv import load_dotenv

from server_interaction import Session, ActionCode

# TODO: add docs for GameSession.__init__

load_dotenv()
HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))


class WrongPayloadFormatException(Exception):
    pass


def validate_login_info(login_info: dict):
    valid_fields = (
        "name",
        "password",
        "game",
        "num_turns",
        "num_players",
        "is_observer",
    )

    for var in login_info.keys():
        if var not in valid_fields:
            raise WrongPayloadFormatException(
                f"Field {var}: {login_info[var]} is not valid login field."
            )


class GameSession:
    """
    Handles interaction with server throughout one game session.

    """

    def __init__(self, **login_info,):
        validate_login_info(login_info)

        self.server = Session(HOST, PORT)
        login_response = self.server.get(ActionCode.LOGIN, login_info)

        self.current_player_id = login_response["idx"]
        self.map = self.server.get(ActionCode.MAP)
        self.game_state = self.server.get(ActionCode.GAME_STATE)

    def update_game_state(self):
        self.game_state = self.server.get(ActionCode.GAME_STATE)

    # @property
    # def game_state(self):
    #     """
    #     Updates game state from server for every call.
    #     """
    #     return self.server.get(ActionCode.GAME_STATE)

    def game_actions(self) -> dict:
        return self.server.get(ActionCode.GAME_ACTIONS)

    def turn(self) -> dict:
        return self.server.get(ActionCode.TURN)

    def chat(self, message: str) -> dict:
        return self.server.get(ActionCode.CHAT, {"message": message})

    def move(self, vehicle_id: int, target: dict) -> dict:
        # TODO: Add validation for vehicle_id and target
        payload = {
            "vehicle_id": vehicle_id,
            "target": target,
        }
        return self.server.get(ActionCode.MOVE, payload)

    def shoot(self, vehicle_id: int, target: dict) -> dict:
        # TODO: Add validation for vehicle_id and target
        payload = {
            "vehicle_id": vehicle_id,
            "target": target,
        }
        return self.server.get(ActionCode.SHOOT, payload)

    def logout(self) -> dict:
        return self.server.get(ActionCode.LOGOUT)


def game_loop(game: GameSession):
    while True:
        game.update_game_state()
        game_state = game.game_state
        if game_state["current_player_idx"] == game.current_player_id:
            pass  # Send game_state to bot

        game.turn()


if __name__ == "__main__":
    game_session = GameSession()
    game_loop(game_session)
