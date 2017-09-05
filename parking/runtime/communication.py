def mark_neighbours(vehicles, distance):
    """ Discovers neighbors for a vehicles and saves them internally into
    vehicle objects.

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

    # loop over vehicles but in other loop don't check vehicles that went
    # through first loop because connections are symmetric
    for veh_idx, veh in list(enumerate(vehicles))[:-1]:
        for other in vehicles[veh_idx + 1:]:
            veh_x, veh_y = veh.position
            oth_x, oth_y = other.position
            if (abs(veh_x - oth_x) + abs(veh_y - oth_y)) < distance:
                veh.connected_neighbors.append(other.name)
                other.connected_neighbors.append(veh.name)

# function to create a graph of connected groups i.e. if veh0 is connected to
# veh1 and veh1 is connected to veh2 then all 3 vehicles share same info about
# parking spaces
def communication_groups(vehicles):
    raise NotImplementedError
