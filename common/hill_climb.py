#!usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function
from cooperativeSearch import CooperativeSearch
from itertools import chain
from random import randint, choice

try:
    xrange
except NameError:
    xrange = range

def count_overlap(driver_matrix):
    forward_edges = (zip(x, x[1:]) for x in driver_matrix)
    backward_edges = (zip(x[::-1], x[-2::-1]) for x in driver_matrix)
    edges = list(chain(*forward_edges, *backward_edges))
    return len(edges) - len(set(edges))

def num_of_visited_nodes(driver_matrix):
    return sum((len(x) for x in driver_matrix))

def total_cost(driver_matrix):
    return count_overlap(driver_matrix) + num_of_visited_nodes(driver_matrix)

def hill(driver_matrix, adjacency_matrix):
    # TODO normalize cost
    costs = [total_cost(driver_matrix)]

    def hill_runner(driver_matrix, adjacency_matrix):
        num_of_drivers = len(driver_matrix)
        cost = total_cost(driver_matrix)
        d = randint(0, num_of_drivers - 1)  # pick a random driver path
        # do not use paths that are to small i.e. smaller than 4
        while len(driver_matrix[d]) < 4:
            d = randint(0, num_of_drivers - 1)
        path = driver_matrix[d]
        #print("chosen path ", path)
        # pick a random node excluding first and the last (start and end)
        node_ind = randint(1, len(path) - 2)
        node = path[node_ind]
        #print("chosen node ", node)
        path_neighbors = (path[node_ind - 1],
                          path[node_ind + 1])
        # chose where to move (you can not move into neighbors already in path)
        neighbors = adjacency_matrix[node][:]
        #print(neighbors)
        move_to = [x for x in enumerate(neighbors) if x[1] != 0 and x[0] not in
                   path_neighbors]
        if not move_to:
            # you are in the corner, so no change
            return driver_matrix
        move_to = choice(move_to)[0]
        #print("move to: ", move_to)
        # get the shortest route to connecting nodes
        # TODO left and right will go out of bounds if node_ind is next to
        # start and end nodes in path
        if node_ind - 1 == 0:
            left_ind = 0
        else:
            left_ind = node_ind - 2

        if node_ind + 1 == (len(path) - 1):
            righ_ind = len(path) - 1
        else:
            righ_ind = node_ind + 2

        left = path[left_ind]
        right = path[righ_ind]

        #print(left, right)
        new_routes = CooperativeSearch(adjacency_matrix, [move_to], 0).shortest()
        left_path = CooperativeSearch.reconstruct_path(new_routes[0], left)
        right_path = CooperativeSearch.reconstruct_path(new_routes[0], right)
        #print("lp", left_path)
        #print("rp", right_path)
        
        new_path = path[:left_ind] + left_path[::-1] + right_path[1:-1] + path[righ_ind:]
        #print("And the path is: ", new_path)

        # some stupid cases where edge gets duplicated discard such cases... in
        # this situation 2 cases should be checked:
        # left path routed without the node that got repeated twice
        # right path router without the node that got repeated twice
        # and then better option should be chosen
        # in any case cycles are out of question here
        if len(new_path) - len(set(new_path)):
            # TODO: improve this case because there might be some benefitical
            # cases here to avoid local optima catch
            return driver_matrix

        # Check if cost is improved and modify the routes if yes
        temp_matrix = [x[:] for x in driver_matrix]
        temp_matrix[d] = new_path
        new_cost = total_cost(temp_matrix)
        if new_cost < cost:
            return temp_matrix

        return driver_matrix



    # Run 1000 times
    # TODO smarter deceision on number of runs
    for i in xrange(1000):
        driver_matrix = hill_runner(driver_matrix, adjacency_matrix)
        costs.append(count_overlap(driver_matrix) + num_of_visited_nodes(driver_matrix))
        #if len(costs) > 100 and len(set(costs[-100:])) == 1:
        #    return driver_matrix
    return driver_matrix


if __name__ == "__main__":
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

    cars = [0, 3, 11, 12, 5]
    #cars = [5, 5, 5, 5, 5]

    obj = CooperativeSearch(graph_ort, cars)
    sh = obj.shortest()
    dest = [15, 15, 15, 15, 15]
    dest = [6, 4, 5, 14, 0]

    recon = []
    for i in xrange(len(cars)):
        recon.append(obj.reconstruct_path(sh[i], dest[i]))
        print(obj.reconstruct_path(sh[i], dest[i]))

    print("num_of_visited_nodes", num_of_visited_nodes(recon))
    print("overlap", count_overlap(recon))
    print("total cost", total_cost(recon))
    print(recon)
    gg = hill(recon, graph_ort)
    print("num_of_visited_nodes", num_of_visited_nodes(gg))
    print("overlap", count_overlap(gg))
    print(total_cost(gg))
    print(gg)
