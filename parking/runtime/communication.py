from collections import deque

def mark_neighbours(vehicles, distance):
    """ Discovers neighbors for a vehicles and saves them internally into
    vehicle objects. Has complexity of approx O(len(vehicles)**2/2).

    Args:
        vehicles (list): A list with vehicle object whose neighbors should be
            discovered.
        distance (float): Maximum distance between two vehicles such that they
            can be considered neighbors. Manhattan distance is used for faster
            computation.
    """
    # Reset previous neighbors
    for v in vehicles:
        v.connected_neighbors = []

    # loop over vehicles but in inner loop don't check vehicles that went
    # through first loop because connections are symmetric
    for veh_idx, veh in list(enumerate(vehicles))[:-1]:
        for other in vehicles[veh_idx + 1:]:
            veh_x, veh_y = veh.position
            oth_x, oth_y = other.position
            if (abs(veh_x - oth_x) + abs(veh_y - oth_y)) < distance:
                veh.connected_neighbors.append(other)
                other.connected_neighbors.append(veh)

def communication_groups(vehicles):
    """ Creates groups of vehicles that are connected at specific time step
    with an assumption that communication is instantaneous. For example if
    vehicle_0 is connected to vehicle_1 and vehicle_1 is connected to vehicle_2
    then all 3 vehicles share same knowledge about parking spaces.

    Args:
        vehicles (list): A list with vehicle objects.

    Returns:
        list(list): A list of list where each inner list is a group of vehicles
            that share the same knowledge at that time instance
    """
    vehicles = vehicles[:]

    groups = []
    while vehicles:
        group = []
        veh_queue = deque([vehicles[0]])

        while veh_queue:
            veh = veh_queue.pop()
            group.append(veh)

            # don't add to queue vehicles that are already in the group or are
            # already in the queue
            filtered = (v for v in veh.connected_neighbors
                        if (v not in group) and (v not in veh_queue))
            veh_queue.extend(filtered)

            if vehicles:
                vehicles.remove(veh)

        groups.append(group)
    return groups
