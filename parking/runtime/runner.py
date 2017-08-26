#!/usr/bin/env python3
from __future__ import print_function, absolute_import

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
        """ Declare environment variable 'SUMO_HOME', for more info refer to:
        http://sumo.dlr.de/wiki/TraCI/Interfacing_TraCI_from_Python """)

import traci

from parking.vehicle.parkingSearchVehicle import ParkingSearchVehicle
from parking.common.vehicleFactory import generatePsvDemand
from parking.env.environment import Environment
from parking.runtime.phase2 import Phase2Routes


class Runtime(object):
    """ Runtime object """

    def __init__(self, p_config):
        """ Runtime object

        Args:
            p_args (str): Arguments provided by command line via argparse
        """

        self._config = p_config
        self._sim_dir = self._config.getCfg("simulation")
        self._environment = Environment(self._config)
        self._vehicle_config = self._config.getCfg("vehicle")

        # run sumo with gui or headless, depending on the --gui flag
        self._sumoBinary = checkBinary('sumo-gui') if not self._sim_dir.get(
            "headless") else checkBinary('sumo')

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

        self.initPOI()
        self.updatePOIColors()

        # do simulation as long as vehicles are present in the network
        while traci.simulation.getMinExpectedNumber() > 0:
            # tell SUMO to do a simulation step
            traci.simulationStep()
            self.updatePOIColors()
            # increase local time counter
            step += 1
            # every 1000 steps: ensure local time still corresponds to SUMO
            if step != (traci.simulation.getCurrentTime() / 1000):
                print("TIMESTEP ERROR", step, "getCurrentTime",
                      traci.simulation.getCurrentTime())
            # if a new vehicle has departed in SUMO, create the corresponding
            # Python representation and remove the vehicles that have
            # disappeared in SUMO
            dep_list = traci.simulation.getDepartedIDList()
            # TODO: arr list is always empty? Possible bug i.e. we dont set
            # vehicles to arrived or something
            arr_list = traci.simulation.getArrivedIDList()
            l_departedVehicles = (x for x in dep_list if x not in arr_list)

            # TODO: from one debugging session I got the order of
            # parkinSearchVehicles = [veh0, veh1, veh3, veh2, veh4]
            # probably arr_list is not given in order...
            l_parkingSearchVehicles.extend(
                    ParkingSearchVehicle(vehID, self._environment,
                        self._config, i_run, step,
                        self._environment._net.getEdge(l_individualRoutes[vehID][-1]).getToNode().getID(),
                        l_cooperativeRoutes[vehID],
                        l_individualRoutes[vehID])
                    for vehID in l_departedVehicles)

            # update status of all vehicles
            for psv in (v for v in l_parkingSearchVehicles if v.is_parked() is False):
                psv.update(step)
                env_edges = self._environment._roadNetwork["edges"]
                for edge in env_edges:
                    oppositeEdgeID = env_edges[edge]["oppositeEdgeID"]
                    visitCount = (psv.traversed_route.count(str(edge)) +
                                  psv.traversed_route.count(oppositeEdgeID))
                    plannedCount = (psv.active_route.count(str(edge)) +
                                    psv.active_route.count(oppositeEdgeID))
                    env_edges[edge]["visitCount"][psv.name] = visitCount
                    env_edges[edge]["plannedCount"][psv.name] = plannedCount

                # if last edge, choose next possible edges to continue
                if psv.last_edge():
                    lastSegment = psv.current_route[-1]
                    succEdges = self._environment._net.getEdge(lastSegment).getToNode().getOutgoing()

                    # calculate costs for every edge except opposite direction
                    # of current edge
                    succEdgeCost = {}
                    for edge in succEdges:
                        # consider all successor edges, BUT if no opposite edge
                        # exists, don't try to exclude it.
                        if lastSegment in self._environment._oppositeEdgeID:
                            if len(succEdges) == 1:
                                succEdgeCost[str(edge.getID())] = self.edgeCost(psv, edge)
                            elif not str(edge.getID()) == self._environment._oppositeEdgeID[lastSegment]:
                                succEdgeCost[str(edge.getID())] = self.edgeCost(psv, edge)
                            # TODO: there is missing else here?
                        else:
                            succEdgeCost[str(edge.getID())] = self.edgeCost(psv, edge)

                    # calculate minima of succEdgeCost
                    minValue = min(succEdgeCost.values())
                    minKeys = [key for key in succEdgeCost if succEdgeCost[key] == minValue]

                    # choose randomly if costs are equal
                    p3_prob = self._vehicle_config["phase3randomprob"]
                    if random.random() < p3_prob:
                        next_link = random.choice(list(succEdgeCost.keys()))
                    else:
                        next_link = random.choice(minKeys)

                    psv.append_route(next_link)

            # break the while-loop if all SUMO vehicles have parked
            if remaining_vehicles(l_parkingSearchVehicles) == 0:
                if self._sim_dir.get("verbose"):
                    print("SUCCESSFULLY PARKED:",
                          parked_vehicles(l_parkingSearchVehicles), "OUT OF",
                                          self._sim_dir.get("vehicles"))
                break

        # close the TraCI control loop
        traci.close()
        sys.stdout.flush()
        l_sumoProcess.wait()

        total_parked = parked_vehicles(l_parkingSearchVehicles)
        searchTimes = [veh.search_time for veh in l_parkingSearchVehicles]
        searchDistances = [veh.search_distance for veh in l_parkingSearchVehicles]
        walkingTimes = [veh.walk_time for veh in l_parkingSearchVehicles]
        walkingDistances = [veh.walk_distance for veh in l_parkingSearchVehicles]
        searchPhases = [veh.search_phase for veh in l_parkingSearchVehicles]

        # TODO: this should probably just return vehicles and leave processing
        # to other instances
        return (total_parked,
                searchTimes,
                walkingTimes,
                searchDistances,
                walkingDistances,
                searchPhases)

    def edgeCost(self, psv, edge):
        """ Calculate cost for an edge for a specific search vehicle

        Args:
            psv: parking search vehicle
            edge: edge

        Returns:
            float: cost of edge
        """
        env_edges = self._environment._roadNetwork["edges"]
        veh_weights = self._vehicle_config["weights"]

        psv_dest_edge = str(psv.destination_edge_id)
        toNodedestinationEdge = env_edges[psv_dest_edge]["toNode"]

        # get counts from environment
        edge_id = edge.getID()
        psv_name = psv.name
        selfVisitCount = env_edges[edge_id]["visitCount"][psv_name]

        visit_count_sum = sum(env_edges[edge_id]["visitCount"].values())
        externalVisitCount = visit_count_sum - selfVisitCount

        externalPlannedCount = sum(env_edges[edge_id]["plannedCount"].values())

        def cost_wrap(coop):
            return veh_weights[coop]["distance"] \
                   * env_edges[edge_id]["nodeDistanceFromEndNode"][toNodedestinationEdge]\
                   + selfVisitCount * veh_weights[coop]["selfvisit"]\
                   + externalVisitCount * veh_weights[coop]["externalvisit"]\
                   + externalPlannedCount * veh_weights[coop]["externalplanned"]

        if psv._driverCooperatesPhase3:
            return cost_wrap("coop")
        return cost_wrap("noncoop")

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

    def initPOI(self):
        """ Initialize parking spaces geommetry in SUMO gui """
        for ps in self._environment._allParkingSpaces:
            traci.poi.add(
                    "ParkingSpace" + str(ps.name),
                    traci.simulation.convert2D(str(ps.edgeID), (ps.position - 2.0))[0], 
                    traci.simulation.convert2D(str(ps.edgeID), (ps.position - 2.0))[1],
                    (255, 0, 0, 0))

    def updatePOIColors(self):
        """ Update color of parking places in SUMO gui """
        for ps in self._environment._allParkingSpaces:
            p_name = "ParkingSpace" + str(ps.name)
            if ps.available:
                traci.poi.setColor(p_name, (0, 255, 0, 0))
            if ps.assignedToVehicleID:
                traci.poi.setColor(p_name, (255, 165, 0, 0))

    def computePhase2Routings(self):
        """ Computes phase 2 routing """
        routes = Phase2Routes(self)
        cooperation = self._sim_dir["coopratioPhase2"]
        # TODO: this is still hardcoded
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


def remaining_vehicles(psvList):
    """ Get number of remaining searching vehicles.

    Args:
        psvList (list): List of parking search vehicle objects

    Returns:
        int: Number of remaining vehicles which are not parked
    """
    return sum(1 for psv in psvList if not psv.is_parked())

def parked_vehicles(psvList):
    """ Get number of successfully parked vehicles.

    Args:
        psvList (list): List of parking search vehicle objects

    Returns:
        int: Number of parked vehicles
    """
    return sum(1 for psv in psvList if psv.is_parked())
