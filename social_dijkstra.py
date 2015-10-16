#!usr/bin/env python3
from __future__ import print_function

def neighbors(output, bool_list, *args):
    """ Get the closest neighbor """
    # inefficient since it raises the complexity to O(V^3)
    minimum = 424242

    for i in range(len(output)):
        if bool_list[i] == False and output[i] <= minimum:
            minimum = output[i]
            min_index = i
    return min_index

def inner(graph, output, bool_list, path, penalty = 2):
    """ Calculates:
            1. shortest route distance and save it in output, 
            2. saves last visited node before reaching desired node in path
            3. modifies underlying graph structure each time it passes
    """
    #TODO the edge that is penalized should be the shortest one, not the last one
    #TODO proper returning and printing
    #TODO reconstruct path automatically from path list
    min_dist = neighbors(output, bool_list)
    bool_list[min_dist] = True

    temp = None # dont change the graph all the time
    for j in range(len(graph)):
        if (not bool_list[j]) and graph[min_dist][j] \
                and output[min_dist] != 424242 \
                and output[min_dist] + graph[min_dist][j] < output[j]:
                    output[j] = output[min_dist] + graph[min_dist][j]
                    # set the parent
                    path[j] = min_dist
                    # remember only the last traversed node and increase the cost
                    # not the proper way to construct this but it is the same
                    # in principle
                    temp = j
        if temp:
            # penalty increases exponentially, probably not so good
            graph[min_dist][temp] = graph[min_dist][temp] * penalty

    return graph, output, bool_list, path

def shortest(graph, cars = [0,0,0], *args):
    """
    Calculate shortest path from multiple users at once
    Graph is a NxN adjacent (weighted) matrix i.e. graph = [[0,1],[1,0]]
    cars container has starting nodes as integers for each car i.e.
    cars[0] is the starting position for first car, cars[1] for second and so
    on. 
    """
    # cars contains starting positions in a graph
    output_lst = []
    path_lst = []
    bool_lst = []
    for i in range(len(cars)):
        output_lst.append([])
        path_lst.append([])
        bool_lst.append([])

    #prepare the output and bool_list starting conditions
    for car in range(len(cars)):
        for elem in range(len(graph)):
            output_lst[car].append(424242)
            path_lst[car].append(-1)
            bool_lst[car].append(False)
            if elem == cars[car]:
                output_lst[car][elem] = 0


    for i in range(len(graph)-1):
        # recursive function?
        for blah in range(len(cars)):
            graph, output_lst[blah], bool_lst[blah], path_lst[blah] = inner(graph, output_lst[blah], bool_lst[blah], path_lst[blah])

    print(list(range(len(graph))))
    for dum in output_lst:
        print(dum)
    for dum_ag in path_lst:
        print(dum_ag)

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
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0],\
                ]

    shortest(graph)
    shortest(graph_ort, [0, 12])
else:
    print("Imported of social dijkstra alg")
