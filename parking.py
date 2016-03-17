#!/usr/bin/env python
from __future__ import print_function

import sys
import runner
import argparse

# Main entry point for the wrapper module.
# For now: starts repetitive simulation runs with identical parameters, 
# and presents the results afterwards.
if __name__ == "__main__":
    l_parser = argparse.ArgumentParser(description="Process parameters for headless simulation runs.")
    l_parser.add_argument("-p","--parkingspaces", dest="parkingspaces", type=int, default=5, help="number of available parking spaces")
    l_parser.add_argument("-s","--parking-search-vehicles", dest="psv", type=int, default=5, help="number of parking search vehicles")
    l_parser.add_argument("-c","--cooperative-ratio", dest="coopratio", type=float, default=0.0, help="cooperative driver ratio [0,1]")
    l_parser.add_argument("--port", dest="sumoport", type=int, default=8873, help="port used for communicating with sumo instance")

    l_mutexgroup = l_parser.add_mutually_exclusive_group(required=True)
    l_mutexgroup.add_argument("-g","--gui", dest="gui", default=False, action='store_true', help="start simulation with SUMO GUI")
    l_mutexgroup.add_argument("-r","--runs", dest="runs", type=int, default=1, help="number of iterations to run")

    args = l_parser.parse_args()

    l_resultSum = 0

    l_successesSum       = 0
    l_searchTimesSum     = 0
    l_searchDistancesSum = 0.0

    l_runtime = runner.Runtime(args)

    for i_run in xrange(args.runs):
        print("RUN:", i_run+1, "OF", args.runs)
        l_successes, l_searchTimes, l_searchDistances = l_runtime.run()

        l_successesSum += l_successes
        l_searchTimesSum += sum(l_searchTimes) #/ float(len(searchTimes))
        l_searchDistancesSum += sum(l_searchDistances) #/ float(len(searchDistances))

    l_successRate = 100*l_resultSum/(args.runs*args.psv)
    print("")
    print("==== SUMMARY AFTER", args.runs, "RUNS ====")
    print("PARAMETERS:        ", args.parkingspaces, "parking spaces")
    print("                   ", args.psv, "searching vehicles")
    print("                   ", args.coopratio*100, "percent of drivers cooperate")
    print("TOTAL SUCCESS RATE:", l_successRate, "percent",
        "of cars found an available parking space")
    print("")

    if l_successesSum:
        l_searchTimesAvg = l_searchTimesSum / float(l_successesSum)
        l_searchDistancesAvg = l_searchDistancesSum / float(l_successesSum)
        print("AVG SEARCH TIME    ", l_searchTimesAvg, "seconds")
        print("AVG SEARCH DISTANCE", l_searchDistancesAvg, "meters")
    print("")

