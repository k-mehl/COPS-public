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

            