#!usr/bin/env python
from __future__ import print_function
import traci
import random
from common.enum import Enum

# Activity states of a vehicle
state = Enum(
    ["CRUISING",
     "SEARCHING",
     "FOUND_PARKING_SPACE",
     "MANEUVERING_TO_PARK",
     "PARKED"]
)

class ParkingSearchVehicle(object):

    ## Constructor for searching vehicles, initializes vehicle attributes
    #  @param p_name Corresponds to the vehicle ID obtained from the route XML file
    #  @param p_coopRatio The fraction of cooperative drivers
    #  @param p_timestep For memorizing the simulation time when a vehicle is created
    def __init__(self, p_name, p_environment, p_config, p_timestep=-1001, p_destinationNodeID="", p_cooperativeRoute=[], p_individualRoute=[]):
        self._name = p_name
        self._environment = p_environment
        self._speed = 0.0
        self._config = p_config

        # allow for differentiation between searching and non-searching vehicles
        self._isSearchingVehicle = "veh" in self._name

        # information about vehicle _activity status, initially vehicle cruises
        # without searching ("phase 1")
        self._activity = state.CRUISING

        # set individual preference for cooperation
        self._driverCooperates = random.random() <= self._config.get("simulation").get("cooperation")

        # information about relevant simulation times; -1001 seems to be used
        # for unset values in SUMO examples
        self._timeCreated = p_timestep
        self._timeBeginSearch = -1001
        self._timeBeginManeuvering = -1001
        self._timeParked = -1001
        # information about the lane position of a found parking space
        self._assignedParkingPosition = -1001
        # information about the edge of an eventually found parking space in the
        # opposite direction
        self._seenOppositeParkingSpace = ""
        # information about the current position of a vehicle
        self._currentEdgeID = ""
        self._currentLaneID = ""
        self._currentLaneLength = -1001.0
        self._currentLanePosition = -1001.0
        self._currentOppositeEdgeID = ""
        # information about the vehicle route

        self._destinationNodeID = p_destinationNodeID
        self._currentRoute = []
        self._currentRouteIndex = -1
        self._activeRoute = []
        self._traversedRoute = []
        self._cooperativeRoute = p_cooperativeRoute
        self._individualRoute = p_individualRoute
        if self._driverCooperates:
            traci.vehicle.setRoute(self._name, self._cooperativeRoute)
            self._destinationEdgeID = self._cooperativeRoute[-1]
        else:
            traci.vehicle.setRoute(self._name, self._individualRoute)
            self._destinationEdgeID = self._individualRoute[-1]


    ## Check for equivalence by name attribute
    def __eq__(self, p_other):
        return self._name == p_other._name


    ## Update vehicle state in the Python representation
    #  @param p_parkingSpaces Information about (currently all) available parking
    #                       spaces
    #  @param p_oppositeEdgeID Contains a dictionary for identification of the
    #                        current opposite direction edge
    #  @param p_timestep Information about the current simulation time
    def update(self, p_timestep=-1001):
        # get all relevant information about the vehicle from SUMO via TraCI
        # calls:
        # get vehicle _speed
        self._speed = traci.vehicle.getSpeed(self._name)
        # get ID of the edge the vehicle currently drives on
        self._currentEdgeID = traci.vehicle.getRoadID(self._name)
        self._timestep = p_timestep

        # as long as vehicle is not parked:
        # get information about the current lane (ID, length and vehicle
        # position)
        if not self._activity==state.PARKED:
            self._currentLaneID = traci.vehicle.getLaneID(self._name)
            self._currentLaneLength = traci.lane.getLength(self._currentLaneID)
            self._currentLanePosition = traci.vehicle.getLanePosition(self._name)
        # if an opposite direction lane exists, get ID of the opposite edge
        if self._currentEdgeID in self._environment._oppositeEdgeID:
            self._oppositeEdgeID = self._environment._oppositeEdgeID[self._currentEdgeID]
        else:
            self._oppositeEdgeID = ""
        # get current vehicle routing from SUMO
        self._currentRoute = traci.vehicle.getRoute(self._name)
        # get the sequence index of the current element within the whole route
        self._currentRouteIndex = traci.vehicle.getRouteIndex(self._name)
        # create a copy of the _currentRoute for further modification
        # and divide current route into remaining segments ('active') and
        # traversed segments
        self._activeRoute = self._currentRoute[:]
        self._traversedRoute = []
        if self._currentRouteIndex > 0:
            for i in range (0, self._currentRouteIndex):
                self._traversedRoute.append(self._activeRoute[0])
                self._activeRoute.remove(self._activeRoute[0])


        # if the vehicle has turned due to a seen opposite parking space,
        # (i.e. as soon as the current edge equals the previoulsy opposite edge)
        # remove information about the seen parking space on the previously
        # opposite edge
        # (because it is no longer opposite)
        if self._seenOppositeParkingSpace == self._currentEdgeID:
            self._seenOppositeParkingSpace = ""

        # if the vehicle is cruising and has entered the search district, change
        # to search phase 2
        if (self._isSearchingVehicle and self._activity == state.CRUISING and
                    self._currentRouteIndex >= 1):
            self._timeBeginSearch = self._timestep
            self._activity = state.SEARCHING
            # reduce _speed for searching
            traci.vehicle.setMaxSpeed(self._name, self._config.get("vehicle").get("maxspeed").get("phase2"))
            # set the vehicle color to yellow in the SUMO GUI
            traci.vehicle.setColor(self._name,(255,255,0,0))

        # search phase 2 (and later also 3)
        if self._activity == state.SEARCHING:

            self._search()

        # if the vehicle has stopped besides found parking space, basically
        # block the road for a while
        if (self._activity == state.FOUND_PARKING_SPACE and
                    self._speed == 0.0 and
                (abs(self._currentLanePosition-self._assignedParkingPosition)<0.1)
            ):
            self._activity = state.MANEUVERING_TO_PARK
            # memorize the time when maneuvering begins
            self._timeBeginManeuvering=self._timestep
            # set the vehicle color to red in the SUMO GUI
            traci.vehicle.setColor(self._name,(255,0,0,0))

        # twelve seconds after beginning to maneuver into a parking space,
        # 'jump' off the road and release queueing traffic
        if (self._activity == state.MANEUVERING_TO_PARK and (self._timestep >
                (self._timeBeginManeuvering + self._config.get("vehicle").get("parking").get("duration")))):

            return self._park()

        return(0)


    def _search(self):
        # if parking space is found ahead on current edge, change vehicle
        # status accordingly
        if ((self._timestep >= self._timeBeginSearch) and
                    self._currentEdgeID in self._environment._roadNetwork["edges"] and
                self.lookoutForParkingSpace(self._environment._roadNetwork["edges"][self._currentEdgeID]["parkingSpaces"])):
            self._activity = state.FOUND_PARKING_SPACE
            # let the vehicle stop besides the parking space
            traci.vehicle.setStop(self._name, self._currentEdgeID,
                                  self._assignedParkingPosition, 0, 2 ** 31 - 1, 0)
            # set the vehicle color to orange to indicate braking in the
            # SUMO GUI
            traci.vehicle.setColor(self._name,(255,165,0,0))
        # if still searching and an opposite edge exists, look there as well
        if (self._activity == state.SEARCHING and
                    self._seenOppositeParkingSpace== "" and
                    self._currentEdgeID in self._environment._oppositeEdgeID):
            self._seenOppositeParkingSpace = \
                self.lookoutForOppositeParkingSpace(self._environment._roadNetwork["edges"][self._environment._roadNetwork["edges"][self._currentEdgeID]["oppositeEdgeID"]]["parkingSpaces"], self._oppositeEdgeID)


    def _park(self):
        # for the change between 'stopped' and 'parked' in SUMO, first the
        # issued stop command has to be deleted by 'resume'
        traci.vehicle.resume(self._name)
        # now, we can directly stop the vehicle again, this time as 'parked'
        # (last parameter 1 instead of 0)
        traci.vehicle.setStop(self._name, self._currentEdgeID,
                              self._assignedParkingPosition, 0, 2 ** 31 - 1, 1)
        # set the vehicle color to black in the SUMO GUI
        traci.vehicle.setColor(self._name,(0,0,0,0))
        # memorize time
        self._timeParked = self._timestep
        # print statistics of the successfully parked vehicle
        # (at the moment output to console)
        print(self._name, "parked after", (self._timeParked -
                                           self._timeBeginSearch), "seconds,",
              traci.vehicle.getDistance(self._name), "meters.")

        self._activity = state.PARKED
        l_destCoords = self._environment._net.getNode(self._destinationNodeID).getCoord()
       	l_vehicleCoords = traci.simulation.convert2D(self._currentEdgeID, self._currentLanePosition)
        l_distanceRoad = traci.simulation.getDistanceRoad(self._currentEdgeID, self._currentLanePosition, self._destinationEdgeID, self._environment._roadNetwork["edges"][self._destinationEdgeID]["length"], True)
        l_distanceAir = traci.simulation.getDistanceRoad(self._currentEdgeID, self._currentLanePosition, self._destinationEdgeID, self._environment._roadNetwork["edges"][self._destinationEdgeID]["length"], False)
        if l_distanceRoad > 1000.0:
        	l_walkingDistance = l_distanceAir
        else:
        	l_walkingDistance = l_distanceRoad
        
        return [self._name, (self._timeParked -
                             self._timeBeginSearch), traci.vehicle.getDistance(self._name), l_walkingDistance]


    ## Lookout for available parking spaces by checking vehicle position
    #information against the 'map' of existing parking spaces
    #  @param p_parkingSpaces Information about all parkingSpaces in the network
    def lookoutForParkingSpace(self, p_parkingSpaces):
        if self._speed > 0.0:
            # for all existing parking spaces, check if there is one available
            # within the assumed viewing distance of the driver
            for parkingSpace in p_parkingSpaces:
                # only consider parking spaces on the current edge
                if (parkingSpace.available and
                        (parkingSpace.edgeID==self._currentEdgeID)):
                    # only consider parking spaces which are
                    # - far away enough so that the vehicle can safely stop
                    # (otherwise SUMO will create an error)
                    # - within a distance of max. 30 meters in front of the
                    # vehicle
                    if ((parkingSpace.position-self._currentLanePosition > self._config.get("vehicle").get("parking").get("distance").get("min"))
                        and (parkingSpace.position-self._currentLanePosition
                                 < self._config.get("vehicle").get("parking").get("distance").get("max"))):
                        # found parking space is assigned to this vehicle
                        # (from now, parking space is no longer available to
                        # other vehicles)
                        parkingSpace.assignToVehicle(self._name)
                        self._assignedParkingPosition = parkingSpace.position
                        return True
        return False


    ## Lookout for available parking spaces in the opposite direction
    #  @param p_parkingSpaces Information about all parkingSpaces in the network
    #  @param p_oppositeEdgeID Name of the edge in opposite direction
    def lookoutForOppositeParkingSpace(self, p_parkingSpaces, p_oppositeEdgeID):
        if self._speed > 0.0:
            # for all existing parking spaces, check if there is one available
            # within the assumed viewing distance of the driver
            for parkingSpace in p_parkingSpaces:
                # only consider parking spaces on the current opposite edge
                if (parkingSpace.available and \
                            (parkingSpace.edgeID==p_oppositeEdgeID)):
                    if (parkingSpace.position <
                                self._currentLaneLength-self._currentLanePosition):
                        if (parkingSpace.position > \
                                        self._currentLaneLength-(self._currentLanePosition+self._config.get("vehicle").get("parking").get("distance").get("max"))):
                            # if an opposite parking space has been found,
                            # insert a loop to the active route (just once back
                            # and forth)
                            self._activeRoute.insert(0,
                                                     p_oppositeEdgeID)
                            self._activeRoute.insert(0, self._currentEdgeID)
                            # communicate the modified active route to the
                            # vehicle via TraCI
                            traci.vehicle.setRoute(self._name, self._activeRoute)
                            return self._oppositeEdgeID
        return ""

    ## Retrieve stored cooperative routing information
    def getCooperativeRoute(self):
        return self._cooperativeRoute

    ## Store cooperative routing information
    #  @param coopRoute list with route information (edge IDs)
    #  @param useCoopRouting if true, tell SUMO to set the cooperative routing
    def setCooperativeRoute(self, p_coopRoute):
        self._cooperativeRoute = p_coopRoute
        if self._driverCooperates:
            traci.vehicle.setRoute(self._name, self._cooperativeRoute)


    ## Retrieve stored individual routing information
    def getIndividualRoute(self):
        return self._individualRoute

    ## Store individual routing information
    #  @param p_indyRoute list with route information (edge IDs)
    def setIndividualRoute(self, p_indyRoute):
        self._individualRoute = p_indyRoute
        if not self._driverCooperates:
            traci.vehicle.setRoute(self._name, self._individualRoute)

    ## Query whether vehicle has successfully parked
    def getParkedStatus(self):
        if self._activity == state.PARKED:
            return True
        return False

    def getVehicleID(self):
        return self._name

    def getVehicleRoute(self):
        return self._currentRoute

    def getDestinationEdgeID(self):
        return self._destinationEdgeID

    def setDestinationEdgeID(self, destinationEdgeID):
        self._destinationEdgeID = destinationEdgeID

    def getTraversedRoute(self):
        return self._traversedRoute

    def setTraversedRoute(self, traversedRoute):
        self._traversedRoute = traversedRoute

    def getActiveRoute(self):
        return self._activeRoute

    def setActiveRoute(self, activeRoute):
        self._activeRoute = activeRoute

    def getName(self):
        return self._name

    def setNextRouteSegment(self, p_edgeID):
        self._activeRoute.append(p_edgeID)
        traci.vehicle.setRoute(self._name, self._activeRoute)

    ## Query whether vehicle is on last segment of planned route
    def isOnLastRouteSegment(self):
        if self._currentRouteIndex == len(self._currentRoute)-1:
            return True
        return False

if __name__ == "__main__":
    print("Nothing to do.")
#else:
#print("ParkingSearchVehicle class imported.")
