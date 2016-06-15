#!usr/bin/env python
from __future__ import print_function

import os
import random

import sumolib

from common.cooperativeSearch import *
from .runner import *

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
        """ Phase 2 routing class with methods to compute mixed ratin
        cooperation during parking search

        Args:
            parent_class: currently this is Runtime object but this should be
                solved better
        """
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

    def cooperativeRoutes(self, penalty, **kwargs):
        """ Cooperative routes that are currently optimized.

        Args:
            penalty (float): penalization for visiting the same edges in case
                of cooperative routing
            kwargs:
                adjacency_matrix,
                adjacency_edge_id,
                origin_node_ind,
                destination_node_ind,
                vehicle_IDs

        Returns:
            dict: keys are vehicle ID's, and edgeID's
        """
        # TODO: remove defaults? should there be so manz defaults?
        adjacency_matrix = kwargs.get("adjacency_matrix",
                                      self._environment._adjacencyMatrix)
        adjacency_edge_id = kwargs.get("adjacency_edge_id",
                                       self._environment._adjacencyEdgeID)
        origin_node_ind = kwargs.get("origin_node_ind",
                                     self.allOriginNodeIndices)
        destination_node_ind = kwargs.get("destination_node_ind",
                                          self.allDestinationNodeIndices)
        vehicle_IDs = kwargs.get("vehicle_IDs", self.allVehicleIDs)

        coopRouter = CoopSearchHillOptimized(adjacency_matrix,
                                             origin_node_ind,
                                             destination_node_ind,
                                             penalty)
        coopPaths = coopRouter.shortest().optimized()
        edges = (self.nodeToEdge(adjacency_edge_id, coopPaths[trip])
                 for trip in xrange(len(vehicle_IDs)))
        return dict(zip(vehicle_IDs, edges))

    def individualRoutes(self, **kwargs):
        """ Just a shortest path routes for multiple agents.

        Args:
            kwargs:
                adjacency_matrix,
                adjacency_edge_id,
                origin_node_ind,
                destination_node_ind,
                vehicle_IDs

        Returns:
            dict: keys are vehicle ID's, and edgeID's
        """
        adjacency_matrix = kwargs.get("adjacency_matrix",
                                      self._environment._adjacencyMatrix)
        adjacency_edge_id = kwargs.get("adjacency_edge_id",
                                       self._environment._adjacencyEdgeID)
        origin_node_ind = kwargs.get("origin_node_ind",
                                     self.allOriginNodeIndices)
        destination_node_ind = kwargs.get("destination_node_ind",
                                          self.allDestinationNodeIndices)
        vehicle_IDs = kwargs.get("vehicle_IDs", self.allVehicleIDs)

        indyRouter = CooperativeSearch(adjacency_matrix, origin_node_ind, 0)
        indyRouter.shortest()
        indyPaths = indyRouter.paths(destination_node_ind)
        edgesIndy = (self.nodeToEdge(adjacency_edge_id, indyPaths[trip])
                     for trip in xrange(len(vehicle_IDs)))
        return dict(zip(vehicle_IDs, edgesIndy))

    def routes(self, coop_share, penalty):
        """ Mixed cooperation routes.

        Args:
            coop_share (float): share of cooperative users
            penalty (float): penalization for visiting the same edges in case
                of cooperative routing

        Returns:
            dict: keys are vehicle ID's, and edgeID's
        """
        if coop_share == 1:
            return self.cooperativeRoutes(penalty)
        if coop_share == 0:
            return self.individualRoutes()
        # prepare indices that will cooperate and the ones that wont
        len_vehIDs = len(self.allVehicleIDs)
        coop_num = int(round(len_vehIDs * coop_share))
        coop_ind = []
        tmp_end = len_vehIDs - 1
        while len(coop_ind) != coop_num:
            num = random.randint(0, tmp_end)
            if num not in coop_ind:
                coop_ind.append(num)

        # TODO: transform this into normal for loop
        non_coop_IDs = [val for ind, val in enumerate(self.allVehicleIDs) if
                        ind not in coop_ind]
        coop_IDs = [self.allVehicleIDs[x] for x in coop_ind]

        non_coop_origins = [val for ind, val in enumerate(self.allOriginNodeIndices)
                            if ind not in coop_ind]
        coop_origins = [self.allOriginNodeIndices[x] for x in coop_ind]

        non_coop_destinations = [val for ind, val in enumerate(self.allDestinationNodeIndices)
                                 if ind not in coop_ind]
        coop_destinations = [self.allDestinationNodeIndices[x] for x in coop_ind]

        coop_routes = self.cooperativeRoutes(
            penalty, origin_node_ind=coop_origins,
            destination_node_ind=coop_destinations,
            vehicle_IDs=coop_IDs)

        non_coop_routes = self.individualRoutes(
            origin_node_ind=non_coop_origins,
            destination_node_ind=non_coop_destinations,
            vehicle_IDs=non_coop_IDs)

        routes = {}
        routes.update(coop_routes)
        routes.update(non_coop_routes)
        return routes

