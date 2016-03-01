#!/usr/bin/env python
from __future__ import print_function
import os
import sys
import optparse
import subprocess
import random

# (from SUMO examples:)
# we need to import python modules from the $SUMO_HOME/tools directory
try:
    sys.path.append(os.path.join(os.path.dirname(
        "__file__"), '..', '..', '..', "tools"))  # tutorial in tests
    sys.path.append(os.path.join(os.environ.get("SUMO_HOME", os.path.join(
        os.path.dirname("__file__"), "..", "..")), "tools"))  # tutorial in docs
    from sumolib import checkBinary
except ImportError:
    sys.exit("please declare environment variable 'SUMO_HOME' as the root"+ \
    "directory of your sumo installation (it should contain folders 'bin'," + \
    "'tools' and 'docs')")

import traci
import sumolib
import random

from parkingSearchVehicle import *
from parkingSpace import *
from vehicleFactory import *

# use first command line argument as number of available parking spaces (20 if
# no argument given)
if len(sys.argv) > 1:
	NUMBER_OF_PARKING_SPACES = int(sys.argv[1])
else:
	NUMBER_OF_PARKING_SPACES = 20

# use second command line argument as number of parking search vehicles (10 if
# no argument given)
if len(sys.argv) > 2:
    NUMBER_OF_PSV = int(sys.argv[2])
else:
    NUMBER_OF_PSV = 10

# for the static simulation (no parking spaces are vacated during the
# simulation):
# check whether sufficient parking spaces are available
if NUMBER_OF_PSV > NUMBER_OF_PARKING_SPACES:
    print("ERROR: more vehicles than parking spaces available")
    exit()

# (from SUMO examples)
# the port used for communicating with your sumo instance
PORT = 8873

# seed for random number generator, random for now
random.seed()

## Runs the simulation on both SUMO and Python layers
def run():
    # (from SUMO examples):
    # execute the TraCI control loop
    traci.init(PORT)
    # internal clock variable, start with 0
    step = 0
    # create a list for all network edges
    edges = []
	# use sumolib to parse the edges XML file and write edge IDs to the list
    for edge in sumolib.output.parse('reroute.edg.xml', ['edge']):
    	edges.append(str(edge.id))
    # full number of edges in the network
    numberOfEdgesinNetwork = len(edges)

    # use sumolib to read the network XML file
    net = sumolib.net.readNet('reroute.net.xml')
    # create a dictionary for easy lookup of opposite edges to any edge
    oppositeEdgeID = {}
    # iterate twice over all edges
    for edge in edges:
    	for otherEdge in edges:
    		# if from/to nodes of one edge match to/from of the other edge
    		# those two are opposite edges, create the dictionary entry
                if ((net.getEdge(edge).getToNode().getID() ==
                    net.getEdge(otherEdge).getFromNode().getID()) and
                    (net.getEdge(edge).getFromNode().getID() ==
                        net.getEdge(otherEdge).getToNode().getID())):
    			oppositeEdgeID[edge] = otherEdge

    # counter for parking spaces during creation
    parkingSpaceNumber=0
    # create empty list for parking spaces
    parkingSpaces = []
    for edge in edges:
        # get length of each edge (somehow TraCI can only get lane lengths,
        # therefore the id string modification)
        length = traci.lane.getLength(edge+"_0")
        # if an edge is at least 40 meters long, start at 18 meters and 
        # create parking spaces every 7 meters until up to 10 meters before the
        # edge ends.
        #     (vehicles can only 'see' parking spaces once they are on the same
        #     edge;
        #     starting at 18 meters ensures the vehicles can safely stop at the
        #     first parking space if it is available)
        if length > 40.0:
            position = 18.0
            # as long as there are more than 10 meters left on the edge, add
            # another parking space
            while position < (traci.lane.getLength(edge+"_0")-10.0):
                parkingSpaces.append(ParkingSpace(parkingSpaceNumber, edge,
                    position))
                # also add SUMO poi for better visualization in the GUI
                traci.poi.add("ParkingSpace" + str(parkingSpaceNumber),
                    traci.simulation.convert2D(edge,(position-2.0))[0],
                    traci.simulation.convert2D(edge,(position-2.0))[1],
                    (255,0,0,0))
                # increment counter
                parkingSpaceNumber+=1
                # go seven meters ahead on the edge
                position+=7.0
    
    # mark a number parking spaces as available as specified per command line
    # argument
    for i in range(0, NUMBER_OF_PARKING_SPACES):
    	# check whether we still have enough parking spaces to make available
        if NUMBER_OF_PARKING_SPACES > parkingSpaceNumber:
            print("Too many parking spaces for network.")
            exit()
        # select a random parking space which is not yet available, and make it
        # available
        success = False
        while not success:
            availableParkingSpaceID = int(random.random()*parkingSpaceNumber)
            if not parkingSpaces[availableParkingSpaceID].available:
                success = True
        # make sure the available parking space is not assigned to any vehicle
        parkingSpaces[availableParkingSpaceID].unassign()    
                
    # create empty list for parking search vehicles
    parkingSearchVehicles=[]

    # do simulation time steps as long as vehicles are present in the network
    while traci.simulation.getMinExpectedNumber() > 0:
    	# tell SUMO to do a simulation step
        traci.simulationStep()
        # increase local time counter
        step += 1
        # every 1000 steps: ensure local time still corresponds to SUMO
        # simulation time
        # (just a safety check for now, can possibly be removed later)
        if step != (traci.simulation.getCurrentTime()/1000):
        	print("TIMESTEP ERROR", step, "getCurrentTime", 
        	        traci.simulation.getCurrentTime())
        # if a new vehicle has departed in SUMO, create the corresponding Python
        # representation
        for vehID in traci.simulation.getDepartedIDList():
        	parkingSearchVehicles.append(ParkingSearchVehicle(vehID, step))
        # if a vehicle has disappeared in SUMO, remove the corresponding Python
        # representation
        for vehID in traci.simulation.getArrivedIDList():
                # for now: output to console that the vehicle disappeared upon
                # reaching the destination
            print(str(vehID), 
                    "did not find an available parking space during phase 2.")
            parkingSearchVehicles.remove(ParkingSearchVehicle(vehID))
        # update status of all vehicles
        # TODO: differentiate this update method into e.g.
        #       getVehicleData() ..... all TraCI getSomething commands
        #       computeRouting() ..... non-cooperative routing
        #       computeCoopRouting() . cooperative routing
        #       selectRouting() ...... select whether to cooperate or not
        #       setVehicleData() ..... all TraCI setSomething commands
        for psv in parkingSearchVehicles:
        	psv.update(parkingSpaces, oppositeEdgeID, step)
        	

    # (from SUMO examples):
    # close the TraCI control loop
    traci.close()
    sys.stdout.flush()


## Get additional command line arguments (from SUMO examples)
def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true", default=False,
                        help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


# Main entry point of the simulation script (from SUMO examples)
if __name__ == "__main__":
	# get additional command line arguments (from SUMO examples)
    options = get_options()

    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # generate the route file for this simulation run
    # using the given number of parking search vehicles
    generatePsvDemand(NUMBER_OF_PSV)

    # (from SUMO examples:)
    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    sumoProcess = subprocess.Popen(
                [sumoBinary, "-c", "reroute.sumo.cfg", "--tripinfo-output", 
                    "tripinfo.xml", "--gui-settings-file", "gui-settings.cfg", 
                    "--remote-port", str(PORT)], stdout=sys.stdout, 
                stderr=sys.stderr)
    run()
    sumoProcess.wait()
