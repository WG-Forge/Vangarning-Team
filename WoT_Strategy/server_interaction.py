import json
import socket
import struct
from enum import IntEnum
from typing import Optional, Union

HOST = "wgforge-srv.wargaming.net"
PORT = 443


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


class WrongPayloadFormatException(Exception):
    pass


class Session:
    """
    Provides server interface.

    Not a singleton as multiple clients from
    one PC needed for testing purposes.

    Client-server message format:
    {action (4 bytes)} +
    {data length (4 bytes)} +
    {bytes of UTF-8 string with data in JSON format}
    """

    def __init__(self, host: str, port: int):
        self.server_details = (host, port)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(11)  # As one game round is 10s + 1s for latencies
        self.client_socket.connect(self.server_details)

    def __del__(self):
        self.client_socket.close()

    def __recvall(self, length):
        result = b""
        while len(result) != length:
            result += self.client_socket.recv(length - len(result))

        return result

    def __generate_message(self, code: int, data: Optional[dict] = None):
        if data is None:
            return struct.pack("<ii", code, 0)

        data_length = len(str(data))
        return struct.pack(
            f"<ii{data_length}s", code, data_length, json.dumps(data).encode("utf-8")
        )

    def get(self, action: Union[ActionCode, int], data: Optional[dict] = None) -> dict:
        """
        Returns response from the server.

        Converts data to client-server message format, sends the result to
        the server and returns 'data' part of the result if response
        code was OK, otherwise raises ResponseException.

        :param action: action code, one from the list of codes in server documentation
        :param data: data to send with the request
        :return: 'data' part of response from server
        """

        message = self.__generate_message(action, data)
        self.client_socket.sendall(message)

        response_code, received_data_len = struct.unpack("<ii", self.__recvall(8))
        received_data = (
            {}
            if received_data_len == 0
            else json.loads(self.__recvall(received_data_len))
        )

        if response_code != ResponseCode.OK:
            raise ResponseException(
                f"Response code: {response_code}\n"
                f'Error message: {received_data["error_message"]}\n'
                f"Data that caused error: {action} {data}"
            )

        return received_data


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

    def game_state(self) -> dict:
        return self.server.get(ActionCode.GAME_STATE)

    def game_actions(self) -> dict:
        return self.server.get(ActionCode.GAME_ACTIONS)

    def turn(self) -> dict:
        return self.server.get(ActionCode.TURN)

    def chat(self, message: str) -> dict:
        return self.server.get(ActionCode.CHAT, {"message": message})

    def action(
        self, action: Union[ActionCode, int], vehicle_id: int, target: dict
    ) -> dict:
        payload = {
            "vehicle_id": vehicle_id,
            "target": target,
        }
        return self.server.get(action, payload)

    def logout(self) -> dict:
        return self.server.get(ActionCode.LOGOUT)
