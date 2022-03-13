"""
Contains Player class.
"""
from typing import Iterator

from game_client.vehicles import TYPE_ORDER, Vehicle
from utility.custom_typings import (AttackMatrixDictTyping, PlayerDictTyping,
                                    WinPointsDictTyping)


class Player:
    """
    Class to describe player instance.

    """

    def __init__(self, data: PlayerDictTyping):
        """
        :param data: piece of GAME_STATE response from the server.
        """
        self.idx: int = data["idx"]
        self.name: str = data["name"]
        self.is_observer: bool = data["is_observer"]
        self.vehicles: list[Vehicle] = []
        self.can_attack_ids: list[int] = []
        self.win_points: WinPointsDictTyping = {
            "capture": 0,
            "kill": 0,
        }

    def add_vehicle(self, vehicle: Vehicle) -> None:
        """
        Adds vehicle to player's vehicles.

        :param vehicle: vehicle class instance
        """
        self.vehicles.append(vehicle)

    def update(
        self, win_points: WinPointsDictTyping, attack_matrix: AttackMatrixDictTyping
    ) -> None:
        """
        Updates info about player.

        :param win_points: win points of the player
        :param attack_matrix: piece of GAME_STATE response from the server
        """
        self.win_points = win_points
        self.__update_can_attack_ids(attack_matrix)

    @property
    def ordered_vehicle_iter(self) -> Iterator[Vehicle]:
        """
        Yields step order sorted vehicles of the player.

        Order is AtSpg, MediumTank, LightTank, HeavyTank, Spg
        """
        for vehicle in sorted(
            self.vehicles, key=lambda v: TYPE_ORDER.index(v.__class__)
        ):
            yield vehicle

    def __update_can_attack_ids(self, attack_matrix: AttackMatrixDictTyping) -> None:
        """
        Updates information about possible targets.


        :param attack_matrix: piece of GAME_STATE response from the server
        """
        result: set[int] = {int(i) for i in attack_matrix.keys()}
        can_attack: set[int] = set()
        cannot_attack: set[int] = {self.idx}
        for player, data in attack_matrix.items():
            if int(player) == self.idx:
                continue
            if self.idx in data:
                can_attack.add(int(player))
            cannot_attack |= set(data)

        # Subtract players who were attacked from all players and then
        # add players who attacked us to the result
        self.can_attack_ids = list(result - cannot_attack | can_attack)
