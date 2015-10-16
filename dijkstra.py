#!usr/bin/env python3
from __future__ import print_function

def neighbours(output, bool_list, *args):
    minimum = 4242

    for i in range(len(output)):
        if bool_list[i] == False and output[i] <= minimum:
            minimum = output[i]
            min_index = i
    return min_index

def shortest(graph, start, cars = [], *args):
    """
    calculate shortest path from multiple users at once
    pass in the vehicle objects
    graph is a  NxN matrix i.e. graph = [[1,2],[3,4]]
    """
    output = []
    path = []
    bool_list = []

    #prepare the output and bool_list starting conditions
    for i in range(len(graph)):
        output.append(4242) # maximum distance xD
        bool_list.append(False)
        path.append(-1)

    output[start] = 0 # distance from starting point is always 0
    for i in range(len(graph)-1):
        # first car ... 
        min_dist = neighbours(output, bool_list)
        bool_list[min_dist] = True

        for j in range(len(graph)):
            if (not bool_list[j]) and graph[min_dist][j] \
                    and output[min_dist] != 4242 \
                    and output[min_dist] + graph[min_dist][j] < output[j]:
                        output[j] = output[min_dist] + graph[min_dist][j]
                        path[j] = min_dist # from here reconstruct the path
                        # gives the parent of a node
                        #change edge weights!!
                        graph[min_dist][j] = graph[min_dist][j]*2

    print(output)
    print(path)
    return output, path

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
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0],\
            ]

shortest(graph, 7)
