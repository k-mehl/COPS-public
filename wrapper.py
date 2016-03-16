#!/usr/bin/env python
from __future__ import print_function

import sys
import runner

# default values, can be modified by command line parameters
NUMBER_OF_RUNS = 10
NUMBER_OF_PSV  = 5
NUMBER_OF_PARKING_SPACES = 5
COOP_RATIO = 0.0

# use first command line argument as number of runs
if len(sys.argv) > 1:
    NUMBER_OF_RUNS = int(sys.argv[1])

# use second command line argument as number of available parking spaces
# (20 if no argument given)
if len(sys.argv) > 2:
    NUMBER_OF_PARKING_SPACES = int(sys.argv[2])

# use third command line argument as number of parking search vehicles
# (10 if no argument given)
if len(sys.argv) > 3:
    NUMBER_OF_PSV = int(sys.argv[3])
    
# use fourth command line argument as ratio of cooperative drivers
if len(sys.argv) > 4:
    COOP_RATIO = float(sys.argv[4])

# Main entry point for the wrapper module.
# For now: starts repetitive simulation runs with identical parameters, 
# and presents the results afterwards.
if __name__ == "__main__":
	successesSum       = 0
	searchTimesSum     = 0
	searchDistancesSum = 0.0
	for run in range(NUMBER_OF_RUNS):
		print("RUN:", run, "OF", NUMBER_OF_RUNS)
		successes, searchTimes, searchDistances = \
			runner.wrapper(NUMBER_OF_PARKING_SPACES, \
			NUMBER_OF_PSV, \
			COOP_RATIO)
		successesSum += successes
		searchTimesSum += sum(searchTimes) #/ float(len(searchTimes))
		searchDistancesSum += sum(searchDistances) #/ float(len(searchDistances))
	successRate = 100*successesSum/(NUMBER_OF_RUNS*NUMBER_OF_PSV)
	print("")
	print("==== SUMMARY AFTER", NUMBER_OF_RUNS, "RUNS ====")
	print("PARAMETERS:        ", NUMBER_OF_PARKING_SPACES, "parking spaces")
	print("                   ", NUMBER_OF_PSV, "searching vehicles")
	print("                   ", COOP_RATIO*100, "percent of drivers cooperate")
	print("TOTAL SUCCESS RATE:", successRate, "percent",
		"of cars found an available parking space")
	if successesSum:
		searchTimesAvg = searchTimesSum / float(successesSum)
		searchDistancesAvg = searchDistancesSum / float(successesSum)
		print("AVG SEARCH TIME    ", searchTimesAvg, "seconds")
		print("AVG SEARCH DISTANCE", searchDistancesAvg, "meters")
	print("")
