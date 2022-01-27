import os
from dotenv import load_dotenv

from server_interaction import Session, ActionCode

load_dotenv()
HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))


class GameSession:
    def __init__(self, **login_info):
        self.server = Session(HOST, PORT)
        self.server.get(ActionCode.LOGIN, login_info)   # Possible errors: no login_info validation

        self.map = self.server.get(ActionCode.MAP)
        self.game_state = self.server.get(ActionCode.GAME_STATE)

    def logout(self):
        self.server.get(ActionCode.LOGOUT)

    def update_game_state(self):
        self.game_state = self.server.get(ActionCode.GAME_STATE)

    def game_actions(self):
        self.server.get(ActionCode.GAME_ACTIONS)

    def turn(self):
        self.server.get(ActionCode.TURN)

    def chat(self, message: str):
        self.server.get(ActionCode.CHAT, {"message": message})

    def move(self, vehicle_id: int, target: dict):
        payload = {
            "vehicle_id": vehicle_id,
            "target": target,
        }
        self.server.get(ActionCode.MOVE, payload)

    def shoot(self, vehicle_id: int, target: dict):
        payload = {
            "vehicle_id": vehicle_id,
            "target": target,
        }
        self.server.get(ActionCode.SHOOT, payload)


if __name__ == '__main__':
    pass
