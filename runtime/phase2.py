#!usr/bin/env python
from __future__ import print_function

import os

import sumolib

from common.cooperativeSearch import *
from runner import *

# Python2-3 compatibility layer
try:
    xrange
except NameError:
    xrange = range

try:
    import itertools.izip as zip
except ImportError:
    pass


class Phase2Routes(object):
    def __init__(self, parent_class):
        # Take what you need from parent_class
        self._config = parent_class._config
        self._environment = parent_class._environment
        self._routefile = parent_class._routefile
        self.nodeToEdge = parent_class.convertNodeSequenceToEdgeSequence

        # prepare dictionaries with vehicle O/D data (IDs and indices)
        # by parsing the generated route XML file
        self.vehicleOriginNode = {}
        self.vehicleOriginNodeIndex = {}
        self.vehicleDestinationNode = {}
        self.vehicleDestinationNodeIndex = {}
        self.allVehicleIDs = []
        self.allOriginNodeIndices = []
        self.allDestinationNodeIndices = []

        for trip in sumolib.output.parse_fast( \
                os.path.join(self._config.getCfg("simulation").get("resourcedir"), self._routefile), 'trip', ['id','from','to']):
            self.allVehicleIDs.append(trip.id)
            self.vehicleOriginNode[trip.id] =  \
                self._environment._net.getEdge(trip.attr_from).getFromNode().getID()
            self.vehicleOriginNodeIndex[trip.id] = \
                self._environment._convertNodeIDtoNodeIndex[self.vehicleOriginNode[trip.id]]
            self.vehicleDestinationNode[trip.id] = \
                self._environment._net.getEdge(trip.to).getToNode().getID()
            self.vehicleDestinationNodeIndex[trip.id] = \
                self._environment._convertNodeIDtoNodeIndex[self.vehicleDestinationNode[trip.id]]
            self.allOriginNodeIndices.append(self.vehicleOriginNodeIndex[trip.id])
            self.allDestinationNodeIndices.append(self.vehicleDestinationNodeIndex[trip.id])

    def cooperativeRoutes(self, penalty):
        coopRouter = CoopSearchHillOptimized(
                                    self._environment._adjacencyMatrix,
                                    self.allOriginNodeIndices,
                                    self.allDestinationNodeIndices,
                                    penalty)
        coopPaths = coopRouter.shortest().optimized()

        edges = (self.nodeToEdge(self._environment._adjacencyEdgeID,
                                 coopPaths[trip])
                 for trip in xrange(len(self.allVehicleIDs)))
        l_cooperativeRoutes = dict(zip(self.allVehicleIDs, edges))
        return l_cooperativeRoutes


    def individualRoutes(self):
        indyRouter = CooperativeSearch(self._environment._adjacencyMatrix,
                                       self.allOriginNodeIndices,
                                       0)
        indyRouter.shortest()
        indyPaths = indyRouter.paths(self.allDestinationNodeIndices)
        edgesIndy = (self.nodeToEdge(self._environment._adjacencyEdgeID,
                                indyPaths[trip])
                     for trip in xrange(len(self.allVehicleIDs)))
        l_individualRoutes = dict(zip(self.allVehicleIDs, edgesIndy))
        return l_individualRoutes

    def mixedCooperation(self):
        raise NotImplementedError
