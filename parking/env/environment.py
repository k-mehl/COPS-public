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

from parking.env.parkingSpace import ParkingSpace


class Environment(object):
    """ Environment class """

    def __init__(self, p_config):
        # initialization just creates a network representation: no vehicles or parking spaces!
        self._config = p_config
        self._destination_edges = []
        self._origin_edges = []
        self._exit_edges = []

        resource_dir = self._config.getCfg("simulation").get("resourcedir")
        reroute_nodes = os.path.join(resource_dir, 'reroute.nod.xml')  # creates path to node.xml file
        reroute_edges = os.path.join(resource_dir, 'reroute.edg.xml')  # creates path to edge.xml file

        self._nodes = [str(x.id) for x in
                       sumolib.output.parse(reroute_nodes, ['node'])]  # create array with all nodes IDs from file
        self._edges = [str(x.id) for x in
                       sumolib.output.parse(reroute_edges, ['edge'])]  # create array with all edges IDs from file

        # TODO: make a proper object from this and then finish refactoring this
        # class
        self._roadNetwork = {"nodes": {node: {} for node in self._nodes},
                             "edges": {edge: {} for edge in self._edges}}  # create dictionary for edges and nodes
        # "edges" : {"edge_id" : {} , ...}, "nodes:" : {"node_id": {}}

        reroute_network = os.path.join(resource_dir, 'reroute.net.xml')  # path to net.xml
        self._net = sumolib.net.readNet(
            reroute_network)  # parses the net (generated network -> representation of shapes)

        # temporary functions to get id of nodes from edge
        def edg_to_id(edge):
            return self._net.getEdge(edge).getToNode().getID()

        def edg_from_id(edge):
            return self._net.getEdge(edge).getFromNode().getID()

        # create and fill adjacency matrices
        num_nodes = len(self._nodes)
        # creates (empty) matrix with mat[num_nodes x num_nodes]:
        self._adjacencyMatrix = [[0] * num_nodes for _ in xrange(num_nodes)]
        self._adjacencyEdgeID = [[""] * num_nodes for _ in xrange(num_nodes)]

        # converts generator xrange to list - mult with 2 = iterate list like nested for loop for i and j
        for i, j in itertools.product(*[xrange(num_nodes)] * 2):
            from_id = self._nodes[i]
            to_id = self._nodes[j]
            for edge in self._edges:
                if edg_from_id(edge) == from_id and edg_to_id(edge) == to_id:
                    e = self._net.getEdge(edge)
                    self._adjacencyMatrix[i][j] = e.getLength()
                    self._adjacencyEdgeID[i][j] = str(e.getID())

        self._oppositeEdgeID = dict(filter(  # filter selects values of dictionary based on lambda fct
            lambda x: (edg_to_id(x[0]) == edg_from_id(x[1])
                       and edg_from_id(x[0]) == edg_to_id(x[1])),  # logical statement, end lambda
            itertools.permutations(self._edges,
                                   2)))  # list to iterate. permutations is the permutation for 2 elements in _edges

        for node in self._nodes:
            self._roadNetwork["nodes"][node]["coordinates"] = self._net.getNode(node).getCoord()

        for edge in self._edges:
            # e is a reference to the road network. all changes and asignment will be saved
            e = self._roadNetwork["edges"][edge]
            e["length"] = self._net.getEdge(edge).getLength()
            e["fromNode"] = str(edg_from_id(edge))
            fromNodeCoord = self._roadNetwork["nodes"][e["fromNode"]]["coordinates"]
            e["toNode"] = str(edg_to_id(edge))
            toNodeCoord = self._roadNetwork["nodes"][e["toNode"]]["coordinates"]
            e["meanCoord"] = tuple(numpy.divide(numpy.add(fromNodeCoord, toNodeCoord), 2))
            e["succEdgeID"] = [str(x.getID())
                               for x in self._net.getEdge(
                    edge).getToNode().getOutgoing()]  # = 'toNode' from edge and get all outgoing edges from this node
            e["nodeDistanceFromEndNode"] = {}

            for node in self._nodes:
                # TODO: discuss the relevant distance measure
                # endNote synonym to toNote used to avoid confusion in variable names
                lineEndNodeToNode = numpy.subtract(e["meanCoord"], self._roadNetwork["nodes"][node]["coordinates"])
                # lineEndNodeToNode = numpy.subtract(toNodeCoord, self._roadNetwork["nodes"][node]["coordinates"])
                e["nodeDistanceFromEndNode"][node] = numpy.sqrt(numpy.sum(lineEndNodeToNode ** 2))

            e["selfVisitCount"] = {}
            e["visitCount"] = {}
            e["plannedCount"] = {}

            if edge in self._oppositeEdgeID:
                e["oppositeEdgeID"] = self._oppositeEdgeID[edge]
            else:
                e["oppositeEdgeID"] = []

        for edge in sumolib.output.parse(
                os.path.join(self._config.getCfg("simulation").get("resourcedir"), "reroute.edg.xml", ),
                ['edge']):
            # if the edge ID contains "entry": use it as origin only,
            # if entry-point is first node, else use it as exit node
            # otherwise: use it as destination only
            if "entry" in str(edge.id):
                if str(edge.id)[0].isdigit():
                    self._exit_edges.append(str(edge.id))
                else:
                    self._origin_edges.append(str(edge.id))
            else:
                self._destination_edges.append(str(edge.id))

    def loadParkingSpaces(self, p_run):
        """ Load parking spaces

        Args:
            p_run (int): run number
        """
        if self._config.getCfg("simulation").get("verbose"):
            print("* loading parking spaces from run cfg")
        self._parkingSpaceNumber = self._config.getCfg("simulation").get("parkingspaces").get("free")

        l_cfgparkingspaces = self._config.getRunCfg(str(p_run)).get("parkingspaces")
        self._allParkingSpaces = [ParkingSpace(v.get("name"),
                                  v.get("edgeID"),
                                  v.get("position"),
                                  available=v.get("available"))
                                 for v in l_cfgparkingspaces.values()]

        for edge in self._edges:
            self._roadNetwork["edges"][edge]["parkingSpaces"] = \
                    [p for p in self._allParkingSpaces if p.edgeID == edge]
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

    @property
    def nodes(self):
        return self._nodes

    @property
    def edges(self):
        return self._edges
