import traci
import sumolib
import numpy

import random
import itertools
import os

try:
    xrange
except NameError:
    xrange = range

try:
    import itertools.imap as map
    import itertools.ifilter as filter
except ImportError:
    pass

from env.parkingSpace import ParkingSpace


class Environment(object):
    """ Environment class """

    def __init__(self, p_config):

        self._config = p_config

        self._roadNetwork = {}

        self._roadNetwork["nodes"] = {}
        self._roadNetwork["edges"] = {}

        self._nodes = list(map(lambda x: str(x.id), sumolib.output.parse(os.path.join(self._config.getCfg("simulation").get("resourcedir"), 'reroute.nod.xml'), ['node'])))
        self._edges = list(map(lambda x: str(x.id), sumolib.output.parse(os.path.join(self._config.getCfg("simulation").get("resourcedir"), 'reroute.edg.xml'), ['edge'])))

        for node in self._nodes:
            self._roadNetwork["nodes"][node] = {}
        for edge in self._edges:
            self._roadNetwork["edges"][edge] = {}

        self._numberOfNodesinNetwork = len(self._nodes)
        self._numberOfEdgesinNetwork = len(self._edges)

        self._net = sumolib.net.readNet(os.path.join(self._config.getCfg("simulation").get("resourcedir"), 'reroute.net.xml'))

        self._convertNodeIDtoNodeIndex = {}
        self._convertNodeIndexToNodeID = {}

        self._adjacencyMatrix = [[0 for x in xrange(self._numberOfNodesinNetwork)] \
            for x in xrange(self._numberOfNodesinNetwork)]

        self._adjacencyEdgeID = [["" for x in xrange(self._numberOfNodesinNetwork)] \
            for x in xrange(self._numberOfNodesinNetwork)]

        for fromNode in xrange(self._numberOfNodesinNetwork):
            fromNodeID = self._nodes[fromNode]
            # fill node dictionaries by the way
            self._convertNodeIndexToNodeID[fromNode]=fromNodeID
            self._convertNodeIDtoNodeIndex[fromNodeID]=fromNode
            for toNode in xrange(self._numberOfNodesinNetwork):
                toNodeID = self._nodes[toNode]
                for edge in self._edges:
                    if (self._net.getEdge(edge).getFromNode().getID()==fromNodeID and
                        self._net.getEdge(edge).getToNode().getID()==toNodeID):
                        self._adjacencyMatrix[fromNode][toNode] = \
                            self._net.getEdge(edge).getLength()
                        self._adjacencyEdgeID[fromNode][toNode] = \
                            str(self._net.getEdge(edge).getID())

        self._oppositeEdgeID = dict(filter(
                lambda x: self._net.getEdge(x[0]).getToNode().getID() == self._net.getEdge(x[1]).getFromNode().getID() and
                              self._net.getEdge(x[0]).getFromNode().getID() == self._net.getEdge(x[1]).getToNode().getID(),
                itertools.permutations(self._edges, 2)
        ))

        for node in self._nodes:
            self._roadNetwork["nodes"][node]["coordinates"] = self._net.getNode(node).getCoord()

        for edge in self._edges:
            self._roadNetwork["edges"][edge]["length"] = self._net.getEdge(edge).getLength()
            self._roadNetwork["edges"][edge]["fromNode"] = str(self._net.getEdge(edge).getFromNode().getID())
            fromNodeCoord = self._roadNetwork["nodes"][self._roadNetwork["edges"][edge]["fromNode"]]["coordinates"]

            self._roadNetwork["edges"][edge]["toNode"] = str(self._net.getEdge(edge).getToNode().getID())
            toNodeCoord = self._roadNetwork["nodes"][self._roadNetwork["edges"][edge]["toNode"]]["coordinates"]

            self._roadNetwork["edges"][edge]["meanCoord"] = tuple(numpy.divide(numpy.add(fromNodeCoord,toNodeCoord),2))

            self._roadNetwork["edges"][edge]["succEdgeID"] = list(map(lambda x: str(x.getID()), self._net.getEdge(edge).getToNode().getOutgoing()))

            self._roadNetwork["edges"][edge]["nodeDistanceFromEndNode"] = {}

            for node in self._nodes:

                #TODO: discuss the relevant distance measure
                #endNote synonym to toNote used to avoid confusion in variable names
                lineEndNodeToNode = numpy.subtract(self._roadNetwork["edges"][edge]["meanCoord"], self._roadNetwork["nodes"][node]["coordinates"])
                #lineEndNodeToNode = numpy.subtract(toNodeCoord, self._roadNetwork["nodes"][node]["coordinates"])
                self._roadNetwork["edges"][edge]["nodeDistanceFromEndNode"][node] = \
                    numpy.sqrt(numpy.sum(lineEndNodeToNode**2))

            self._roadNetwork["edges"][edge]["visitCount"] = {}
            self._roadNetwork["edges"][edge]["plannedCount"] = {}

            if edge in self._oppositeEdgeID:
                self._roadNetwork["edges"][edge]["oppositeEdgeID"] = self._oppositeEdgeID[edge]
            else:
                self._roadNetwork["edges"][edge]["oppositeEdgeID"] = []

    def loadParkingSpaces(self, p_run):
        """ Load parking spaces

        Args:
            p_run (int): run number
        """
        if self._config.getCfg("simulation").get("verbose"):
            print("* loading parking spaces from run cfg")
        self._parkingSpaceNumber = self._config.getCfg("simulation").get("parkingspaces").get("free")

        l_cfgparkingspaces = self._config.getRunCfg(str(p_run)).get("parkingspaces")
        self._allParkingSpaces = list(map(lambda v: ParkingSpace(v.get("name"),
                                                         v.get("edgeID"),
                                                         v.get("position"),
                                                         available=v.get("available")),
                              l_cfgparkingspaces.values()))

        for edge in self._edges:
            self._roadNetwork["edges"][edge]["parkingSpaces"] = list(filter(lambda p: p.edgeID == edge, self._allParkingSpaces))
        if self._config.getCfg("simulation").get("verbose"):
            print("  -> done.")

    def initParkingSpaces(self, p_run):
        """ Initialize parking spaces

        Args:
            p_run (int): run number
        """
        for edge in self._edges:
            #self._roadNetwork["edges"][edge]["visitCount"] = 0
            self._roadNetwork["edges"][edge]["parkingSpaces"] = []

        self._parkingSpaceNumber = 0
        self._allParkingSpaces = []

        for edge in self._edges:
            # if an edge is at least 40 meters long, start at 18 meters and
            # create parking spaces every 7 meters until up to 10 meters before the
            # edge ends.
            #     (vehicles can only 'see' parking spaces once they are on the same
            #     edge;
            #     starting at 18 meters ensures the vehicles can safely stop at the
            #     first parking space if it is available)
            length = self._roadNetwork["edges"][edge]["length"]
            if length > 40.0:
                position = 20.0
                # as long as there are more than 10 meters left on the edge, add
                # another parking space
                while position < (length-10.0):
                    self._roadNetwork["edges"][edge]["parkingSpaces"].append(ParkingSpace(self._parkingSpaceNumber, edge,
                        position))
                    self._allParkingSpaces.append(self._roadNetwork["edges"][edge]["parkingSpaces"][-1])
                    # also add SUMO poi for better visualization in the GUI
                    #traci.poi.add("ParkingSpace" + str(parkingSpaceNumber),
                    #    traci.simulation.convert2D(edge,(position-2.0))[0],
                    #    traci.simulation.convert2D(edge,(position-2.0))[1],
                    #    (255,0,0,0))
                    # increment counter
                    self._parkingSpaceNumber+=1
                    # go seven meters ahead on the edge
                    position+=7.0

        # mark a number parking spaces as available as specified per command line
        # argument
        for i in xrange(0, self._config.getCfg("simulation").get("parkingspaces").get("free")):
            # check whether we still have enough parking spaces to make available
            if self._config.getCfg("simulation").get("parkingspaces").get("free") > self._parkingSpaceNumber:
                print("Too free many parking spaces for network.")
                #exit() #TODO remove this exit, wtf?! Btw, this error handling should probably occur _before_ running the simulation!
            # select a random parking space which is not yet available, and make it
            # available
            success = False
            while not success:
                availableParkingSpaceID = int(random.random() * self._parkingSpaceNumber)
                if not self._allParkingSpaces[availableParkingSpaceID].available:
                    success = True
            # make sure the available parking space is not assigned to any vehicle
            self._allParkingSpaces[availableParkingSpaceID].unassign()

        # update parking spaces in run configuration
        self._config.updateRunCfgParkingspaces(p_run, self._allParkingSpaces)
