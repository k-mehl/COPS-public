#!usr/bin/env python
from __future__ import print_function

import os

import sumolib

from common.cooperativeSearch import *
from vehicle.parkingSearchVehicle import *
from common.vehicleFactory import *
from env.environment import *
from runner import *

# Python2-3 compatibility layer
try:
    xrange
except NameError:
    xrange = range

try:
    import itertools.izip as zip
    import itertools.imap as map
except ImportError:
    pass


class Phase2Routes(Runtime):
    def __init__(self, conf):
        super(Phase2Routes, self).__init__(conf)
        self.vehicleOriginNode = {}
        self.vehicleOriginNodeIndex = {}
        self.vehicleDestinationNode = {}
        self.vehicleDestinationNodeIndex = {}
        self.allVehicleIDs = []
        self.allOriginNodeIndices = []
        self.allDestinationNodeIndices = []
        # HACK...
        if os.path.isfile(os.path.join(self._config.getCfg("simulation").get("resourcedir"), self._config.getCfg("simulation").get("routefile"))) and self._config.getCfg("simulation").get("forceroutefile"):
            self._routefile = self._config.getCfg("simulation").get("routefile")
        else:
            self._routefile = self._config.getCfg("simulation").get("routefile")
            generatePsvDemand(self._config.getCfg("simulation").get("vehicles"), self._config.getCfg("simulation").get("resourcedir"), self._routefile)
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

        self.nodeToEdge = self.convertNodeSequenceToEdgeSequence

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
