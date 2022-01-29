import socket
import struct
import json
from typing import Optional
from enum import IntEnum


# TODO: add logging
# TODO: add docstrings


class ActionCode(IntEnum):
    LOGIN = 1
    LOGOUT = 2
    MAP = 3
    GAME_STATE = 4
    GAME_ACTIONS = 5
    TURN = 6
    CHAT = 100
    MOVE = 101
    SHOOT = 102


class ResponseCode(IntEnum):
    OK = 0
    BAD_COMMAND = 1
    ACCESS_DENIED = 2
    INAPPROPRIATE_GAME_STATE = 3
    TIMEOUT = 4
    INTERNAL_SERVER_ERROR = 500


class ResponseException(Exception):
    pass


class Session:
    def __init__(self, host: str, port: int):
        self.server_details = (host, port)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(11)
        self.client_socket.connect(self.server_details)

    def __del__(self):
        self.client_socket.close()

    def _generate_message(self, code: int, data: Optional[dict] = None):
        if data is None:
            return struct.pack("<ii", code, 0)

        data_length = len(str(data))
        return struct.pack(
            f"<ii{data_length}s", code, data_length, json.dumps(data).encode("utf-8")
        )

    def get(self, action: (ActionCode, int), data: Optional[dict] = None) -> dict:
        """

        :param action:
        :param data:
        :return:
        """
        if isinstance(action, ActionCode):
            action = action.value

        message = self._generate_message(action, data)
        self.client_socket.sendall(message)

        response_code = int.from_bytes(self.client_socket.recv(4), "little")
        received_data_len = int.from_bytes(self.client_socket.recv(4), "little")
        received_data = (
            {}
            if received_data_len == 0
            else json.loads(self.client_socket.recv(received_data_len))
        )

        if response_code != ResponseCode.OK:
            raise ResponseException(
                f'Error message: {received_data["error_message"]}\n'
                f"Response code: {response_code}\n"
                f"Payload: {received_data}"
            )

        return received_data


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    HOST = os.getenv("HOST")
    PORT = int(os.getenv("PORT"))

    s = Session(HOST, PORT)
    login_response = s.get(ActionCode.LOGIN, {"name": "Boris"})
    map_response = s.get(ActionCode.MAP)
    game_state_response = s.get(ActionCode.GAME_STATE)
    game_actions_response = s.get(ActionCode.GAME_ACTIONS)
    logout_response = s.get(ActionCode.LOGOUT)
    print(login_response)
    print(map_response)
    print(game_state_response)
    print(game_actions_response)
    print(logout_response)
