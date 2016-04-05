#!/usr/bin/env python
from __future__ import print_function

import os
import subprocess
import sys

# (from SUMO examples:)
# we need to import python modules from the $SUMO_HOME/tools directory
try:
    sys.path.append(os.path.join(os.path.dirname(
        "__file__"), '..', '..', '..', "tools"))  # tutorial in tests
    sys.path.append(os.path.join(os.environ.get("SUMO_HOME", os.path.join(
        os.path.dirname("__file__"), "..", "..")), "tools"))  # tutorial in docs
    from sumolib import checkBinary
except ImportError:
    sys.exit("please declare environment variable 'SUMO_HOME' as the root"+ \
    "directory of your sumo installation (it should contain folders 'bin'," + \
    "'tools' and 'docs')")

import traci
import sumolib

from common.cooperativeSearch import *
from vehicle.parkingSearchVehicle import *
from common.vehicleFactory import *
from env.environment import *

class Runtime(object):

    ## C'tor
    # @param p_args Arguments provided by command line via argparse
    def __init__(self, p_config):

        self._config = p_config

        # run sumo with gui or headless, depending on the --gui flag
        self._sumoBinary = checkBinary('sumo-gui') if not self._config.getCfg("simulation").get("headless") else checkBinary('sumo')

        self._environment = Environment(self._config)
        #print(self._environment._roadNetwork["edges"])

    ## Runs the simulation on both SUMO and Python layers
    def run(self, i_run):

        # if there is a run configuration loaded use it to populate parkingspaces in environment otherwise initialize new
        if not self._config.getRunCfg(str(i_run)):
            print("* no run cfg found. Initializing random parking spaces.")
            self._environment.initParkingSpaces(i_run)

        elif self._config.isRunCfgOk(i_run):
            self._environment.loadParkingSpaces(i_run)
        else:
            return

        # if --routefile flag is provided, use the file for routing,
        # otherwise generate (and overwrite if exists) route file (reroute.rou.xml) for this simulation run
        # using the given number of parking search vehicles
        if self._config.getCfg("simulation").get("routefile") == "reroute.rou.xml":
            self._routefile = "reroute.rou.xml"
            generatePsvDemand(self._config.getCfg("simulation").get("vehicles"), self._config.getCfg("simulation").get("resourcedir"), self._routefile)
        else:
            self._routefile = self._config.getCfg("simulation").get("routefile")

        # this is the normal way of using traci. sumo is started as a
        # subprocess and then the python script connects and runs
        l_sumoProcess = subprocess.Popen(
            [self._sumoBinary,
             "-n", os.path.join(self._config.getCfg("simulation").get("resourcedir"), "reroute.net.xml"),
             "-r", os.path.join(self._config.getCfg("simulation").get("resourcedir"), self._routefile),
             "--tripinfo-output", os.path.join(self._config.getCfg("simulation").get("resourcedir"), "tripinfo.xml"),
             "--gui-settings-file", os.path.join(self._config.getCfg("simulation").get("resourcedir"), "gui-settings.cfg"),
             "--no-step-log",
             "--remote-port", str(self._config.getCfg("simulation").get("sumoport"))],
            stdout=sys.stdout,
            stderr=sys.stderr)

        # execute the TraCI control loop
        traci.init(self._config.getCfg("simulation").get("sumoport"))

        # internal clock variable, start with 0
        step = 0

        # create empty list for parking search vehicles
        l_parkingSearchVehicles=[]

        # compute phase 2 routing information (individual and cooperative)
        l_individualRoutes, l_cooperativeRoutes = self.computePhase2Routings()

        # create lists for search time and distance results
        searchTimes = []
        searchDistances = []
        walkingDistances = []
        searchPhases = []

        self.initPOI()
        self.updatePOIColors()

        # do simulation time steps as long as vehicles are present in the network
        while traci.simulation.getMinExpectedNumber() > 0:
            # tell SUMO to do a simulation step
            traci.simulationStep()
            self.updatePOIColors()
            # increase local time counter
            step += 1
            # every 1000 steps: ensure local time still corresponds to SUMO
            # simulation time
            # (just a safety check for now, can possibly be removed later)
            if step != (traci.simulation.getCurrentTime()/1000):
                print("TIMESTEP ERROR", step, "getCurrentTime",
                        traci.simulation.getCurrentTime())
            # if a new vehicle has departed in SUMO, create the corresponding Python
            # representation
            l_departedVehicles = traci.simulation.getDepartedIDList()

            # get individual vehicle preferences from run config if present, otherwise generate values
            l_run = str(i_run)

            l_parkingSearchVehicles.extend(map(
                    lambda vehID: ParkingSearchVehicle( vehID, self._environment, self._config, i_run, step,
                                                        self._environment._net.getEdge(l_individualRoutes[vehID][-1]).getToNode().getID(),
                                                        l_cooperativeRoutes[vehID], l_individualRoutes[vehID]),
                    l_departedVehicles
            ))

            # if a vehicle has disappeared in SUMO, remove the corresponding Python
            # representation
            for vehID in traci.simulation.getArrivedIDList():
                    # for now: output to console that the vehicle disappeared upon
                    # reaching the destination
                print(str(vehID),
                        "did not find an available parking space during phase 2.")
                l_parkingSearchVehicles.remove(ParkingSearchVehicle(vehID))
            # update status of all vehicles
            # TODO: differentiate this update method into e.g.
            #       getVehicleData() ..... all TraCI getSomething commands
            #       computeRouting() ..... non-cooperative routing
            #       computeCoopRouting() . cooperative routing
            #       selectRouting() ...... select whether to cooperate or not
            #       setVehicleData() ..... all TraCI setSomething commands
            for psv in l_parkingSearchVehicles:

                result = psv.update(step)
                #count edge visits of each vehicle
                #TODO: make visit update more efficient
                for edge in self._environment._roadNetwork["edges"].keys():
                    traversedRoute = psv.getTraversedRoute()[:]
                    plannedRoute = psv.getActiveRoute()[:]
                    #traversedRoutePlusCurrentEdge.append(psv.getActiveRoute()[0])

                    oppositeEdgeID = self._environment._roadNetwork["edges"][edge]["oppositeEdgeID"]
                    visitCount = traversedRoute.count(str(edge)) \
                        +traversedRoute.count(oppositeEdgeID)
                    plannedCount = plannedRoute.count(str(edge)) \
                        +plannedRoute.count(oppositeEdgeID)
                    self._environment._roadNetwork["edges"][edge]["visitCount"][psv.getName()] = visitCount
                    self._environment._roadNetwork["edges"][edge]["plannedCount"][psv.getName()] = plannedCount

                # if result values could be obtained, the vehicle found
                # a parking space in the last time step
                if result:
                    searchTimes.append(result[1])
                    searchDistances.append(result[2])
                    walkingDistances.append(result[3])
                    searchPhases.append(result[4])
                else:
                    # if the vehicle is on the last route segment,
                    # choose one of the possible next edges to continue
                    if psv.isOnLastRouteSegment():
                        currentRoute = psv.getVehicleRoute()
                        succEdges = \
                            self._environment._net.getEdge(currentRoute[-1]).getToNode().getOutgoing()

                        #calculate costs for every edge except opposite direction of current edge
                        succEdgeCost = {}

                        for edge in succEdges:
                            # consider all successor edges, BUT if no opposite edge exists, don't try to
                            # exclude it.
                            if currentRoute[-1] in self._environment._oppositeEdgeID:
                                if not str(edge.getID()) == self._environment._oppositeEdgeID[currentRoute[-1]]:
                                    succEdgeCost[str(edge.getID())] = self.calculateEdgeCost(psv, edge)
                            else:
                                succEdgeCost[str(edge.getID())] = self.calculateEdgeCost(psv, edge)

                        #calculate minima of succEdgeCost
                        minValue = numpy.min(succEdgeCost.values())
                        minKeys = [key for key in succEdgeCost if succEdgeCost[key] == minValue]

                        #choose randomly if costs are equal
                        if len(minKeys) > 1:
                            nextRouteSegment = random.choice(minKeys)
                        else:
                            nextRouteSegment = minKeys[0]

                        psv.setNextRouteSegment(nextRouteSegment)

            # break the while-loop if all remaining SUMO vehicles have
            # successfully parked
            if self.getNumberOfRemainingVehicles(l_parkingSearchVehicles)==0:
                print("SUCCESSFULLY PARKED:",
                    self.getNumberOfParkedVehicles(l_parkingSearchVehicles),
                    "OUT OF", self._config.getCfg("simulation").get("vehicles"))
                break

        # (from SUMO examples):
        # close the TraCI control loop
        traci.close()
        sys.stdout.flush()

        l_sumoProcess.wait()

        # Return results
        return self.getNumberOfParkedVehicles(l_parkingSearchVehicles), searchTimes, searchDistances, walkingDistances, searchPhases

    ## Calculate cost for an edge for a specific search vehicle
    #  @param psv parking search vehicle
    #  @param edge edge
    #  @return cost of edge
    def calculateEdgeCost(self, psv, edge):
        toNodedestinationEdge = self._environment._roadNetwork["edges"][str(psv.getDestinationEdgeID())]["toNode"]

        #get counts from environment
        selfVisitCount = self._environment._roadNetwork["edges"][edge.getID()]["visitCount"][psv.getName()]
        externalVisitCount = sum(self._environment._roadNetwork["edges"][edge.getID()]["visitCount"].values())-selfVisitCount
        externalPlannedCount = sum(self._environment._roadNetwork["edges"][edge.getID()]["plannedCount"].values())

        #calculate cost
        if psv._driverCooperatesPhase3:
            cost = self._config.getCfg("vehicle").get("weights").get("coop").get("distance") * \
                   self._environment._roadNetwork["edges"][edge.getID()]["nodeDistanceFromEndNode"][toNodedestinationEdge]\
            + selfVisitCount*self._config.getCfg("vehicle").get("weights").get("coop").get("selfvisit")\
            + externalVisitCount * self._config.getCfg("vehicle").get("weights").get("coop").get("externalvisit")\
            + externalPlannedCount * self._config.getCfg("vehicle").get("weights").get("coop").get("externalplanned")
        else:
            cost = self._config.getCfg("vehicle").get("weights").get("noncoop").get("distance") * \
                   self._environment._roadNetwork["edges"][edge.getID()]["nodeDistanceFromEndNode"][toNodedestinationEdge]\
            + selfVisitCount*self._config.getCfg("vehicle").get("weights").get("noncoop").get("selfvisit")\
            + externalVisitCount * self._config.getCfg("vehicle").get("weights").get("noncoop").get("externalvisit")\
            + externalPlannedCount * self._config.getCfg("vehicle").get("weights").get("noncoop").get("externalplanned")
        return cost

    ## Convert a route given as sequence of node indices into the corresponding
    #  sequence of edge IDs
    #  @param adjacencyEdgeID adjacency matrix containing the edge IDs
    #  @param nodeSequence route given as node index list
    #  @return edgeSequence route given as edge ID list
    def convertNodeSequenceToEdgeSequence(self, adjacencyEdgeID, nodeSequence):
        edgeSequence = []
        for segment in range(0, len(nodeSequence)-1):
            nextEdge=adjacencyEdgeID[nodeSequence[segment]][nodeSequence[segment+1]]
            if nextEdge=="":
                print("ERROR: could not convert node sequence to edge sequence.")
                #exit() #TODO remove this exit, wtf?!
            else:
                edgeSequence.append(nextEdge)
        return edgeSequence

    ## Get number of remaining searching vehicles
    #  @param psvList List of parking search vehicle objects
    #  @return Number of remaining vehicles which are not parked
    def getNumberOfRemainingVehicles(self, psvList):
        if not psvList:
            return 0

        remainingVehicles = 0
        for psv in psvList:
            if not psv.getParkedStatus():
                remainingVehicles += 1
        return remainingVehicles


    ## Get number of successfully parked vehicles
    #  @param psvList List of parking search vehicle objects
    #  @return Number of parked vehicles
    def getNumberOfParkedVehicles(self, psvList):
        if not psvList:
            return 0

        parkedVehicles = 0
        for psv in psvList:
            if  psv.getParkedStatus():
                parkedVehicles += 1
        return parkedVehicles


    def initPOI(self):
        for ps in self._environment._allParkingSpaces:
            traci.poi.add("ParkingSpace" + str(ps.name),
                        traci.simulation.convert2D(str(ps.edgeID),(ps.position-2.0))[0],
                        traci.simulation.convert2D(str(ps.edgeID),(ps.position-2.0))[1],
                        (255,0,0,0))


    def updatePOIColors(self):
        for ps in self._environment._allParkingSpaces:
            if ps.available:
                traci.poi.setColor("ParkingSpace"+str(ps.name),(0,255,0,0))
            if ps.assignedToVehicleID:
                traci.poi.setColor("ParkingSpace"+str(ps.name),(255,165,0,0))


    def computePhase2Routings(self):
        # prepare dictionaries with vehicle O/D data (IDs and indices)
        # by parsing the generated route XML file
        vehicleOriginNode = {}
        vehicleOriginNodeIndex = {}
        vehicleDestinationNode = {}
        vehicleDestinationNodeIndex = {}
        allVehicleIDs = []
        allOriginNodeIndices = []
        allDestinationNodeIndices = []
        for trip in sumolib.output.parse_fast( \
                os.path.join(self._config.getCfg("simulation").get("resourcedir"), self._routefile), 'trip', ['id','from','to']):
            allVehicleIDs.append(trip.id)
            vehicleOriginNode[trip.id] =  \
                self._environment._net.getEdge(trip.attr_from).getFromNode().getID()
            vehicleOriginNodeIndex[trip.id] = \
                self._environment._convertNodeIDtoNodeIndex[vehicleOriginNode[trip.id]]
            vehicleDestinationNode[trip.id] = \
                self._environment._net.getEdge(trip.to).getToNode().getID()
            vehicleDestinationNodeIndex[trip.id] = \
                self._environment._convertNodeIDtoNodeIndex[vehicleDestinationNode[trip.id]]
            allOriginNodeIndices.append(vehicleOriginNodeIndex[trip.id])
            allDestinationNodeIndices.append(vehicleDestinationNodeIndex[trip.id])

        # use Aleksandar's Cooperative Search Router to create a dictionary
        # containing all cooperative vehicle routes (only once in advance)
        coopRouter = CooperativeSearch(self._environment._adjacencyMatrix, allOriginNodeIndices)
        shortestNeighbors = coopRouter.shortest()

        l_cooperativeRoutes = dict(map(
            lambda trip: ( allVehicleIDs[trip], self.convertNodeSequenceToEdgeSequence(
                self._environment._adjacencyEdgeID,coopRouter.reconstruct_path(
                            shortestNeighbors[trip],allDestinationNodeIndices[trip],
                            allOriginNodeIndices[trip])) ),
                xrange(len(allVehicleIDs))
        ))

        # use Aleksandar's Cooperative Search Router to create a dictionary
        # containing all non-cooperative vehicle routes (only once in advance)
        indyRouter = CooperativeSearch(self._environment._adjacencyMatrix, allOriginNodeIndices, 0)
        indyShortestNeighbors = indyRouter.shortest()

        l_individualRoutes = dict(map(
            lambda trip: ( allVehicleIDs[trip], self.convertNodeSequenceToEdgeSequence(
                self._environment._adjacencyEdgeID,indyRouter.reconstruct_path(
                            indyShortestNeighbors[trip],allDestinationNodeIndices[trip],
                            allOriginNodeIndices[trip]))
            ),
            xrange(len(allVehicleIDs))
        ))
        return l_individualRoutes, l_cooperativeRoutes