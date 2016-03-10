#!usr/bin/env python
from __future__ import print_function
import traci
import random

## Integer values to indicate the current activity status of a vehicle
VEHICLE_CRUISING = 0
VEHICLE_SEARCHING = 1
VEHICLE_FOUND_PARKING_SPACE = 2
VEHICLE_MANEUVERING_TO_PARK = 3
VEHICLE_PARKED = 4

class ParkingSearchVehicle(object):

    ## Constructor for searching vehicles, initializes vehicle attributes
    #  @param name Corresponds to the vehicle ID obtained from the route XML
    #  file
    #  @param coopRatio The fraction of cooperative drivers
    #  @param timestep For memorizing the simulation time when a vehicle is
    #  created
    def __init__(self, name, coopRatio=0.0, timestep=-1001):
        self.name = name
        self.speed = 0.0
        # allow for differentiation between searching and non-searching vehicles
        if "veh" in name:
            self.isSearchingVehicle = True
        else:
            self.isSearchingVehicle = False
        # information about vehicle activity status, initially vehicle cruises
        # without searching ("phase 1")
        self.activity = VEHICLE_CRUISING
        # set individual preference for cooperation
        self.driverCooperates = False
        if random.random()<=coopRatio:
        	self.driverCooperates = True
        # information about relevant simulation times; -1001 seems to be used
        # for unset values in SUMO examples
        self.timeCreated = timestep
        self.timeBeginSearch = -1001
        self.timeBeginManeuvering = -1001
        self.timeParked = -1001
        # information about the lane position of a found parking space
        self.assignedParkingPosition = -1001
        # information about the edge of an eventually found parking space in the
        # opposite direction
        self.seenOppositeParkingSpace = ""
        # information about the current position of a vehicle
        self.currentEdgeID = ""
        self.currentLaneID = ""
        self.currentLaneLength = -1001.0
        self.currentLanePosition = -1001.0
        self.currentOppositeEdgeID = ""
        # information about the vehicle route
        self.currentRoute = []
        self.currentRouteIndex = -1
        self.activeRoute = []
        self.traversedRoute = []
        self.cooperativeRoute = []
        self.individualRoute = []
        

    ## Check for equivalence by name attribute
    def __eq__(self, other):
        return self.name == other.name


    ## Update vehicle state in the Python representation
    #  @param parkingSpaces Information about (currently all) available parking
    #                       spaces
    #  @param oppositeEdgeID Contains a dictionary for identification of the
    #                        current opposite direction edge
    #  @param timestep Information about the current simulation time
    def update(self, parkingSpaces, oppositeEdgeID, timestep=-1001):
        # get all relevant information about the vehicle from SUMO via TraCI
        # calls:
        # get vehicle speed
        self.speed = traci.vehicle.getSpeed(self.name)
        # get ID of the edge the vehicle currently drives on
        self.currentEdgeID = traci.vehicle.getRoadID(self.name)
        # as long as vehicle is not parked:
        # get information about the current lane (ID, length and vehicle
        # position)
        if not self.activity==4:
            self.currentLaneID = traci.vehicle.getLaneID(self.name)
            self.currentLaneLength = traci.lane.getLength(self.currentLaneID)
            self.currentLanePosition = traci.vehicle.getLanePosition(self.name)
        # if an opposite direction lane exists, get ID of the opposite edge
        if self.currentEdgeID in oppositeEdgeID:
            self.oppositeEdgeID = oppositeEdgeID[self.currentEdgeID]
        else:
            self.oppositeEdgeID = ""
        # get current vehicle routing from SUMO
        self.currentRoute = traci.vehicle.getRoute(self.name)
        # get the sequence index of the current element within the whole route
        self.currentRouteIndex = traci.vehicle.getRouteIndex(self.name)
        # create a copy of the currentRoute for further modification
        # and divide current route into remaining segments ('active') and
        # traversed segments
        self.activeRoute = self.currentRoute
        self.traversedRoute = []
        if self.currentRouteIndex > 0:
            for i in range (0, self.currentRouteIndex):
                self.traversedRoute.append(self.activeRoute[0])
                self.activeRoute.remove(self.activeRoute[0])


        # if the vehicle has turned due to a seen opposite parking space,
        # (i.e. as soon as the current edge equals the previoulsy opposite edge)
        # remove information about the seen parking space on the previously
        # opposite edge
        # (because it is no longer opposite) 
        if self.seenOppositeParkingSpace == self.currentEdgeID:
            self.seenOppositeParkingSpace = ""
        
        # if the vehicle is cruising and has entered the search district, change
        # to search phase 2
        if (self.isSearchingVehicle and self.activity == VEHICLE_CRUISING and
                self.currentRouteIndex >= 1):
            self.timeBeginSearch = timestep
            self.activity = VEHICLE_SEARCHING
            # reduce speed for searching
            traci.vehicle.setMaxSpeed(self.name, 8.333)
            # set the vehicle color to yellow in the SUMO GUI
            traci.vehicle.setColor(self.name,(255,255,0,0))

        # search phase 2 (and later also 3)
        if self.activity == VEHICLE_SEARCHING: 
            # if parking space is found ahead on current edge, change vehicle
            # status accordingly
            if ((timestep >= self.timeBeginSearch+1) and
                    self.lookoutForParkingSpace(parkingSpaces)):
            	self.activity = VEHICLE_FOUND_PARKING_SPACE
                # let the vehicle stop besides the parking space
                traci.vehicle.setStop(self.name, self.currentEdgeID,
                        self.assignedParkingPosition, 0, 2**31 - 1, 0)
                # set the vehicle color to orange to indicate braking in the
                # SUMO GUI
            	traci.vehicle.setColor(self.name,(255,165,0,0))
            # if still searching and an opposite edge exists, look there as well
            if (self.activity == VEHICLE_SEARCHING and
                    self.seenOppositeParkingSpace=="" and self.currentEdgeID in
                    oppositeEdgeID):
                self.seenOppositeParkingSpace = \
                self.lookoutForOppositeParkingSpace(parkingSpaces,
                                                    oppositeEdgeID) 

        # if the vehicle has stopped besides found parking space, basically
        # block the road for a while
        if (self.activity == VEHICLE_FOUND_PARKING_SPACE and 
                self.speed == 0.0 and 
                (abs(self.currentLanePosition-self.assignedParkingPosition)<0.1)
                ):
            self.activity = VEHICLE_MANEUVERING_TO_PARK
            # memorize the time when maneuvering begins
            self.timeBeginManeuvering=timestep
            # set the vehicle color to red in the SUMO GUI
            traci.vehicle.setColor(self.name,(255,0,0,0))

        # twelve seconds after beginning to maneuver into a parking space,
        # 'jump' off the road and release queueing traffic
        if (self.activity == VEHICLE_MANEUVERING_TO_PARK and (timestep >
            (self.timeBeginManeuvering + 12))):
            self.activity = VEHICLE_PARKED
            # for the change between 'stopped' and 'parked' in SUMO, first the
            # issued stop command has to be deleted by 'resume'
            traci.vehicle.resume(self.name)
            # now, we can directly stop the vehicle again, this time as 'parked'
            # (last parameter 1 instead of 0)
            traci.vehicle.setStop(self.name, self.currentEdgeID,
                    self.assignedParkingPosition, 0, 2**31 - 1, 1)
            # set the vehicle color to black in the SUMO GUI
            traci.vehicle.setColor(self.name,(0,0,0,0))
            # memorize time
            self.timeParked = timestep
            # print statistics of the successfully parked vehicle
            # (at the moment output to console)
            print(self.name, "parked after", (self.timeParked -
                self.timeBeginSearch), "seconds,",
                traci.vehicle.getDistance(self.name), "meters.")
            

    ## Lookout for available parking spaces by checking vehicle position
    #information against the 'map' of existing parking spaces
    #  @param parkingSpaces Information about all parkingSpaces in the network
    def lookoutForParkingSpace(self, parkingSpaces):
        if self.speed > 0.0:
            # for all existing parking spaces, check if there is one available
            # within the assumed viewing distance of the driver
            for parkingSpace in parkingSpaces:
                # only consider parking spaces on the current edge
                if (parkingSpace.available and
                        (parkingSpace.edgeID==self.currentEdgeID)):
                    # only consider parking spaces which are
                    # - far away enough so that the vehicle can safely stop
                    # (otherwise SUMO will create an error)
                    # - within a distance of max. 30 meters in front of the
                    # vehicle
                    if ((parkingSpace.position-self.currentLanePosition >12.0)
                            and (parkingSpace.position-self.currentLanePosition
                                <30.0)):
                        # found parking space is assigned to this vehicle
                        # (from now, parking space is no longer available to
                        # other vehicles)
                        parkingSpace.assignToVehicle(self.name)
                        self.assignedParkingPosition = parkingSpace.position
                        return True
        return False


    ## Lookout for available parking spaces in the opposite direction
    #  @param parkingSpaces Information about all parkingSpaces in the network
    #  @param oppositeEdgeID Name of the edge in opposite direction
    def lookoutForOppositeParkingSpace(self, parkingSpaces, oppositeEdgeID):
        if self.speed > 0.0:
            # for all existing parking spaces, check if there is one available
            # within the assumed viewing distance of the driver
            for parkingSpace in parkingSpaces:
                # only consider parking spaces on the current opposite edge
                if (parkingSpace.available and \
                    (parkingSpace.edgeID==oppositeEdgeID[self.currentEdgeID])):
                    if (parkingSpace.position <
                            self.currentLaneLength-self.currentLanePosition):
                        if (parkingSpace.position > \
                        self.currentLaneLength-(self.currentLanePosition+30.0)):
                            # if an opposite parking space has been found,
                            # insert a loop to the active route (just once back
                            # and forth)
                            self.activeRoute.insert(0, 
                                    oppositeEdgeID[self.currentEdgeID])
                            self.activeRoute.insert(0, self.currentEdgeID)
                            # communicate the modified active route to the
                            # vehicle via TraCI
                            traci.vehicle.setRoute(self.name, self.activeRoute)
                            return self.oppositeEdgeID
        return ""

    ## Retrieve stored cooperative routing information
    def getCooperativeRoute(self):
        return self.cooperativeRoute

    ## Store cooperative routing information
    #  @param coopRoute list with route information (edge IDs)
    #  @param useCoopRouting if true, tell SUMO to set the cooperative routing
    def setCooperativeRoute(self, coopRoute):
        self.cooperativeRoute = coopRoute
        if self.driverCooperates:
            traci.vehicle.setRoute(self.name, self.cooperativeRoute)

	## Retrieve stored individual routing information
    def getIndividualRoute(self):
        return self.individualRoute

    ## Store individual routing information
    #  @param indyRoute list with route information (edge IDs)
    #  @param useCoopRouting if false, tell SUMO to set the individual routing
    def setIndividualRoute(self, indyRoute):
        self.individualRoute = indyRoute
        if not self.driverCooperates:
            traci.vehicle.setRoute(self.name, self.individualRoute)

    ## Query whether vehicle has successfully parked
    def getParkedStatus(self):
        if self.activity == VEHICLE_PARKED:
            return True
        return False
             
if __name__ == "__main__":
    print("Nothing to do.")
#else:
    #print("ParkingSearchVehicle class imported.")
