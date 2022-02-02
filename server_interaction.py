import json
import socket
import struct
from enum import IntEnum
from typing import Optional

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

    def get(self, action: (ActionCode, int), data: Optional[dict] = None) -> dict:
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
            )

        return received_data
