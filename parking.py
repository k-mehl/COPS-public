#!/usr/bin/env python
from __future__ import print_function

import argparse
import os
import time

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

    print("* pre-testing runcfg for all runs")
    if l_config.existRunCfg():
        if len(filter(lambda i_run: not l_config.isRunCfgOk(i_run), xrange(l_config.getCfg("simulation").get("runs")))) > 0:
            raise StandardError("/!\ error(s) in run configuration")
        else:
            print("  passed.")
    else:
        print("  no runcfg found/loaded.")


    l_resultSum = 0

    l_successesSum       = 0
    l_searchTimesSum     = 0
    l_searchDistancesSum = 0.0
    l_walkingDistancesSum= 0.0
    l_totalDistancesSum  = 0.0

    l_numParkingSpaces = l_config.getCfg("simulation").get("parkingspaces")
    l_numVehicles = l_config.getCfg("simulation").get("vehicles")
    l_numCooperation = l_config.getCfg("simulation").get("cooperation")
    l_numRuns = l_config.getCfg("simulation").get("runs")

    l_runtime = runner.Runtime(l_config)

    l_mainresultdir = "results"

    if not os.path.isdir(l_mainresultdir):
            os.mkdir(l_mainresultdir)

    l_resultdir = time.strftime("%Y%m%d%H%M%S")

    if not os.path.isdir((os.path.join(l_mainresultdir, l_resultdir))):
            os.mkdir((os.path.join(l_mainresultdir, l_resultdir)))

    l_resultfile = "details-s" + str(l_numVehicles) + \
        "p" + str(l_numParkingSpaces) + \
        "c" + str(int(l_numCooperation*100)) + \
        "r" + str(l_numRuns) + ".csv"

    l_summaryfile= "summary-s" + str(l_numVehicles) + \
        "p" + str(l_numParkingSpaces) + \
        "c" + str(int(l_numCooperation*100)) + \
        "r" + str(l_numRuns) + ".txt"

    rf = open(os.path.join(l_mainresultdir, l_resultdir, l_resultfile), 'w')


    for i_run in xrange(l_config.getCfg("simulation").get("runs")):
        print("RUN:", i_run, "OF", l_config.getCfg("simulation").get("runs")-1)
        l_successes, l_searchTimes, l_searchDistances, l_walkingDistances = l_runtime.run(i_run)
        for i_result in range(len(l_searchTimes)):
            print
            rf.write(str(l_numVehicles) + ",")
            rf.write(str(l_numParkingSpaces) + ",")
            rf.write(str(l_numCooperation) + ",")
            rf.write(str(l_searchTimes[i_result]) + ",")
            rf.write(str(l_searchDistances[i_result]) + ",")
            rf.write(str(l_walkingDistances[i_result]) + ",")
            rf.write(str((l_searchDistances[i_result]+l_walkingDistances[i_result])) + "\n")
        l_successesSum += l_successes
        l_searchTimesSum += sum(l_searchTimes) #/ float(len(searchTimes))
        l_searchDistancesSum += sum(l_searchDistances) #/ float(len(searchDistances))
        l_walkingDistancesSum += sum(l_walkingDistances)
        l_totalDistancesSum += (sum(l_searchDistances)+sum(l_walkingDistances))


    rf.close()
    
    sf = open(os.path.join(l_mainresultdir, l_resultdir, l_summaryfile), 'w')

    l_successRate = 100*l_successesSum/(l_config.getCfg("simulation").get("runs")*l_config.getCfg("simulation").get("vehicles"))

    sf.write("")
    sf.write("==== SUMMARY AFTER " + str(l_numRuns) + " RUNS ====\n")
    sf.write("PARAMETERS:          " + str(l_numVehicles) + " vehicles\n")
    sf.write("                     " + str(l_numParkingSpaces) + " parking spaces\n")
    sf.write("                     " + str(int(l_numCooperation*100)) + " percent of drivers cooperate\n")
    if l_successesSum:
        l_searchTimesAvg = l_searchTimesSum / float(l_successesSum)
        l_searchDistancesAvg = l_searchDistancesSum / float(l_successesSum)
        l_walkingDistancesAvg = l_walkingDistancesSum / float(l_successesSum)
        l_totalDistancesAvg = l_totalDistancesSum / float(l_successesSum)
        sf.write("AVG SEARCH TIME      " + str(l_searchTimesAvg) + " seconds\n")
        sf.write("AVG SEARCH DISTANCE  " + str(l_searchDistancesAvg) + " meters\n")
        sf.write("AVG WALKING DISTANCE " + str(l_walkingDistancesAvg) + " meters\n")
        sf.write("AVG TOTAL DISTANCE   " + str(l_totalDistancesAvg) + " meters\n")
    
    sf.close()


