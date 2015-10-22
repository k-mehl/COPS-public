#!usr/bin/env python3
from __future__ import print_function

def reconstruct_path(path):
    """
    Reconstruct all paths pairs i.e. if start = 0 and number of nodes is 4
    it will output paths: 0-0; 0-1; 0-2; 0-3.
    """
    start = path.index("start")
    destination = 0
    num_of_destinations = len(path)
    temp_path = []
    while destination != num_of_destinations:
        temp_dest = destination
        temp_path.append(destination)
        while start != temp_dest:
            temp_dest = path[temp_dest]
            temp_path.append(temp_dest)
        print("From", start, "to", destination, ":", temp_path[::-1])
        temp_path = []
        destination +=1

def neighbors(output, bool_list, *args):
    """ Get the closest neighbor """
    # inefficient since it raises the complexity to O(V^3)
    minimum = 424242
    # use python collections or lambda with min function and benchmark all 
    # solutions
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
    max_size = 424242
    min_dist = neighbors(output, bool_list)
    bool_list[min_dist] = True

    temp = None # dont change the graph all the time
    for node in range(len(graph)):
        if (not bool_list[node]) and graph[min_dist][node] \
                and output[min_dist] != max_size \
                and output[min_dist] + graph[min_dist][node] < output[node]:
                    output[node] = output[min_dist] + graph[min_dist][node]
                    # set the parent
                    path[node] = min_dist
                    # remember only the last traversed node and increase the cost
                    # not the proper way to construct this but it is the same
                    # in principle
                    temp = node
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
    max_size = 424242
    # cars contains starting positions in a graph
    output_lst = []
    path_lst = []
    bool_lst = []
    for i in range(len(cars)):
        output_lst.append([])
        path_lst.append([])
        bool_lst.append([])

    #prepare the output_list and bool_list starting conditions
    for car in range(len(cars)):
        for elem in range(len(graph)):
            output_lst[car].append(max_size)
            path_lst[car].append("start")
            bool_lst[car].append(False)
            if elem == cars[car]:
                output_lst[car][elem] = 0

    len_to_check = len(graph) - 1
    while len_to_check != 0:
        # Check step-wise for every car
        num_of_steps = len(cars)
        step = 0
        while step != num_of_steps:
            graph, output_lst[step], bool_lst[step], path_lst[step] = inner(graph, output_lst[step], bool_lst[step], path_lst[step])
            step += 1
        len_to_check -= 1

#    print("Shortest paths lengths from chosen starting point:")
#    for dum in output_lst:
#        print(dum)
#    print("Path lists for all the agents:")
#    for dum_ag in path_lst:
#        print(dum_ag)
    return path_lst

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

    first = shortest(graph)
    print("reconstruct path for:", first[0])
    reconstruct_path(first[0])

    shortest(graph_ort, [0, 12])
else:
    print("Imported of social dijkstra alg")
