#!usr/bin/env python
from __future__ import print_function

class ParkingSpace(object):

    ## Constructor for parking spaces, initializes parking space attributes
    #  @param Name
    #  @param edgeID Specifies the edge on which the parking space is located
    #  @param position Specifies the position of the parking space on the edge
    #                  [meters]
    def __init__(self, name, edgeID, position):
        self.name = name
        # parking space is not available by default
        self.available = False
        self.edgeID = edgeID
        self.position = position
        # parking space is not assigned to any vehicle by default
        self.assignedToVehicleID = ""

    ## Check for equivalence by name attribute
    def __eq__(self, other):
        return self.name == other.name

    ## Assign a parking space to a specific vehicle
    #  @param vehID Identifier of the vehicle which has found the parking space
    def assignToVehicle(self, vehID):
        # ensure that the parking space is no longer available to other 
        # vehicles
        self.available = False
        self.assignedToVehicleID = vehID

    ## Unassign a parking space from a specific vehicle 
    #  (mainly for future variants with dynamic occupancy)
    #  @return Return the ID of the vehicle which has 
    #          vacated this parking space
    def unassign(self):
        self.available = True
        vehID = self.assignedToVehicleID
        self.assignedToVehicleID = ""
        return vehID

                
if __name__ == "__main__":
    print("Nothing to do.")
#else:
    #print("ParkingSpace class imported.")
