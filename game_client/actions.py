"""
Contains class for describing game action.

"""
from game_client.server_interaction import ActionCode
from game_client.vehicles import Vehicle
from utility.coordinates import Coords
from utility.custom_typings import CoordsDictTyping


class Action:
    """
    Class containing information and methods for game action.
    """

    def __init__(
        self,
        action_code: ActionCode,
        actor: Vehicle,
        target: Coords,
        affected_vehicles=None,
    ):
        if affected_vehicles is None:
            affected_vehicles = []

        self.action_code: ActionCode = action_code
        self.actor: Vehicle = actor
        self.target: Coords = target
        self.affected_vehicles = affected_vehicles

    @property
    def server_format(self) -> tuple[ActionCode, int, CoordsDictTyping]:
        """
        Returns action in server format: ActionCode + actor id + target hex.
        """
        return self.action_code, self.actor.vehicle_id, self.target.server_format