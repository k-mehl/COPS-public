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

try:
    import itertools.izip as zip
except ImportError:
    pass

reconstruct_path = CooperativeSearch.reconstruct_path


def count_overlap(driver_matrix):
    """ Calculate the overlap based on the number of edges that are visited
    multiple times.

    Args:
        driver_matrix (list of lists): A list whose members are lists that
        contain paths that are represented by consecutively visited nodes.
    Returns:
        int: A number of edges that were traversed multiple times.
    """
    forward_edges = chain.from_iterable((zip(x, x[1:]) for x in driver_matrix))
    backward_edges = chain.from_iterable((zip(x[::-1], x[-2::-1]) for x in
                                          driver_matrix))
    edges = list(chain(forward_edges, backward_edges))
    return len(edges) - len(set(edges))


def num_of_visited_nodes(driver_matrix):
    """ Calculate the total number of visited nodes for multiple paths.

    Args:
        driver_matrix (list of lists): A list whose members are lists that
        contain paths that are represented by consecutively visited nodes.
    Returns:
        int: Number of visited nodes
    """
    return sum((len(x) for x in driver_matrix))


def total_cost(driver_matrix):
    """ Sum of number of total visited nodes and edge overlap. """
    return count_overlap(driver_matrix) + num_of_visited_nodes(driver_matrix)


def hill(driver_matrix, adjacency_matrix):
    """ A hill based optimizer for routes.

    Note:
        Cost function is based on the sum of number of visited nodes and edges
        that overlap. Goal is to minimize this sum.

    Args:
        driver_matrix (list of lists): A list whose members are lists that
            contain paths that are represented by consecutively visited nodes.

        adjacency_matrix (list of lists): Adjacency matrix of an underlying
            graph.

    Returns:
        list: Optimized list of routes.
    """
    # TODO normalize cost
    # TODO: make all this into a class
    costs = [total_cost(driver_matrix)]
    feasible_ind = [x[0] for x in enumerate(driver_matrix) if len(x[1]) > 3]
    # too short, no need to optimize
    if not feasible_ind:
        return driver_matrix

    def hill_runner(driver_matrix, adjacency_matrix):
        cost = total_cost(driver_matrix)
        d = choice(feasible_ind)  # pick a random driver path index
        # do not use paths that are to small i.e. smaller than 4
        path = driver_matrix[d]
        # pick a random node excluding first and the last (start and end)
        path_end = len(path) - 1
        node_ind = randint(1, path_end - 1)
        node = path[node_ind]
        path_neighbors = (path[node_ind - 1], path[node_ind + 1])
        # chose where to move (you can not move into neighbors already in path)
        neighbors = adjacency_matrix[node][:]
        move_to = [x for x in enumerate(neighbors)
                   if x[1] != 0 and x[0] not in path_neighbors]
        if not move_to:
            # you are in the corner, so no change just return
            return driver_matrix
        move_to = choice(move_to)[0]
        # get the shortest route to connecting nodes
        if node_ind == 1:
            left_ind = 0
        else:
            left_ind = node_ind - 2

        if node_ind == path_end - 1:
            righ_ind = path_end
        else:
            righ_ind = node_ind + 2

        left = path[left_ind]
        right = path[righ_ind]

        left_route, righ_route = CooperativeSearch(adjacency_matrix,
                                                   [left, move_to],
                                                   0).shortest().path_lst

        left_path = reconstruct_path(left_route, move_to, left)
        right_path = reconstruct_path(righ_route, right, move_to)

        new_path = path[:left_ind] + left_path + right_path[1:-1] + path[righ_ind:]

        # TODO: some stupid cases where edge gets duplicated discard such
        # cases... in this situation 2 cases should be checked: left path
        # routed without the node that got repeated twice right path router
        # without the node that got repeated twice and then better option
        # should be chosen in any case cycles are out of question here
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

    for i in xrange(1000):
        driver_matrix = hill_runner(driver_matrix, adjacency_matrix)
        costs.append(total_cost(driver_matrix))
        # Check if you can stop
        if len(costs) > 100 and len(set(costs[-100:])) == 1:
            return driver_matrix
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
    # cars = [5, 5, 5, 5, 5]

    obj = CooperativeSearch(graph_ort, cars)
    sh = obj.shortest().path_lst
    dest = [15, 15, 15, 15, 15]
    # dest = [6, 4, 5, 14, 0]

    recon = []
    for i in xrange(len(cars)):
        recon.append(obj.reconstruct_path(sh[i], dest[i]))
        print(obj.reconstruct_path(sh[i], dest[i], cars[i]))

    print("num_of_visited_nodes", num_of_visited_nodes(recon))
    print("overlap", count_overlap(recon))
    print("total cost", total_cost(recon))
    print(recon)
    gg = hill(recon, graph_ort)
    print("num_of_visited_nodes", num_of_visited_nodes(gg))
    print("overlap", count_overlap(gg))
    print("total_cost", total_cost(gg))
    print(gg)
