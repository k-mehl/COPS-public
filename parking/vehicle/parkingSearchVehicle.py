from __future__ import print_function
import random

import traci

from parking.common.enum import Enum

# Activity states of a vehicle
state = Enum(
    ["CRUISING",
     "SEARCHING",
     "FOUND_PARKING_SPACE",
     "MANEUVERING_TO_PARK",
     "PARKED"]
)


class ParkingSearchVehicle(object):
    def __init__(self,
                 p_name,
                 p_environment,
                 p_config,
                 p_run,
                 p_timestep=-1001,
                 p_destinationNodeID="",
                 p_cooperativeRoute=None,
                 p_individualRoute=None, is_coop=None):
        """ Initializer for searching vehicles, initializes vehicle attributes

        The init is called while the run() method in a simulation step. No vehicles of this type exits before this step.

        Args:
            p_name: Corresponds to the vehicle ID obtained from the route XML
                file
            p_environment: Reference to environment
            p_config: Reference to configuration
            p_run: Current run number
            p_timestep: For memorizing the simulation time when a vehicle is
                created
            p_destinationNodeID (str): Destination ID
            p_cooperativeRoute (list): predefined route
            p_individualRoute (list): predefined route
            is_coop: boolean if the car is a coop car in new realization
        """

        self._environment = p_environment
        self._config = p_config

        self._name = p_name
        self._speed = 0.0

        # information about relevant simulation times; -1001 seems to be used
        # for unset values in SUMO examples
        self._timeCreated = p_timestep
        self._timeBeginSearch = -1001
        self._timeBeginManeuvering = -1001
        self._timeParked = -1001

        # information about the lane position of a found parking space
        self._assignedParkingPosition = -1001
        self._assignedParkingEdge = ""

        # information about the edge of an eventually found parking space in
        # the opposite direction
        self._seenOppositeParkingSpace = ""

        # neighbors who share parking information with the vehicles
        self._connected_neighbors = []

        # information about the current position of a vehicle
        self._currentEdgeID = ""
        self._currentLaneID = ""
        self._currentLaneLength = -1001.0
        self._currentLanePosition = -1001.0
        self._currentOppositeEdgeID = ""
        self._position = None  # vehicle position in (x, y)

        self._oppositeEdgeID = None

        # information needed to separate search phases
        self._search_phase = 1
        self._lastEdgeBeforePhase3 = ""

        # information for result analysis. None used as defensive programming.
        self._search_time = None
        self._search_distance = None
        self._walk_time = None
        self._walk_distance = None

        self._destinationNodeID = p_destinationNodeID
        self._cooperative_route = p_cooperativeRoute
        self._individual_route = p_individualRoute

        self._is_coop = is_coop

        # information about the vehicle
        l_vcfg = {}
        _run_cfg = self._config.getRunCfg(str(p_run))
        if _run_cfg is not None and _run_cfg.get("vehicles") is not None:
            # reads the runcofiguration from config.runs.json.gz
            l_vcfg = _run_cfg["vehicles"].get(self._name)

        # TODO: move cooperation logic decision out of the vehicles it should
        # be assigned from outside controler
        _sim_cfg = self._config.getCfg("simulation")
        # if not (l_vcfg or lenght(l_vcfg) == 0) ->
        if not l_vcfg or len(l_vcfg) == 0:  # no vehicle cfg exists

            # old initial vehicle settings (by using mixed traffic argument)
            if self._config.getMixedTrafficCfg("ratio") == -1.0 and self._is_coop is None:
                self._driverCooperatesPhase2 = random.random() \
                                               <= _sim_cfg["coopratioPhase2"]
                self._driverCooperatesPhase3 = random.random() \
                                               <= _sim_cfg["coopratioPhase3"]
            else:
                # new initial vehicle config
                if self._is_coop is True:
                    if self._config.getMixedTrafficCfg("coopPhase2"):
                        self._driverCooperatesPhase2 = True
                    else:
                        self._driverCooperatesPhase2 = False

                    if self._config.getMixedTrafficCfg("coopPhase3"):
                        self._driverCooperatesPhase3 = True
                    else:
                        self._driverCooperatesPhase3 = False
                else:
                    self._driverCooperatesPhase2 = False
                    self._driverCooperatesPhase3 = False

            # information about vehicle _activity status, initially vehicle
            # cruises without searching ("phase 1")
            self._activity = state.CRUISING
            # allow for differentiation between searching and non-searching
            # vehicles
            self._isSearchingVehicle = "veh" in self._name

            # update vehicle in run cfg
            l_initialvcfg = {
                "name": self._name,
                "isSearchingVehicle": self._isSearchingVehicle,
                "activity": self._activity,
                "coopPhase2": self._driverCooperatesPhase2,
                "coopPhase3": self._driverCooperatesPhase3,
                "is_coop": self._is_coop
            }
            self._config.updateRunCfgVehicle(p_run, l_initialvcfg)

        else:
            # check whether cooperation was enforced via -c flag from cmd line.
            # If so, throw a dice regarding cooperation
            if _sim_cfg.get("forcecooperationphasetwo") is None:
                self._driverCooperatesPhase2 = l_vcfg["coopPhase2"]
            else:
                self._driverCooperatesPhase2 = random.random() <= _sim_cfg["forcecooperationphasetwo"]

            if _sim_cfg.get("forcecooperationphasethree") is None:
                self._driverCooperatesPhase3 = l_vcfg.get("coopPhase3")
            else:
                self._driverCooperatesPhase3 = random.random() <= _sim_cfg["forcecooperationphasethree"]

            self._activity = l_vcfg.get("activity")
            self._isSearchingVehicle = l_vcfg.get("isSearchingVehicle")

            self._is_coop = l_vcfg.get("is_coop")

        # set the route
        # this can be done better, but i used the existing implementation
        self._current_route = []
        self._currentRouteIndex = -1
        self._activeRoute = []
        self._traversedRoute = []

        if self._is_coop is not None:  # my realization
            # This is for phase2
            if self._is_coop is True and self._config.getMixedTrafficCfg("coopPhase2") is True:
                # only set cooperative route if coop phase 2 is wished
                traci.vehicle.setRoute(self._name, self._cooperative_route)
                self._destinationEdgeID = self._cooperative_route[-1]
            else:
                traci.vehicle.setRoute(self._name, self._individual_route)
                self._destinationEdgeID = self._individual_route[-1]

            # this is for phase 3
            if self._is_coop is True and self._config.getMixedTrafficCfg("coopPhase3") is True:
                # set the weights done like old version:
                self._driverCooperatesPhase3 = True  # True
            else:
                self._driverCooperatesPhase3 = False  # False

        elif self._driverCooperatesPhase2:
            traci.vehicle.setRoute(self._name, self._cooperative_route)  # changes the vehicle route to given edges list
            self._destinationEdgeID = self._cooperative_route[-1]
        else:
            traci.vehicle.setRoute(self._name, self._individual_route)
            self._destinationEdgeID = self._individual_route[-1]

    def __eq__(self, p_other):
        """ Check for equivalence by name attribute """
        return self._name == p_other._name

    def update(self, p_timestep=-1001):
        """ Update vehicle state in the Python representation

        Args:
            p_parkingSpaces: Information about (currently all) available
                parking spaces
            p_oppositeEdgeID: Contains a dictionary for identification of the
                current opposite direction edge
            p_timestep: Information about the current simulation time
        """
        if self._activity == state.PARKED:
            return True

        # Returns the speed in m/s of the named vehicle within the last step.
        self._speed = traci.vehicle.getSpeed(self._name)
        # Returns the id of the edge the named vehicle was at within the last step.
        self._currentEdgeID = traci.vehicle.getRoadID(self._name)
        self._timestep = p_timestep  # =simulation step
        # Returns the id of the lane the named vehicle was at within the last step.
        self._currentLaneID = traci.vehicle.getLaneID(self._name)
        # Returns the position of the named vehicle within the last step [m,m].
        self._position = traci.vehicle.getPosition(self._name)

        # return if vehicle is currently being teleported or SUMO did other
        # esoteric things resulting in no # information regarding current
        # position in network

        if self._currentLaneID is None or self._currentLaneID == "":
            print("/!\ no information regarding {}'s position, skipping update()".format(self._name))
            return

        self._currentLaneLength = traci.lane.getLength(self._currentLaneID)
        self._currentLanePosition = traci.vehicle.getLanePosition(self._name)

        # get the opposite edge if exists (catches wrong index error, if none exists and sets to default)
        try:
            self._oppositeEdgeID = self._environment._oppositeEdgeID[self._currentEdgeID]
        except KeyError:
            self._oppositeEdgeID = ""

        self._current_route = traci.vehicle.getRoute(self._name)
        self._currentRouteIndex = traci.vehicle.getRouteIndex(self._name)

        # create a copy of the _current_route for further modification
        # and divide current route into remaining segments ('active') and
        # traversed segments
        self._activeRoute = self._current_route[:]  # deep copy.
        self._traversedRoute = []
        # TODO: sumo returns -1 if vehicle has not departed solve this in a
        # better way without this check i.e. check at the beginning of update
        # if vehicle departed or not.
        if self._currentRouteIndex > 0:
            # traversed Route is the part of the route till current edge
            # active route is missing part of route from the current edge
            self._traversedRoute = self._activeRoute[:self._currentRouteIndex]  # list from 0 till index -1
            self._activeRoute = self._activeRoute[self._currentRouteIndex:]  # from index till end

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
            self._search_phase = 2
            self._activity = state.SEARCHING
            _max = self._config.getCfg("vehicle")["maxspeed"]["phase2"]
            traci.vehicle.setMaxSpeed(self._name, _max)
            if self._is_coop:
                traci.vehicle.setColor(self._name, (255, 255, 255, 0))  # white car if coop
            else:
                traci.vehicle.setColor(self._name, (255, 255, 0, 0))  # yellow car

        # if the vehicle has reached the last edge before phase 3 should start,
        # change to phase 3 as soon as the edge ID changes again
        if self._lastEdgeBeforePhase3 and not self._search_phase == 3:
            if not self._currentEdgeID == self._lastEdgeBeforePhase3:
                self._search_phase = 3

        # search phase 2 (and later also 3)
        if self._activity == state.SEARCHING:
            self._search()

        # if the vehicle has stopped besides found parking space, basically
        # block the road for a while
        if (self._activity == state.FOUND_PARKING_SPACE and self._speed == 0.0
            and (abs(self._currentLanePosition - self._assignedParkingPosition) < 0.1)):
            self._activity = state.MANEUVERING_TO_PARK
            # memorize the time when maneuvering begins
            self._timeBeginManeuvering = self._timestep
            # set the vehicle color to red in the SUMO GUI
            traci.vehicle.setColor(self._name, (255, 0, 0, 0))

        # twelve seconds after beginning to maneuver into a parking space,
        # 'jump' off the road and release queueing traffic
        if (self._activity == state.MANEUVERING_TO_PARK and
                (self._timestep > (self._timeBeginManeuvering +
                                       self._config.getCfg("vehicle")["parking"]["duration"]))):
            return self._park()
        return False

    def _search(self):
        # if parking space is found ahead on current edge, change vehicle
        # status accordingly
        if ((self._timestep >= self._timeBeginSearch)  # a step has been made
            and self._currentEdgeID in self._environment._roadNetwork["edges"]
            and self.lookoutForParkingSpace(
                self._environment._roadNetwork["edges"][self._currentEdgeID]["parkingSpaces"])):
            # found a free parking space - change state
            self._activity = state.FOUND_PARKING_SPACE
            # let the vehicle stop besides the parking space
            self._assignedParkingEdge = self._currentEdgeID
            traci.vehicle.setStop(self._name, self._currentEdgeID,
                                  self._assignedParkingPosition,
                                  0, 2 ** 31 - 1, 0)
            # set the vehicle color to orange to indicate braking in the GUI
            traci.vehicle.setColor(self._name, (255, 165, 0, 0))

        # if still searching and an opposite edge exists, look there as well
        if (self._activity == state.SEARCHING and
                    self._seenOppositeParkingSpace == "" and
                    self._currentEdgeID in self._environment._oppositeEdgeID):
            self._seenOppositeParkingSpace = \
                self.lookoutForOppositeParkingSpace(self._environment._roadNetwork["edges"][
                                                        self._environment._roadNetwork["edges"][self._currentEdgeID][
                                                            "oppositeEdgeID"]]["parkingSpaces"], self._oppositeEdgeID)

    def _park(self):
        # for the change between 'stopped' and 'parked' in SUMO, first the
        # issued stop command has to be deleted by 'resume'
        # Resumes the vehicle from the current stop (throws an error if the vehicle is not stopped).
        traci.vehicle.resume(self._name)

        # since an exception is thrown when vehicle position is at  xx.000000000000004 set the former assigned
        # position to actual position. check if the actual edge is the assigned edge
        if self._is_wrong_stop_position():
            # the vehicle is in a wrong position to stop cause of unexact traci/ sumo positioning:
            # set the assigned position to actual traci position:
            self._assignedParkingPosition = traci.vehicle.getLanePosition(self._name)

        # now, we can directly stop the vehicle again, this time as 'parked'
        # (last parameter 1 instead of 0)
        traci.vehicle.setStop(self._name, self._currentEdgeID,
                              self._assignedParkingPosition, 0, 2 ** 31 - 1, 1)  # flag = 1
        traci.vehicle.setColor(self._name, (0, 0, 0, 0))  # black vehicle

        # memorize time
        self._timeParked = self._timestep

        # print statistics of the successfully parked vehicle
        if self._config.getCfg("simulation").get("verbose"):
            pars = {"veh": self._name,
                    "time": self._timeParked - self._timeBeginSearch,
                    "distance": traci.vehicle.getDistance(self._name),
                    "p2_coop": self._driverCooperatesPhase2,
                    "p3_coop": self._driverCooperatesPhase3,
                    "is_coop": self._is_coop,
                    "current_phase": self._search_phase}
            print("{veh:<5} parked after {time:>4}s and {distance:>5.0f}m "
                  "phase2Coop={p2_coop}, phase3Coop={p3_coop}, is_coop={is_coop}. "
                  "Current search phase: {current_phase}".format(**pars))

        self._activity = state.PARKED

        # calculation of the vehicle times
        #  when the random destination is an entry edge
        if "entry" in self._destinationEdgeID:
            l_distanceRoad = traci.simulation.getDistanceRoad(
                self._destinationEdgeID, self._environment._roadNetwork[
                    "edges"][self._destinationEdgeID]["length"],
                self._currentEdgeID, self._currentLanePosition, True)
        else:
            l_distanceRoad = traci.simulation.getDistanceRoad(
                self._currentEdgeID, self._currentLanePosition,
                self._destinationEdgeID, self._environment._roadNetwork[
                    "edges"][self._destinationEdgeID]["length"], True)

        l_walkingDistance = l_distanceRoad
        l_walkingTime = l_distanceRoad / 1.111  # assume 4 km/h walking speed

        self._search_time = (self._timeParked - self._timeBeginSearch)
        self._walk_time = l_walkingTime
        self._search_distance = traci.vehicle.getDistance(self._name)
        self._walk_distance = l_walkingDistance

    def lookoutForParkingSpace(self, p_parkingSpaces):
        """ Lookout for available parking spaces by checking vehicle position
        information against the 'map' of existing parking spaces.

        Args:
            p_parkingSpaces: Information about all parkingSpaces in the network
        """
        _dist_min = self._config.getCfg("vehicle")["parking"]["distance"]["min"]
        _dist_max = self._config.getCfg("vehicle")["parking"]["distance"]["max"]
        if self._speed <= 0.0:
            return False
        # for all existing parking spaces, check if there is one available
        # within the assumed viewing distance of the driver
        for ps in sorted(p_parkingSpaces, key=lambda x: x.position):
            # only consider parking spaces on the current edge
            if ps.available and ps.edgeID == self._currentEdgeID:
                # only consider parking spaces which are
                # - far away enough so that the vehicle can safely stop
                # (otherwise SUMO will create an error)
                # - within a distance of max. 30 meters in front of the
                # vehicle
                _poss_diff = ps.position - self._currentLanePosition
                if _dist_min < _poss_diff < _dist_max:
                    # found parking space is assigned to this vehicle
                    # (from now, parking space is no longer available to
                    # other vehicles)
                    ps.assignToVehicle(self._name)
                    self._assignedParkingPosition = ps.position
                    self._assignedParkingEdge = ps.edgeID  # here i set the edge for exception check
                    return True
        return False

    def lookoutForOppositeParkingSpace(self, p_parkingSpaces,
                                       p_oppositeEdgeID):
        """ Lookout for available parking spaces in the opposite direction

        Args:
            p_parkingSpaces: Information about all parkingSpaces in the network
            p_oppositeEdgeID: Name of the edge in opposite direction
        """
        # TODO: maybe better check for vehicle status
        if self._speed <= 0:
            return ""

        _dist_max = self._config.getCfg("vehicle")["parking"]["distance"]["max"]
        _lane_diff = self._currentLaneLength - self._currentLanePosition  # length to drive at the current lane
        _sight_diff = self._currentLaneLength - (self._currentLanePosition + _dist_max)

        # for all existing parking spaces, check if there is one available
        # within the assumed viewing distance of the driver
        for ps in p_parkingSpaces:
            # only consider parking spaces on the current opposite edge
            if ps.available and (ps.edgeID == p_oppositeEdgeID):
                if (_sight_diff < ps.position < _lane_diff):
                    # if an opposite parking space has been found,
                    # insert a loop to the active route (just once back
                    # and forth)
                    self._activeRoute.insert(0, p_oppositeEdgeID)  # set egde id to route at first position
                    self._activeRoute.insert(0,
                                             self._currentEdgeID)  # set current edge to first position -> traci needs the current position to route
                    # communicate the modified active route to the
                    # vehicle via TraCI
                    traci.vehicle.setRoute(self._name, self._activeRoute)  # update route to traci
                    return self._oppositeEdgeID
        return ""

    def last_edge(self):
        """ Check if vehicle is on the last segment of planned route """
        # is the route only one edge long?
        if self._currentRouteIndex == len(self._current_route) - 1:
            #  is vehicle  not in search phase 3 and not the last edge before3 is set
            if not self._search_phase == 3 and not self._lastEdgeBeforePhase3:
                # set the last edge before changing to phase 3
                self._lastEdgeBeforePhase3 = self._currentEdgeID
            return True
        return False

    def append_route(self, p_edgeID):
        """ Add edge to vehicle active route and to vehicle representation in
        SUMO """
        self._activeRoute.append(p_edgeID)
        traci.vehicle.setRoute(self._name, self._activeRoute)

    def is_parked(self):
        """ Check if vehicle has successfully parked """
        if self._activity == state.PARKED:
            return True
        return False

    def _is_wrong_stop_position(self):
        '''
        Checks if the traci position is the same as the assigned.
        also checks if the current edge id is the same like the assigned edge
        and checks if it's the same position [m] to except a tolerance of 0.99 m
        :return: True, if position is not correct but within the tolerance
        '''
        if (abs(traci.vehicle.getLanePosition(self._name) - self._assignedParkingPosition) != 0.00) \
                and (self._assignedParkingEdge == traci.vehicle.getRoadID(self._name)) \
                and (int(traci.vehicle.getLanePosition(self._name)) == int(self._assignedParkingPosition)):
            return True
        else:
            return False

    @property
    def cooperative_route(self):
        """ Cooperative routing information (list) """
        return self._cooperative_route

    @cooperative_route.setter
    def cooperative_route(self, value):
        self._cooperative_route = value
        if self._driverCooperatesPhase2:
            traci.vehicle.setRoute(self._name, self._cooperative_route)

    @property
    def individual_route(self):
        """ Individual routing information (list) """
        return self._individual_route

    @individual_route.setter
    def individual_route(self, value):
        self._individual_route = value
        if not self._driverCooperatesPhase2:
            traci.vehicle.setRoute(self._name, self._individual_route)

    @property
    def destination_edge_id(self):
        return self._destinationEdgeID

    @destination_edge_id.setter
    def destination_edge_id(self, destinationEdgeID):
        self._destinationEdgeID = destinationEdgeID

    @property
    def traversed_route(self):
        return self._traversedRoute

    @traversed_route.setter
    def traversed_route(self, traversedRoute):
        self._traversedRoute = traversedRoute

    @property
    def active_route(self):
        return self._activeRoute

    @active_route.setter
    def active_route(self, activeRoute):
        self._activeRoute = activeRoute

    @property
    def search_phase(self):
        return self._search_phase

    @property
    def name(self):
        return self._name

    @property
    def is_coop(self):
        return self._is_coop

    def __getattr__(self, name):
        class_name = "_" + name
        if hasattr(self, class_name):
            return getattr(self, class_name)
        else:
            raise AttributeError("{} has no attribute {}".format(
                type(self).__name__, name))

    def __repr__(self):
        return self._name

        # this is called uncoditionally hence be careful with this
        # def __setattr__(self, name, val):
        #     class_name = "_" + name
        #     if hasattr(self, class_name):
        #         setattr(self, class_name, val)
        #     else:
        #         raise AttributeError("You can not set {}".format(name))

