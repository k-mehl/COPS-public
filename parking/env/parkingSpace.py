#!usr/bin/env python3
from __future__ import print_function


class ParkingSpace(object):
    def __init__(self, name, edgeID, position, available=False):
        """ Constructor for parking spaces, initializes parking space
        attributes

        Args:
            name: Parking space indentifier.
            edgeID: Specifies the edge on which the parking space is located.
            position: Specifies the position of the parking space on the edge
                in meters.
        """
        self.name = name
        # parking space is not available by default
        self.available = available
        self.edgeID = edgeID
        self.position = position
        # parking space is not assigned to any vehicle by default
        self.assignedToVehicleID = ""

    def __eq__(self, other):
        """ Check for equivalence by name attribute """
        return self.name == other.name

    def assignToVehicle(self, vehID):
        """ Assign a parking space to a specific vehicle

        Args:
            vehID: Identifier of the vehicle which has found the parking space
        """
        # ensure that the parking space is no longer available to the other
        # vehicles
        self.available = False
        self.assignedToVehicleID = vehID

    def unassign(self):
        """ Unassign a parking space from a specific vehicle (mainly for future
        variants with dynamic occupancy)

        Returns:
            The ID of the vehicle which has vacated this parking space.
        """
        self.available = True
        vehID = self.assignedToVehicleID
        self.assignedToVehicleID = ""
        return vehID


if __name__ == "__main__":
    print("Nothing to do.")
# else:
#     print("ParkingSpace class imported.")
