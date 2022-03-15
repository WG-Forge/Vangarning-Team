"""
Contains class for describing game action.

"""
from dataclasses import dataclass, field

from game_client.server_interaction import ActionCode
from game_client.vehicles import Vehicle
from utility.coordinates import Coords
from utility.custom_typings import CoordsDictTyping


@dataclass(frozen=True)
class Action:
    """
    Class containing information and methods for game action.

    """

    action_code: ActionCode
    actor: Vehicle
    target: Coords
    affected_vehicles: list[Vehicle] = field(default_factory=list)

    @property
    def server_format(self) -> tuple[ActionCode, int, CoordsDictTyping]:
        """
        Returns action in server format: ActionCode + actor id + target hex.
        """
        return self.action_code, self.actor.vehicle_id, self.target.server_format
