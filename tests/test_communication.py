import sys
sys.path.append("../parking")

from parking.runtime.communication import mark_neighbours

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
    vehicles = [Vehicle((0, 0)),
                Vehicle((0, 100)),
                Vehicle((200, 100)),
                Vehicle((1000, 1000))]

    mark_neighbours(vehicles, 500)

    assert "veh1" in vehicles[0].connected_neighbors
    assert "veh2" in vehicles[0].connected_neighbors
    assert "veh0" in vehicles[1].connected_neighbors
    assert "veh2" in vehicles[1].connected_neighbors
    assert "veh0" in vehicles[2].connected_neighbors
    assert "veh1" in vehicles[2].connected_neighbors
    assert len(vehicles[0].connected_neighbors) == 2
    assert len(vehicles[1].connected_neighbors) == 2
    assert len(vehicles[2].connected_neighbors) == 2
    assert len(vehicles[-1].connected_neighbors) == 0
