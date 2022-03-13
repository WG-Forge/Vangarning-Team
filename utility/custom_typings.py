"""
Project-specific typings.

"""

from typing import Optional, TypedDict


class CoordsDictTyping(TypedDict):
    """
    Server format coordinates typing.

    """

    x: int
    y: int
    z: int


CoordsTupleTyping = tuple[int, int, int]


ContentDictTyping = dict[str, list[CoordsDictTyping]]


class MapDictTyping(TypedDict):
    """
    Server format map response typing.

    """

    size: int
    name: str
    spawn_points: list[dict[str, list[CoordsDictTyping]]]
    content: ContentDictTyping


class PlayerDictTyping(TypedDict):
    """
    Server format player typing.

    """

    idx: int
    name: str
    is_observer: bool


class VehicleDictTyping(TypedDict):
    """
    Server format vehicle typing.

    """

    player_id: int
    vehicle_type: str
    health: int
    spawn_position: CoordsDictTyping
    position: CoordsDictTyping
    capture_points: int
    shoot_range_bonus: int


class WinPointsDictTyping(TypedDict):
    """
    Server format win points typing.

    """

    capture: int
    kill: int


AttackMatrixDictTyping = dict[str, list[int]]


class GameStateDictTyping(TypedDict):
    """
    Server format game state response typing.

    """

    num_players: int
    num_turns: int
    current_turn: int
    players: list[PlayerDictTyping]
    observers: list
    current_player_idx: int
    finished: bool
    vehicles: dict[str, VehicleDictTyping]
    attack_matrix: AttackMatrixDictTyping
    winner: Optional[int]
    win_points: dict[str, WinPointsDictTyping]
    catapult_usage: list[CoordsDictTyping]
