#!/usr/bin/env python
from __future__ import print_function

import argparse
import os

from runtime import runner

# Main entry point for the wrapper module.
# For now: starts repetitive simulation runs with identical parameters, 
# and presents the results afterwards.
if __name__ == "__main__":
    l_parser = argparse.ArgumentParser(description="Process parameters for headless simulation runs.")
    l_parser.add_argument("-p","--parkingspaces", dest="parkingspaces", type=int, default=5, help="number of available parking spaces")
    l_parser.add_argument("-s","--parking-search-vehicles", dest="psv", type=int, default=5, help="number of parking search vehicles")
    l_parser.add_argument("-c","--cooperative-ratio", dest="coopratio", type=float, default=0.0, help="cooperative driver ratio [0,1]")
    l_parser.add_argument("--port", dest="sumoport", type=int, default=8873, help="port used for communicating with sumo instance")
    l_parser.add_argument("--load-route-file", dest="routefile", type=str, help="provide a route file (SUMO xml format), overrides use of auto-generated routes")
    l_parser.add_argument("--resourcedir", dest="resourcedir", type=str, default="resources", help="base directory, relative to current working directory, for reading/writing temporary and SUMO related files (default: resources)")
    l_parser.add_argument("-r","--runs", dest="runs", type=int, default=1, help="number of iterations to run")
    l_parser.add_argument("--fixedseed", dest="fixedseed", type = int, default=1, help="flag whether random number generator get run number as fixed seed")

    # if display GUI, restrict to one run (implies --run 1)
    # for more than one run, disallow use of --gui
    l_mutexgroup = l_parser.add_mutually_exclusive_group(required=True)
    l_mutexgroup.add_argument("-g","--gui", dest="gui", default=False, action='store_true', help="start simulation with SUMO GUI")
    l_mutexgroup.add_argument("--headless", dest="headless", default=False, action='store_true', help="start simulation in headless mode without SUMO GUI (default)")

    l_args = l_parser.parse_args()

    # raise exception if gui mode requested with > 1 run
    if l_args.gui and l_args.runs > 1:
        message = "Number of runs can't exceed 1, if run in GUI mode."
        raise argparse.ArgumentTypeError(message)

    # raise exception if headless mode requested  AND number of parking spaces < vehicles
    # in the static case this produces an endless loop of at least one vehicle searching for a free space.
    # In Gui mode this behavior is acceptable
    if l_args.headless and l_args.parkingspaces < l_args.psv:
        message = "Number of parking spaces must be at least equal to number of vehicles, if run in headless mode."
        raise argparse.ArgumentTypeError(message)

    # raise an exception if basedir does not exist
    if not os.path.isdir(l_args.resourcedir):
        message = "The provided directory {} does not exist for argument --resourcedir".format(l_args.resourcedir)
        raise argparse.ArgumentTypeError(message)

    l_resultSum = 0

    l_successesSum       = 0
    l_searchTimesSum     = 0
    l_searchDistancesSum = 0.0

    l_runtime = runner.Runtime(l_args)

    for i_run in xrange(l_args.runs):
        print("RUN:", i_run+1, "OF", l_args.runs)
        l_successes, l_searchTimes, l_searchDistances = l_runtime.run(i_run)

        l_successesSum += l_successes
        l_searchTimesSum += sum(l_searchTimes) #/ float(len(searchTimes))
        l_searchDistancesSum += sum(l_searchDistances) #/ float(len(searchDistances))

    l_successRate = 100*l_successesSum/(l_args.runs*l_args.psv)
    print("")
    print("==== SUMMARY AFTER", l_args.runs, "RUNS ====")
    print("PARAMETERS:        ", l_args.parkingspaces, "parking spaces")
    print("                   ", l_args.psv, "searching vehicles")
    print("                   ", l_args.coopratio*100, "percent of drivers cooperate")
    print("TOTAL SUCCESS RATE:", l_successRate, "percent",
        "of cars found an available parking space")
    print("")

    if l_successesSum:
        l_searchTimesAvg = l_searchTimesSum / float(l_successesSum)
        l_searchDistancesAvg = l_searchDistancesSum / float(l_successesSum)
        print("AVG SEARCH TIME    ", l_searchTimesAvg, "seconds")
        print("AVG SEARCH DISTANCE", l_searchDistancesAvg, "meters")
    print("")

