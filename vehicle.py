
class Vehicle(object):

    """Docstring for Vehicle. """

    def __init__(self):
        self.position = [0,0]
        self.destination = [0,0]
        self.route = [list(self.position)] # must start at starting point
        self.shortest_path = []

        #bad solution but play with it
        self.checked = []
        self.last_node = []
        self.next_node = []

    def set_position(self, pos_x, pos_y):
        # vehicle can only start at node, for now that means that it starts at:
        assert self.position[0] % 2 == 0 and self.position[1] % 2 == 0
        # ================ remove this later ===================
        self.position = [pos_x, pos_y]
        self.route = [list(self.position)]

    def get_position(self):
        return self.position

    def set_destination(self, pos_x, pos_y):
        self.destination = [pos_x, pos_y]
        self._shortest_path()
        return self.destination

    def get_destination(self):
        return self.destination

    def update_position(self, pos_x = 0, pos_y = 0):
        # this update method is for more general case for now simpler update will do
        self.position[0] = round(self.position[0] + pos_x, 2)
        self.position[1] = round(self.position[1] + pos_y, 2)
        return self.position

    def traversed(self, *args):
        """ Manually add visited nodes in order they were visited """
        for node in args:
            self.route.append(node)
        return self.route

    def _shortest_path(self):
        # first update x or y until coordinates meet we add with 2 since we will
        # make the grid to be div into parts of 2, but car must start at coords
        # that are divisible by 2, as a test this will do and x > 0, y > 0
        # silly but will do for now
        # self.shortest_path.append(self.position) # why would I need my 
        # position here?

        start = list(self.position)
        def go_horizontal():
            if start[0] < self.destination[0]:
                start[0] += 2
                self.shortest_path.append(list(start))
            elif start[0] > self.destination[0]:
                start[0] -= 2
                self.shortest_path.append(list(start))

        # go to y coord when x is ok
        def go_vertical():
            if start[1] < self.destination[1]:
                start[1] += 2
                self.shortest_path.append(list(start))
            elif start[1] > self.destination[1]:
                start[1] -= 2
                self.shortest_path.append(list(start))
        
        # check if we already traversed that path and plan accordingly
        # for now if we have a path we move diagonally
        if len(self.checked) != 0:
            while start != self.destination:
                if (start[0] - 2) not in self.checked or \
                        (start[0] + 2) not in self.checked:
                    go_horizontal()
                else:
                    print("You shouldnt be here!! Horizontal if")
                if (start[1] - 2) not in self.checked or \
                        (start[1] + 2) not in self.checked:
                    go_vertical()
                else:
                    print("You shouldnt be here!! Vertical if")
        # car can not get stuck since it will end up here if both conditions
        # are not valid so it will move horizontally first and then vertically
        else: 
            while start[0] != self.destination[0]:
                go_horizontal()
            while start[1] != self.destination[1]:
                go_vertical()

    def update(self):
        # whole logic of sim is happening here, not very good should just 
        # update position and some other part should check for logic
        # also an ugly solution....
        if len(self.shortest_path) == 0:
            return
        if len(self.last_node) == 0 and len(self.next_node) == 0:
            self.last_node = list(self.route[-1])
            self.next_node = list(self.shortest_path[0])
        #if true than we have some work to do
        if self.last_node[0] != self.next_node[0] or \
                self.last_node[1] != self.next_node[1]:

            if self.last_node[0] < self.next_node[0]:
                self.update_position(0.2, 0)
            elif self.last_node[0] > self.next_node[0]:
                self.update_position(-0.2, 0)

            if self.last_node[1] < self.next_node[1]:
                self.update_position(0, 0.2)
            elif self.last_node[1] > self.next_node[1]:
                self.update_position(0, -0.2)
            if self.position[0] == self.next_node[0] and \
                    self.position[1] == self.next_node[1]:
                self.route.append(list(self.next_node))
                self.shortest_path = self.shortest_path[1:]
                self.last_node = list(self.route[-1])
                if len(self.shortest_path) != 0:
                    self.next_node = list(self.shortest_path[0])
                
if __name__ == "__main__":
    #TODO add checks for shortest path when we have a path already
    vec = Vehicle()
    assert vec.get_position() == [0,0]
    vec.set_position(2,2)
    assert vec.get_position() == [2,2]
    assert vec.update_position(0.2,0.2) == [2.2, 2.2]
    assert vec.update_position(-0.2,-0.2) == [2, 2]
    assert vec.update_position() == [2, 2]

    node1, node2, node3 = [[1,2],[4,8],[10,11]]
    # unpacking nodes
    assert vec.traversed(*[node1, node2]) == [vec.route[0], node1, node2]
    # adding unpacked nodes
    assert vec.traversed(node3) == [vec.route[0], node1, node2, node3]
    # adding coordinates
    assert vec.traversed([1,2]) == [vec.route[0],node1, node2, node3,[1,2]]

    # start all over again
    vec = Vehicle()
    vec.set_destination(6,6)
    print("Shortest route (without starting positions): ")
    print(vec.shortest_path) #implement get_shortest path method 

    for i in range(70):
        vec.update()
    assert vec.position == vec.get_destination()
    print("Traversed route")
    print(vec.route)
    print("================ The other diagonal test =========================")
    vec1 = Vehicle()
    vec1.set_position(18,2)
    vec1.set_destination(2,18)
    print("Shortest route (without starting positions): ")
    print(vec1.shortest_path)
    for i in range(200):
        vec1.update()
    assert vec1.get_position() == vec1.get_destination()
    print("Traversed route")
    print(vec1.route)
    print("Program finished")
else:
    print("Import of vehicle class went ok")
