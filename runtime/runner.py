#!/usr/bin/env python
from __future__ import print_function

import os
import subprocess
import sys
import random

try:
    xrange
except NameError:
    xrange = range

try:
    import itertools.izip as zip
except ImportError:
    pass

try:
    # we need to import python modules from the $SUMO_HOME/tools directory
    # check: http://sumo.dlr.de/wiki/TraCI/Interfacing_TraCI_from_Python#importing_traci_in_a_script
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
    from sumolib import checkBinary
except KeyError:
    sys.exit(
        """
        Declare environment variable 'SUMO_HOME', for more info refer to:
        http://sumo.dlr.de/wiki/TraCI/Interfacing_TraCI_from_Python
        """)

import traci
import sumolib

from common.cooperativeSearch import *
from vehicle.parkingSearchVehicle import *
from common.vehicleFactory import *
from env.environment import *
from . import phase2


class Runtime(object):
    """ Runtime object """

    def __init__(self, p_config):
        """ Runtime object

        Args:
            p_args (str): Arguments provided by command line via argparse
        """

        self._config = p_config
        self._sim_dir = self._config.getCfg("simulation")

        # run sumo with gui or headless, depending on the --gui flag
        self._sumoBinary = checkBinary('sumo-gui') if not self._sim_dir.get(
            "headless") else checkBinary('sumo')

        self._environment = Environment(self._config)

    def run(self, i_run):
        """ Runs the simulation on both SUMO and Python layers

        Args:
            i_run (int): run number
        """
        # if there is a run configuration loaded use it to populate
        # parkingspaces in environment otherwise initialize new
        if not self._config.getRunCfg(str(i_run)):
            if self._sim_dir.get("verbose"):
                print("* no run cfg found. Initializing random parking spaces.")
            self._environment.initParkingSpaces(i_run)

        elif self._config.isRunCfgOk(i_run):
            self._environment.loadParkingSpaces(i_run)
        else:
            return

        # if --routefile flag is provided, use the file for routing, otherwise
        # generate (and overwrite if exists) route file (reroute.rou.xml) for
        # this simulation run using the given number of parking search vehicles
        if os.path.isfile(
                os.path.join(
                    self._sim_dir.get("resourcedir"),
                    self._sim_dir.get("routefile"))) and self._sim_dir.get(
                        "forceroutefile"):
            self._routefile = self._sim_dir.get("routefile")
        else:
            self._routefile = self._sim_dir.get("routefile")
            generatePsvDemand(
                self._sim_dir.get("vehicles"),
                self._sim_dir.get("resourcedir"), self._routefile)

        # this is the normal way of using traci. sumo is started as a
        # subprocess and then the python script connects and runs
        l_sumoProcess = subprocess.Popen(
            [self._sumoBinary,
             "-n",
             os.path.join(self._sim_dir.get("resourcedir"), "reroute.net.xml"),
             "-r",
             os.path.join(self._sim_dir.get("resourcedir"), self._routefile),
             "--tripinfo-output",
             os.path.join(self._sim_dir.get("resourcedir"), "tripinfo.xml"),
             "--gui-settings-file", os.path.join(
             self._sim_dir.get("resourcedir"), "gui-settings.cfg"),
             "--no-step-log",
             "--remote-port",
             str(self._sim_dir.get("sumoport"))],
            stdout=sys.stdout,
            stderr=sys.stderr)

        # execute the TraCI control loop
        traci.init(self._sim_dir.get("sumoport"))

        # internal clock variable, start with 0
        step = 0

        # create empty list for parking search vehicles
        l_parkingSearchVehicles = []

        # compute phase 2 routing information (individual and cooperative)
        l_individualRoutes, l_cooperativeRoutes = self.computePhase2Routings()

        # create lists for search time and distance results
        searchTimes = []
        walkingTimes = []
        searchDistances = []
        walkingDistances = []
        searchPhases = []

        self.initPOI()
        self.updatePOIColors()

        # do simulation time steps as long as vehicles are present in the
        # network
        while traci.simulation.getMinExpectedNumber() > 0:
            # tell SUMO to do a simulation step
            traci.simulationStep()
            self.updatePOIColors()
            # increase local time counter
            step += 1
            # every 1000 steps: ensure local time still corresponds to SUMO
            # simulation time
            # (just a safety check for now, can possibly be removed later)
            if step != (traci.simulation.getCurrentTime() / 1000):
                print("TIMESTEP ERROR", step, "getCurrentTime",
                      traci.simulation.getCurrentTime())
            # if a new vehicle has departed in SUMO, create the corresponding
            # Python representation and remove the vehicles that have
            # disappeared in SUMO
            dep_list = traci.simulation.getDepartedIDList()
            arr_list = traci.simulation.getArrivedIDList()
            l_departedVehicles = (x for x in dep_list if x not in arr_list)

            # get individual vehicle preferences from run config if present,
            # otherwise generate values
            # TODO: following was unused, why was it there?
            # l_run = str(i_run)

            # TODO: separate l_individualRoutes and l_cooperativeRoutes
            l_parkingSearchVehicles.extend(
                    ParkingSearchVehicle(vehID, self._environment,
                        self._config, i_run, step,
                        self._environment._net.getEdge(l_individualRoutes[vehID][-1]).getToNode().getID(),
                        l_cooperativeRoutes[vehID],
                        l_individualRoutes[vehID])
                    for vehID in l_departedVehicles)

            # if a vehicle has disappeared in SUMO, remove the corresponding Python
            # representation
            # for vehID in traci.simulation.getArrivedIDList():
            #         # for now: output to console that the vehicle disappeared upon
            #         # reaching the destination
            #     print(str(vehID),
            #             "did not find an available parking space during phase 2.")
            #     l_parkingSearchVehicles.remove(ParkingSearchVehicle(vehID))

            # update status of all vehicles
            # TODO: differentiate this update method into e.g.
            #       getVehicleData() ..... all TraCI getSomething commands
            #       computeRouting() ..... non-cooperative routing
            #       computeCoopRouting() . cooperative routing
            #       selectRouting() ...... select whether to cooperate or not
            #       setVehicleData() ..... all TraCI setSomething commands
            for psv in l_parkingSearchVehicles:

                result = psv.update(step)
                # count edge visits of each vehicle
                # TODO: make visit update more efficient
                traversedRoute = psv.getTraversedRoute()
                plannedRoute = psv.getActiveRoute()
                name = psv.getName()
                for edge in self._environment._roadNetwork["edges"]:
                    # traversedRoutePlusCurrentEdge.append(psv.getActiveRoute()[0])
                    oppositeEdgeID = self._environment._roadNetwork["edges"][edge]["oppositeEdgeID"]
                    visitCount = traversedRoute.count(str(edge)) \
                                 + traversedRoute.count(oppositeEdgeID)
                    plannedCount = plannedRoute.count(str(edge)) \
                                 + plannedRoute.count(oppositeEdgeID)
                    self._environment._roadNetwork["edges"][edge]["visitCount"][name] = visitCount
                    self._environment._roadNetwork["edges"][edge]["plannedCount"][name] = plannedCount

                # if result values could be obtained, the vehicle found
                # a parking space in the last time step
                if result:
                    searchTimes.append(result[1])
                    walkingTimes.append(result[2])
                    searchDistances.append(result[3])
                    walkingDistances.append(result[4])
                    searchPhases.append(result[5])
                elif psv.isOnLastRouteSegment():
                    # if the vehicle is on the last route segment,
                    # choose one of the possible next edges to continue
                    lastSegment = psv.getVehicleRoute()[-1]
                    succEdges = self._environment._net.getEdge(lastSegment).getToNode().getOutgoing()

                    # calculate costs for every edge except opposite
                    # direction of current edge
                    succEdgeCost = {}

                    for edge in succEdges:
                        # consider all successor edges, BUT if no opposite edge
                        # exists, don't try to exclude it.
                        if lastSegment in self._environment._oppositeEdgeID:
                            if len(succEdges) == 1:
                                succEdgeCost[str(edge.getID())] = \
                                    self.calculateEdgeCost(psv, edge)
                            elif not str(edge.getID()) == self._environment._oppositeEdgeID[lastSegment]:
                                succEdgeCost[str(edge.getID())] = self.calculateEdgeCost(psv, edge)
                        else:
                            succEdgeCost[str(edge.getID())] = self.calculateEdgeCost(psv, edge)

                    # calculate minima of succEdgeCost
                    minValue = min(succEdgeCost.values())
                    minKeys = [key for key in succEdgeCost if succEdgeCost[key] == minValue]

                    # choose randomly if costs are equal
                    # TODO: if "vehicle" always has "phase3randomprob" then
                    # this is reduntant i.e. there is no None from get method.
                    p3_prob = self._config.getCfg("vehicle").get("phase3randomprob")
                    if p3_prob:
                        phase3RandomProb = p3_prob
                    else:
                        phase3RandomProb = 0.0

                    if random.random() < phase3RandomProb:
                        nextRouteSegment = random.choice(list(succEdgeCost.keys()))
                    else:
                        nextRouteSegment = random.choice(minKeys)

                    psv.setNextRouteSegment(nextRouteSegment)

            # break the while-loop if all remaining SUMO vehicles have
            # successfully parked
            if self.getNumberOfRemainingVehicles(l_parkingSearchVehicles) == 0:
                if self._sim_dir.get("verbose"):
                    print("SUCCESSFULLY PARKED:",
                          self.getNumberOfParkedVehicles(
                              l_parkingSearchVehicles), "OUT OF",
                          self._sim_dir.get("vehicles"))
                break

        # close the TraCI control loop
        traci.close()
        sys.stdout.flush()

        l_sumoProcess.wait()

        return (self.getNumberOfParkedVehicles(l_parkingSearchVehicles),
                searchTimes,
                walkingTimes,
                searchDistances,
                walkingDistances,
                searchPhases)

    def calculateEdgeCost(self, psv, edge):
        """ Calculate cost for an edge for a specific search vehicle

        Args:
            psv: parking search vehicle
            edge: edge

        Returns:
            float: cost of edge
        """
        env_edges = self._environment._roadNetwork["edges"]
        veh_weights = self._config.getCfg("vehicle")["weights"]

        toNodedestinationEdge = env_edges[str(psv.getDestinationEdgeID())]["toNode"]

        # get counts from environment
        selfVisitCount = env_edges[edge.getID()]["visitCount"][psv.getName()]
        externalVisitCount = sum(env_edges[edge.getID()]["visitCount"].values()) - selfVisitCount
        externalPlannedCount = sum(env_edges[edge.getID()]["plannedCount"].values())

        
        def cost_wrap(coop):
            return veh_weights[coop]["distance"] \
                   * env_edges[edge.getID()]["nodeDistanceFromEndNode"][toNodedestinationEdge]\
                   + selfVisitCount * veh_weights[coop]["selfvisit"]\
                   + externalVisitCount * veh_weights[coop]["externalvisit"]\
                   + externalPlannedCount * veh_weights[coop]["externalplanned"]

        if psv._driverCooperatesPhase3:
            return cost_wrap("coop")
        else:
            return cost_wrap("noncoop")

        # if psv._driverCooperatesPhase3:
        #     cost = veh_weights["coop"]["distance"] * \
        #            env_edges[edge.getID()]["nodeDistanceFromEndNode"][toNodedestinationEdge]\
        #            + selfVisitCount * veh_weights["coop"]["selfvisit"]\
        #            + externalVisitCount * veh_weights["coop"]["externalvisit"]\
        #            + externalPlannedCount * veh_weights["coop"]["externalplanned"]
        # else:
        #     cost = veh_weights["noncoop"]["distance"] * \
        #            env_edges[edge.getID()]["nodeDistanceFromEndNode"][toNodedestinationEdge]\
        #            + selfVisitCount * veh_weights["noncoop"]["selfvisit"]\
        #            + externalVisitCount * veh_weights["noncoop"]["externalvisit"]\
        #            + externalPlannedCount * veh_weights["noncoop"]["externalplanned"]
        # return cost

    def convertNodeSequenceToEdgeSequence(self, adjacencyEdgeID, nodeSequence):
        """ Convert a route given as sequence of node indices into the
        corresponding sequence of edge IDs

        Args:
            adjacencyEdgeID (matrix): adjacency matrix containing the edge IDs
            nodeSequence (Iterable): route given as node index iterable

        Returns:
            list: edgeSequence route given as edge ID list
        """
        node_pairs = zip(nodeSequence, nodeSequence[1:])
        return [adjacencyEdgeID[row][col] for row, col in node_pairs]

    def getNumberOfRemainingVehicles(self, psvList):
        """ Get number of remaining searching vehicles

        Args:
            psvList (list): List of parking search vehicle objects

        Returns:
            int: Number of remaining vehicles which are not parked
        """
        return sum(1 for psv in psvList if not psv.getParkedStatus())

    def getNumberOfParkedVehicles(self, psvList):
        """ Get number of successfully parked vehicles

        Args:
            psvList (list): List of parking search vehicle objects

        Returns:
            int: Number of parked vehicles
        """
        return sum(1 for psv in psvList if psv.getParkedStatus())

    def initPOI(self):
        """ Initialize parking spaces geommetry in SUMO gui """
        for ps in self._environment._allParkingSpaces:
            traci.poi.add(
                    "ParkingSpace" + str(ps.name),
                    traci.simulation.convert2D(
                        str(ps.edgeID), (ps.position - 2.0))[0], 
                    traci.simulation.convert2D(
                        str(ps.edgeID), (ps.position - 2.0))[1],
                    (255, 0, 0, 0))

    def updatePOIColors(self):
        """ Update color of parking places in SUMO gui """
        for ps in self._environment._allParkingSpaces:
            if ps.available:
                traci.poi.setColor("ParkingSpace" + str(ps.name),
                                   (0, 255, 0, 0))
            if ps.assignedToVehicleID:
                traci.poi.setColor("ParkingSpace" + str(ps.name),
                                   (255, 165, 0, 0))

    def computePhase2Routings(self):
        """ Computes phase 2 routing """
        routes = phase2.Phase2Routes(self)
        cooperation = self._sim_dir.get("coopratioPhase2")
        if cooperation == 1.0:
            l_cooperativeRoutes = routes.routes(1.0, penalty=0.2)
            l_individualRoutes = l_cooperativeRoutes
        elif cooperation == 0.0:
            l_individualRoutes = routes.routes(0.0, penalty=0)
            l_cooperativeRoutes = l_individualRoutes
        else:
            l_cooperativeRoutes = routes.routes(cooperation, penalty=0.2)
            l_individualRoutes = routes.individualRoutes()

        # For tests
        # assert routes.routes(1.0, penalty=0.2) == routes.cooperativeRoutes(0.2)
        # assert routes.routes(0.0, penalty=0.2) == l_cooperativeRoutes

        return l_individualRoutes, l_cooperativeRoutes
