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
import sys

try:
    xrange
except NameError:
    xrange = range

class CooperativeSearch(object):


    def __init__(self, graph, agents, penalty=0.2):
        """
        A class to hold necessary data and functions for cooperative searching on
        a graph, where graph is represented as an weighted adjacency matrix.
        
        Args:
            graph (2d list):
            agents (int list): Starting positions of agents
            penalty (float): How many times to increase the cost of traversing the
            edge for other agents.

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
        for dummy in range(len(self.agents)):
            self.output_lst.append([])
            self.path_lst.append([])
            self.bool_lst.append([])
            self.history.append([])

        # prepare the output_list and bool_list starting conditions
        for agent in range(len(self.agents)):
            for elem in range(len(self.graph)):
                self.output_lst[agent].append(sys.maxsize)  # max distance
                self.path_lst[agent].append("start")
                self.bool_lst[agent].append(False)
                if elem == self.agents[agent]:
                    self.output_lst[agent][elem] = 0

    def shortest(self):
        """
        Calculate cooperational paths for multiple users. This is a wrapper for
        the class.
        """
        len_to_check = len(self.graph) - 1
        num_of_steps = len(self.agents)
        while len_to_check != 0:
            car = 0
            while car != num_of_steps:
                # self._inner(car)
                self.dijkstra_inner(car)
                car += 1
            len_to_check -= 1

        return self.path_lst

    def _inner(self, car_index):
        """
        Helper method that traverses one row of adjacency matrix for one agent
        and increases the cost of nodes that were checked i.e. modifies the
        dynamic adjacency matrix. It is derived from Dijkstra's shortest path
        algorithm.
        """
        # TODO do not copy lists
        output = self.output_lst[car_index]
        bool_list = self.bool_lst[car_index]
        path = self.path_lst[car_index]
        max_size = sys.maxsize
        min_index = self._neighbors(output, bool_list)
        bool_list[min_index] = True

        temp = None  # dont change the graph all the time
        for node in range(len(self.graph)):
            if (not bool_list[node]) \
                and self.dynamic_graph[min_index][node] \
                and output[min_index] != max_size \
                and output[min_index] + self.dynamic_graph[min_index][node] < output[node]:
                    output[node] = output[min_index] + self.dynamic_graph[min_index][node]
                    path[node] = min_index
                    temp = node
            # TODO the bug is here (it increases the cost all the time)...
            # lets try the case when it increases the cost on all edges by
            # puting temp = None after penalty increasement? or maybe
            # increasement should be in proportion to the lenght of the edge
            # i.e. long edges get penalized less??
            if temp:
                self.dynamic_graph[min_index][temp] += \
                        self.graph[min_index][temp] * self.penalty
                self.dynamic_graph[temp][min_index] += \
                        self.graph[temp][min_index] * self.penalty
                #temp = None # this was missing from the first version... why?

    def dijkstra_inner(self, car_index):
        """
        Helper method that traverses one row of adjacency matrix for one agent
        and increases the cost of nodes that were checked i.e. modifies the
        dynamic adjacency matrix. It is derived from Dijkstra's shortest path
        algorithm.
        """
        # TODO do not copy lists
        output = self.output_lst[car_index]
        bool_list = self.bool_lst[car_index]
        path = self.path_lst[car_index]
        max_size = sys.maxsize
        min_index = self._neighbors(output, bool_list)
        bool_list[min_index] = True

        driver_graph = [x[:] for x in self.dynamic_graph]
        history = self.history[car_index]
        for position in history:
            driver_graph[position[0]][position[1]] -= \
                self.graph[position[0]][position[1]] * self.penalty

        temp_l = []
        for node in range(len(self.graph)):
            if ((not bool_list[node]) \
                and driver_graph[min_index][node] \
                and output[min_index] != max_size \
                and output[min_index] + driver_graph[min_index][node] <
                output[node]):
                    output[node] = (output[min_index] +
                                    driver_graph[min_index][node])
                    path[node] = min_index
                    temp_l.append(node)

        if temp_l:
            # Get min cost node that would be traversed
            _, temp = min(((output[x], x) for x in temp_l[::-1]),
                          key=lambda p: p[0])

            # Penalize
            self.dynamic_graph[min_index][temp] += \
                self.graph[min_index][temp] * self.penalty
            self.dynamic_graph[temp][min_index] += \
                self.graph[temp][min_index] * self.penalty

            # Add memory to car
            history.append((min_index, temp))
            history.append((temp, min_index))

    def _neighbors(self, output, bool_list):
        """
        Helper method to get the closest neighbor based on two criteria.
        """
        minimum = sys.maxsize
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

    import random
    cars = []
    cars = [0,3,11,12]
    
    #for i in range(5):
    #    cars.append(random.choice([0,1,2,3,4,7,8,11,12,13,14,15]))
    obj = CooperativeSearch(graph_ort_man, cars)
    sh = obj.shortest()
    dest = [8,14,5,1]

    for i in range(len(cars)):
        #dest = random.randint(0,15)
        #print(sh[i])
        print(obj.reconstruct_path(sh[i], dest[i]))
        
    # some testing with networkx
    import networkx as nx
    import numpy as np
    import matplotlib.pyplot as plt
    adj_matrix = np.matrix(graph_ort_man)
    G = nx.from_numpy_matrix(adj_matrix)
    pos=nx.spring_layout(G, iterations=200)
    nx.draw(G, pos, with_labels=True)
    plt.show()
