#!/usr/bin/env python
from __future__ import print_function

import argparse
import os

from runtime import runner
from runtime import configuration



# Main entry point for the wrapper module.
# For now: starts repetitive simulation runs with identical parameters, 
# and presents the results afterwards.
if __name__ == "__main__":
    l_configdir = os.path.expanduser(u"~/.parkingsearch")
    l_parser = argparse.ArgumentParser(description="Process parameters for headless simulation runs.")
    l_parser.add_argument("--config", dest="config", type=str, default=os.path.join(l_configdir, u"config.json"))
    l_parser.add_argument("-p","--parkingspaces", dest="parkingspaces", type=int, help="number of available parking spaces")
    l_parser.add_argument("-s","--parking-search-vehicles", dest="psv", type=int, help="number of parking search vehicles")
    l_parser.add_argument("-c","--cooperative-ratio", dest="coopratio", type=float, help="cooperative driver ratio [0,1]")
    l_parser.add_argument("--port", dest="sumoport", type=int, help="port used for communicating with sumo instance")
    l_parser.add_argument("--load-route-file", dest="routefile", type=str, help="provide a route file (SUMO xml format), overrides use of auto-generated routes")
    l_parser.add_argument("--resourcedir", dest="resourcedir", type=str, help="base directory, relative to current working directory, for reading/writing temporary and SUMO related files (default: resources)")
    l_parser.add_argument("-r","--runs", dest="runs", type=int, help="number of iterations to run")
    l_parser.add_argument("--runconfig", dest="runconfiguration", type=str, help="json configuration file containing environment information for each run")

    # if display GUI, restrict to one run (implies --run 1)
    # for more than one run, disallow use of --gui
    l_mutexgroup = l_parser.add_mutually_exclusive_group(required=False)
    l_mutexgroup.add_argument("--gui", dest="gui", default=False, action='store_true', help="start simulation with SUMO GUI")
    l_mutexgroup.add_argument("--headless", dest="headless", default=False, action='store_true', help="start simulation in headless mode without SUMO GUI")

    l_args = l_parser.parse_args()

    # get config
    l_config = configuration.Configuration(l_args, l_configdir)


    l_resultSum = 0

    l_successesSum       = 0
    l_searchTimesSum     = 0
    l_searchDistancesSum = 0.0

    l_runtime = runner.Runtime(l_config)

    print("* pre-testing runcfg for all runs")
    if l_config.existRunCfg() and len(filter(lambda i_run: not l_config.isRunCfgOk(i_run), xrange(l_config.getCfg("simulation").get("runs")))) > 0:
        raise StandardError("/!\ error(s) in run configuration")

    for i_run in xrange(l_config.getCfg("simulation").get("runs")):
        print("RUN:", i_run+1, "OF", l_config.getCfg("simulation").get("runs"))
        l_successes, l_searchTimes, l_searchDistances = l_runtime.run(i_run)

        l_successesSum += l_successes
        l_searchTimesSum += sum(l_searchTimes) #/ float(len(searchTimes))
        l_searchDistancesSum += sum(l_searchDistances) #/ float(len(searchDistances))

    l_successRate = 100*l_successesSum/(l_config.getCfg("simulation").get("runs")*l_config.getCfg("simulation").get("vehicles"))
    print("")
    print("==== SUMMARY AFTER", l_config.getCfg("simulation").get("runs"), "RUNS ====")
    print("PARAMETERS:        ", l_config.getCfg("simulation").get("parkingspaces").get("free"), "free parking spaces")
    print("                   ", l_config.getCfg("simulation").get("vehicles"), "searching vehicles")
    print("                   ", l_config.getCfg("simulation").get("cooperation")*100, "percent of drivers cooperate")
    print("TOTAL SUCCESS RATE:", l_successRate, "percent",
        "of cars found an available parking space")
    print("")

    if l_successesSum:
        l_searchTimesAvg = l_searchTimesSum / float(l_successesSum)
        l_searchDistancesAvg = l_searchDistancesSum / float(l_successesSum)
        print("AVG SEARCH TIME    ", l_searchTimesAvg, "seconds")
        print("AVG SEARCH DISTANCE", l_searchDistancesAvg, "meters")
    print("")

    # write run cfg
    l_config.writeRunCfg()
