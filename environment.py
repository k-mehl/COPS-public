import traci
import sumolib

from parkingSpace import *

import random
import itertools

class Environment(object):
    def __init__(self):
        self._roadNetwork = {}

        self._roadNetwork["nodes"] = {}
        self._roadNetwork["edges"] = {}

        self._nodes = map(lambda x: str(x.id), sumolib.output.parse('reroute.nod.xml', ['node']))
        self._edges = map(lambda x: str(x.id), sumolib.output.parse('reroute.edg.xml', ['edge']))

        for node in self._nodes:
            self._roadNetwork["nodes"][node] = {}
        for edge in self._edges:
            self._roadNetwork["edges"][edge] = {}

        self._numberOfNodesinNetwork = len(self._nodes)
        self._numberOfEdgesinNetwork = len(self._edges)

        self._net = sumolib.net.readNet('reroute.net.xml')

        self._convertNodeIDtoNodeIndex = {}
        self._convertNodeIndexToNodeID = {}

        self._adjacencyMatrix = [[0 for x in range(self._numberOfNodesinNetwork)] \
            for x in range(self._numberOfNodesinNetwork)]

        self._adjacencyEdgeID = [["" for x in range(self._numberOfNodesinNetwork)] \
            for x in range(self._numberOfNodesinNetwork)]

        for fromNode in range(self._numberOfNodesinNetwork):
            fromNodeID = self._nodes[fromNode]
            # fill node dictionaries by the way
            self._convertNodeIndexToNodeID[fromNode]=fromNodeID
            self._convertNodeIDtoNodeIndex[fromNodeID]=fromNode
            for toNode in range(self._numberOfNodesinNetwork):
                toNodeID = self._nodes[toNode]
                for edge in self._edges:
                    if (self._net.getEdge(edge).getFromNode().getID()==fromNodeID and
                        self._net.getEdge(edge).getToNode().getID()==toNodeID):
                        self._adjacencyMatrix[fromNode][toNode] = \
                            self._net.getEdge(edge).getLength()
                        self._adjacencyEdgeID[fromNode][toNode] = \
                            str(self._net.getEdge(edge).getID())

        self._oppositeEdgeID = dict( filter(
                lambda (x,y): self._net.getEdge(x).getToNode().getID() == self._net.getEdge(y).getFromNode().getID() and
                              self._net.getEdge(x).getFromNode().getID() == self._net.getEdge(y).getToNode().getID(),
                itertools.permutations(self._edges, 2)
        ))

        for edge in self._edges:
            self._roadNetwork["edges"][edge]["length"] = self._net.getEdge(edge).getLength()
            self._roadNetwork["edges"][edge]["visitCount"] = 0
            self._roadNetwork["edges"][edge]["fromNode"] = str(self._net.getEdge(edge).getFromNode().getID())
            self._roadNetwork["edges"][edge]["toNode"] = str(self._net.getEdge(edge).getToNode().getID())
            self._roadNetwork["edges"][edge]["succEdgeID"] = map(lambda x: str(x.getID()), self._net.getEdge(edge).getToNode().getOutgoing())
            if edge in self._oppositeEdgeID:
                self._roadNetwork["edges"][edge]["oppositeEdgeID"] = self._oppositeEdgeID[edge]
            else:
                self._roadNetwork["edges"][edge]["oppositeEdgeID"] = []
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
                position = 18.0
                # as long as there are more than 10 meters left on the edge, add
                # another parking space
                while position < (length-10.0):
                    self._roadNetwork["edges"][edge]["parkingSpaces"].append(ParkingSpace(self._parkingSpaceNumber, edge,
                        position))
                    self._allParkingSpaces.append(self._roadNetwork["edges"][edge]["parkingSpaces"][-1])
                    if self._parkingSpaceNumber < 5:
                        print(self._allParkingSpaces)
                    # also add SUMO poi for better visualization in the GUI
                    #traci.poi.add("ParkingSpace" + str(parkingSpaceNumber),
                    #    traci.simulation.convert2D(edge,(position-2.0))[0],
                    #    traci.simulation.convert2D(edge,(position-2.0))[1],
                    #    (255,0,0,0))
                    # increment counter
                    self._parkingSpaceNumber+=1
                    # go seven meters ahead on the edge
                    position+=7.0