#!usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: CooperativeSearch.py
Author: Aleksandar Trifunovic
Email: firtek.ex@gmail.com
Github: https://github.com/akstrfn
Description: Cooperatively searhing space
"""

from __future__ import print_function
from sys import maxsize  # faster like this then like sys.maxsize 40ns vs 17ns

try:
    xrange
except NameError:
    xrange = range
try:
    import itertools.imap as map
    import itertools.izip as zip
except ImportError:
    pass

class CooperativeSearch(object):

    def __init__(self, graph, agents, penalty=0.2):
        """
        A class to hold necessary data and functions for cooperative searching
        on a graph, where graph is represented as an weighted adjacency matrix.

        Args:
            graph (2d list):
            agents (int list): Starting positions of agents
            penalty (float): How many times to increase the cost of traversing
            the edge for other agents.

        """
        self.graph = graph
        self.agents = agents
        self.penalty = penalty
        for agent in self.agents:
            assert agent < len(self.graph), \
                "Starting position of a car can not be outside of the graph"
        # cheaper than deepcopy and it works for this case, simple copy
        # doesn't work
        self.dynamic_graph = [g[:] for g in self.graph]
        self.output_lst = []  # distance to every node from the starting node
        self.path_lst = []    # paths to every node
        self.bool_lst = []    # visited nodes

        # history necessary for drivers to know which nodes they have increased
        self.history = []

        # prepare necessary containers
        for dummy in xrange(len(self.agents)):
            self.output_lst.append([])
            self.path_lst.append([])
            self.bool_lst.append([])
            self.history.append([])

        # prepare the output_list and bool_list starting conditions
        for agent in xrange(len(self.agents)):
            for elem in xrange(len(self.graph)):
                self.output_lst[agent].append(maxsize)  # max distance
                self.path_lst[agent].append("entry")
                self.bool_lst[agent].append(False)
                if elem == self.agents[agent]:
                    self.output_lst[agent][elem] = 0
                    self.path_lst[agent][elem] = "start"

    def shortest(self):
        """
        Calculate cooperational paths for multiple users. This is a wrapper for
        the class.

        Returns:
            A list of lists with shortest paths to all other nodes from
            starting node.
        """
        len_to_check = len(self.graph) - 1
        num_of_steps = len(self.agents)
        while len_to_check != 0:
            car = 0
            while car != num_of_steps:
                self._inner(car)
                # self.dijkstra_inner(car)
                car += 1
            len_to_check -= 1

    def _inner(self, car_index):
        """
        Helper method that traverses one row of adjacency matrix for one agent
        and increases the cost of nodes that were checked i.e. modifies the
        dynamic adjacency matrix. It is derived from Dijkstra's shortest path
        algorithm.
        """
        output = self.output_lst[car_index]
        bool_list = self.bool_lst[car_index]
        path = self.path_lst[car_index]
        min_index = self._neighbors(output, bool_list)
        bool_list[min_index] = True

        temp = None  # dont change the graph all the time
        for node in xrange(len(self.graph)):
            if (not bool_list[node]) \
                and self.dynamic_graph[min_index][node] \
                and output[min_index] != maxsize \
                and output[min_index] + self.dynamic_graph[min_index][node] < output[node]:
                    output[node] = output[min_index] + self.dynamic_graph[min_index][node]
                    path[node] = min_index
                    temp = node
            # MAGIC happens here... Increasing the node cost basically until
            # the next node that satisfies requested conditions is reached and
            # then that node gets increased.
            if temp:
                self.dynamic_graph[min_index][temp] += self.graph[min_index][temp] * self.penalty
                self.dynamic_graph[temp][min_index] += self.graph[temp][min_index] * self.penalty

    def dijkstra_inner(self, car_index):
        """
        Helper method that traverses one row of adjacency matrix for one agent
        and increases the cost of nodes that were checked i.e. modifies the
        dynamic adjacency matrix. It is derived from Dijkstra's shortest path
        algorithm.
        """
        # TODO one loop could be added to add additional corrections of choosen
        # paths hence one could optimize that loop locally
        # TODO make this into separate class
        output = self.output_lst[car_index]
        bool_list = self.bool_lst[car_index]
        path = self.path_lst[car_index]
        min_index = self._neighbors(output, bool_list)
        bool_list[min_index] = True

        # Modify dynamic driver graph with the knowledge of which edges has the
        # driver penalized before i.e. revealing the 'real' cost of and edge
        driver_graph = [x[:] for x in self.dynamic_graph]
        history = self.history[car_index]
        for position in history:
            driver_graph[position[0]][position[1]] -= \
                self.graph[position[0]][position[1]] * self.penalty

        temp_l = []
        for node in xrange(len(self.graph)):
            if ((not bool_list[node]) \
                and driver_graph[min_index][node] \
                and output[min_index] != maxsize \
                and output[min_index] + driver_graph[min_index][node] <
                output[node]):
                    output[node] = (output[min_index] +
                                    driver_graph[min_index][node])
                    path[node] = min_index
                    temp_l.append(node)

        if temp_l:
            # Get min cost node that would be traversed
            _, temp = min(((output[x], x) for x in temp_l),
                          key=lambda p: p[0])

            # Penalize both directions
            self.dynamic_graph[min_index][temp] += \
                self.graph[min_index][temp] * self.penalty
            self.dynamic_graph[temp][min_index] += \
                self.graph[temp][min_index] * self.penalty

            # Add memory to car in both direction
            history.append((min_index, temp))
            history.append((temp, min_index))

    def _neighbors(self, output, bool_list):
        """
        Helper method to get the closest neighbor based on two criteria.
        """
        minimum = maxsize
        for ind, bool in enumerate(bool_list):
            if not bool and output[ind] <= minimum:
                minimum = output[ind]
                min_index = ind
        return min_index

    @staticmethod
    def reconstruct_path(path, destination, start=None):
        """
        Reconstruct a path from closes neighbourhood list.

        Args:
            path (list): list with integers and optional string where every
            value is pointing to a previous in path i.e. path[0] gives a
            closest node to node 0.
            destination (int): the destination node
            start (int): which node is the starting node
        Returns:
            list.

        >>> reconstruct_path(['start', 9, 6, 0, 2, 6, 8, 0, 7, 0, 14, 15, 13, \
            8, 7, 9], 8)
        [0, 7, 8]
        >>> reconstruct_path([3, 7, 6, -1, 2, 10, 5, 14, 10, 0, 14, 1, 11, 8, \
                3, 9], 14, start=3)
        [3, 14]
        """
        if start is None:
            start = path.index("start")
        sol = [destination]
        while sol[-1] != start:
            destination = path[destination]
            sol.append(destination)
        return sol[::-1]

    def paths(self, destinations):
        """
        Return reconstructed shortest paths.
        """
        paths = list(map(self.reconstruct_path, self.path_lst, destinations))
        return paths

class CoopSearchHillOptimized(CooperativeSearch):

    def __init__(self, graph, agents, destinations, penalty):
        super(CoopSearchHillOptimized, self).__init__(graph, agents, penalty)
        self.destinations = destinations

    def optimized(self):
        from hill_climb import hill
        # this thing with dest[ind] works when you pass dest as an argument
        # i.e. CoopSearchHillOptimized(graph_ort, cars, dest, 0.2).optimized()
        # now that is crazy
        #return hill([self.reconstruct_path(path, dest[ind]) for ind, path in
        #             enumerate(self.shortest())], self.graph)
        #
        # shortest() must be called first
        routes = list(map(self.reconstruct_path,
                          self.path_lst,
                          self.destinations,
                          self.agents))
        return hill(routes, self.graph)


if __name__ == "__main__":
    # TODO add proper tests

    graph = [[0, 4, 0, 0, 0, 0, 0, 8, 0],
             [4, 0, 8, 0, 0, 0, 0, 11, 0],
             [0, 8, 0, 7, 0, 4, 0, 0, 2],
             [0, 0, 7, 0, 9, 14, 0, 0, 0],
             [0, 0, 0, 9, 0, 10, 0, 0, 0],
             [0, 0, 4, 0, 10, 0, 2, 0, 0],
             [0, 0, 0, 14, 0, 2, 0, 1, 6],
             [8, 11, 0, 0, 0, 0, 1, 0, 7],
             [0, 0, 2, 0, 0, 0, 6, 7, 0]]

    graph_ort_man = [[0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                     [1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                     [0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                     [0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0],
                     [0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0],
                     [0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0],
                     [0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0],
                     [0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0],
                     [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1],
                     [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0]]

    graph_ort = [[0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0],
                 [0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0],
                 [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
                 [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0],
                 [0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                 [1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0],
                 [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0],
                 [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                 [0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0],
                 [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
                 [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0],
                 [0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
                 [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0]]


    gg_bug = [[0, 90.5, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [90.5, 0, 90.5, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 90.5, 0, 90.5, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 90.5, 0, 90.5, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 90.5, 0, 90.5, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 90.5, 0, 0, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [65.5, 0, 0, 0, 0, 0, 0, 90.5, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 65.5, 0, 0, 0, 0, 90.5, 0, 90.5, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 65.5, 0, 0, 0, 0, 90.5, 0, 90.5, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 65.5, 0, 0, 0, 0, 90.5, 0, 90.5, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 65.5, 0, 0, 0, 0, 90.5, 0, 90.5, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 90.5, 0, 0, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 0, 0, 90.5, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 90.5, 0, 90.5, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 90.5, 0, 90.5, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 90.5, 0, 90.5, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 90.5, 0, 90.5, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 90.5, 0, 0, 0, 0, 0, 0, 65.5, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 0, 0, 90.5, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 90.5, 0, 90.5, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 90.5, 0, 90.5, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 90.5, 0, 90.5, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 90.5, 0, 90.5, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 65.5, 0, 0, 0, 0, 90.5, 0, 0, 0, 0, 0],
              [8.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 8.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8.0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8.0, 0, 0, 0, 0]]

    # import random
    # cars = [0, 3, 11, 12, 5]
    cars = [25, 25, 25, 25, 25]
    # for i in xrange(5):
    #     cars.append(random.choice([0,1,2,3,4,7,8,11,12,13,14,15]))
    obj = CooperativeSearch(gg_bug, cars)
    sh = obj.shortest()
    # dest = [8,4,5,1]
    # dest = [15, 15, 15, 15, 15]
    dest = [12, 12, 12, 12, 12]
    another = CooperativeSearch(gg_bug, cars).paths(dest)

    h_obj = CoopSearchHillOptimized(gg_bug, cars, dest, 0.2).optimized()
    for i in xrange(len(cars)):
        print("Dijkstra")
        print(obj.reconstruct_path(sh[i], dest[i]))
        print(another[i])
        print("Optimized")
        print(h_obj[i])
    # some testing with networkx
    # import networkx as nx
    # import numpy as np
    # import matplotlib.pyplot as plt
    # adj_matrix = np.matrix(graph_ort_man)
    # adj_matrix = np.matrix(gg_bug)
    # G = nx.from_numpy_matrix(adj_matrix)
    # pos=nx.spring_layout(G, iterations=200)
    # nx.draw(G, pos, with_labels=True)
    # plt.show()
