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
import copy

class CooperativeSearch(object):

    def __init__(self, graph, agents, penalty = 0.2):
        """
        A class to hold necessary data and functions for cooperative searching on
        a graph, where graph is represented as an weighted adjacency matrix.
        
        Args:
            graph (2d list): 
            agents (int list): Starting positions of agents
        Kwargs:
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
        self.output_lst = [] # distance to every node from the starting node
        self.path_lst = [] # paths to every node
        self.bool_lst = [] # visited nodes

        # prepare necessary containers
        for dummy in range(len(self.agents)):
            self.output_lst.append([])
            self.path_lst.append([])
            self.bool_lst.append([])

        #prepare the output_list and bool_list starting conditions
        for agent in range(len(self.agents)):
            for elem in range(len(self.graph)):
                self.output_lst[agent].append(sys.maxsize) # max distance
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
                self._inner(car)
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
        #TODO do not copy lists
        output = self.output_lst[car_index]
        bool_list = self.bool_lst[car_index]
        path = self.path_lst[car_index]
        max_size = sys.maxsize
        min_dist = self._neighbors(output, bool_list) 
        bool_list[min_dist] = True

        temp = None # dont change the graph all the time
        for node in range(len(self.graph)):
            if (not bool_list[node]) \
                and self.dynamic_graph[min_dist][node] \
                and output[min_dist] != max_size \
                and output[min_dist] + self.dynamic_graph[min_dist][node] < output[node]:
                    output[node] = output[min_dist] + self.dynamic_graph[min_dist][node]
                    path[node] = min_dist
                    temp = node
            #TODO the bug is here (it increases the cost all the time)...
            # lets try the case when it increases the cost on all edges by
            # puting temp = None after penalty increasement? or maybe
            # increasement should be in proportion to the lenght of the edge
            # i.e. long edges get penalized less??
            if temp:
                self.dynamic_graph[min_dist][temp] += \
                        self.graph[min_dist][temp] * self.penalty
                self.dynamic_graph[temp][min_dist] += \
                        self.graph[temp][min_dist] * self.penalty
                #temp = None # this was missing from the first version... why?

    def _OLD_inner(graph_original, graph, output, bool_list, path, history, penalty = 1):
        """ 
        !!!DO NOT USE THIS!!!
        This is old inner loop with some ideas on how to improve algorithm were it
        is implemented increasement only to the smallest cost edge, but still not
        good enough because it lacks histrical knowledge (maybe)
        """
        #TODO improve algorithm
        max_size = sys.maxsize
        min_dist = neighbors(output, bool_list)
        bool_list[min_dist] = True

        #drivers_graph = [x[:] for x in graph]
        #for position in history:
        #    drivers_graph[position[0]][position[1]] -= graph_original[position[0]][position[1]] * penalty

        temp_l = []
        temp = None 
        for node in range(len(graph)):
            if (not bool_list[node]) and graph[min_dist][node] \
                and output[min_dist] != max_size \
                and output[min_dist] + graph[min_dist][node] < output[node]: #and output[min_dist] + drivers_graph[min_dist][node] < output[node]:
                    #output[node] = output[min_dist] + graph[min_dist][node]
                    output[node] = output[min_dist] + graph[min_dist][node]
                    # set the parent
                    path[node] = min_dist
                    # remember only the last traversed node and increase the
                    # cost later
                    temp = node
                    temp_l.append(temp)
            # this version is weird but it works.... it increases the cost for a
            # node many times as there are nodes.... donno why this works!!!
            #if temp:
            #    graph[min_dist][temp] += graph_original[min_dist][temp] * penalty

        #this version to be used only to increase the node with smallest cost... i
        #need to figure this one in more details
        min_val = sys.maxsize
        for i in temp_l[::-1]:
            if output[i] < min_val:
                min_val = output[i]
                temp = i
        # increases the value on all traversed nodes... this is very tricky
        if temp:
            graph[min_dist][temp] += graph_original[min_dist][temp] * penalty
            #history.append((min_dist, temp))
        #graph[min_dist][temp] = round(graph[min_dist][temp], 1)

        #print(temp_l)
        #print(output)
        #print(path)
        #print([output[i] for i in temp_l])
        return graph, output, bool_list, path, history

    def _neighbors(self, output, bool_list):
        """ 
        Helper method to get the closest neighbor based on two criteria.
        """
        #TODO inefficient since it raises the complexity to O(V^3)
        minimum = sys.maxsize
        for i in range(len(output)):
            if bool_list[i] == False and output[i] <= minimum:
                minimum = output[i]
                min_index = i
        return min_index

    @staticmethod
    def reconstruct_path(path, destination, start=None):
        """
        Reconstruct a path from closes neighbourhood list.

        Args:
            path (list): list with integers and optional string where every
            value is pointing to a previous in path i.e. path[0] gives a closest
            node to node 0.
            destination (int): the destination node
        Kwargs:
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
        if start == None:
            start = path.index("start")
        sol = [destination]
        while sol[-1] != start:
            destination = path[destination]
            sol.append(destination)
        return sol[::-1]



if __name__ == "__main__":
    # TODO add proper tests

    graph = [[0, 4, 0, 0, 0, 0, 0, 8, 0],\
            [4, 0, 8, 0, 0, 0, 0, 11, 0],\
            [0, 8, 0, 7, 0, 4, 0, 0, 2],\
            [0, 0, 7, 0, 9, 14, 0, 0, 0],\
            [0, 0, 0, 9, 0, 10, 0, 0, 0],\
            [0, 0, 4, 0, 10, 0, 2, 0, 0],\
            [0, 0, 0, 14, 0, 2, 0, 1, 6],\
            [8, 11, 0, 0, 0, 0, 1, 0, 7],\
            [0, 0, 2, 0, 0, 0, 6, 7, 0]] 

    graph_ort = [\
                [0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],\
                [1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],\
                [0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],\
                [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],\
                [1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],\
                [0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0],\
                [0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0],\
                [0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0],\
                [0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0],\
                [0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0],\
                [0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0],\
                [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1],\
                [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0],\
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0],\
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1],\
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0]]

    graph_ort =[[0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0],\
                [0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0],\
                [0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0],\
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],\
                [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],\
                [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0],\
                [0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],\
                [1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0],\
                [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0],\
                [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],\
                [0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0],\
                [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],\
                [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0],\
                [0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],\
                [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0],\
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0]] 

    import random
    cars = []
    cars = [0,3,11,12]
    
    #for i in range(5):
    #    cars.append(random.choice([0,1,2,3,4,7,8,11,12,13,14,15]))
    obj = CooperativeSearch(graph_ort, cars)
    sh = obj.shortest()
    dest = [8,14,5,1]

    for i in range(len(cars)):
        #dest = random.randint(0,15)
        #print(sh[i])
        print(obj.reconstruct_path(sh[i], dest[i]))
        
    # some testing with networkx
    #import networkx as nx
    #import numpy as np
    #import matplotlib.pyplot as plt
    #adj_matrix = np.matrix(graph_ort)
    #G = nx.from_numpy_matrix(adj_matrix)
    #pos=nx.spring_layout(G, iterations=200)
    #nx.draw(G, pos, with_labels=True)
    #plt.show()
