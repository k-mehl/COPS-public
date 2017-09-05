import sys
sys.path.append("../parking")

from parking.runtime.communication import mark_neighbours
from parking.runtime.communication import communication_groups

# Proper vehicle class is harder to use hence a quick mock
class Vehicle():
    num = 0
    name_ = "veh"
    def __init__(self, position_, name_=None):
        if name_:
            self.__class__.name_ = name_

        self.connected_neighbors = []
        self.position = position_
        self.name = Vehicle.name_ + str(Vehicle.num)
        Vehicle.num += 1

def test_mark_neighbours():

    veh0 = Vehicle((0, 0))
    veh1 = Vehicle((0, 100))
    veh2 = Vehicle((200, 100))
    veh3 = Vehicle((1000, 1000))

    vehicles = [veh0, veh1, veh2, veh3]
    mark_neighbours(vehicles, 500)

    assert veh1 in vehicles[0].connected_neighbors
    assert veh2 in vehicles[0].connected_neighbors
    assert veh0 in vehicles[1].connected_neighbors
    assert veh2 in vehicles[1].connected_neighbors
    assert veh0 in vehicles[2].connected_neighbors
    assert veh1 in vehicles[2].connected_neighbors
    assert len(vehicles[0].connected_neighbors) == 2
    assert len(vehicles[1].connected_neighbors) == 2
    assert len(vehicles[2].connected_neighbors) == 2
    assert len(vehicles[-1].connected_neighbors) == 0

def test_communication_groups():
    # reset name number to 0 and set all cords to 0 since they are not relevant
    Vehicle.num = 0
    veh0 = Vehicle((0, 0))
    veh1 = Vehicle((0, 0))
    veh2 = Vehicle((0, 0))
    veh3 = Vehicle((0, 0))
    veh4 = Vehicle((0, 0))
    veh5 = Vehicle((0, 0))

    veh0.connected_neighbors = [veh1]
    veh1.connected_neighbors = [veh0]

    veh3.connected_neighbors = [veh4, veh5]
    veh4.connected_neighbors = [veh3, veh5]
    veh5.connected_neighbors = [veh3, veh4]

    res = communication_groups([veh0, veh1, veh2, veh3, veh4, veh5])

    assert len(res) == 3

    assert len(res[0]) == 2
    assert (veh0 and veh1) in res[0]

    assert len(res[1]) == 1
    assert veh2 in res[1]

    assert len(res[2]) == 3
    assert (veh3 and veh4 and veh5) in res[2]
