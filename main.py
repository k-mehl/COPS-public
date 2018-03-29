#!/usr/bin/env python3
from __future__ import print_function

import argparse
import os
import time
import traceback

from parking.runtime import runner
from parking.runtime import configuration


try:
    xrange
except NameError:
    xrange = range

if __name__ == "__main__":
    l_configdir = os.path.expanduser(u"~/.parkingsearch")
    l_parser = argparse.ArgumentParser(
        description="Command line interfrace for whole project.")
    l_parser.add_argument("--config", dest="config", type=str,
                          default=os.path.join(l_configdir, u"config.json"))
    l_parser.add_argument("-p", "--parkingspaces", dest="parkingspaces",
                          type=int, help="number of available parking spaces")
    l_parser.add_argument("-s", "--parking-search-vehicles", dest="psv",
                          type=int, help="number of parking search vehicles")
    l_parser.add_argument("--cooperative-ratio-phase-two",
                          dest="coopratioPhase2", type=float,
                          help="force cooperative driver ratio in phase 2 to value [0,1]")
    l_parser.add_argument("--cooperative-ratio-phase-three",
                          dest="coopratioPhase3", type=float,
                          help="force cooperative driver ratio in phase 3 to value [0,1]")
    l_parser.add_argument("--port", dest="sumoport", type=int,
                          help="port used for communicating with sumo instance")
    l_parser.add_argument("--load-route-file", dest="routefile", type=str,
                          help="provide a route file (SUMO xml format), "
                               "overrides use of auto-generated routes")
    l_parser.add_argument("--resourcedir", dest="resourcedir", type=str,
                          help="base directory, relative to current working "
                               "directory, for reading/writing temporary and "
                               "SUMO related files")
    l_parser.add_argument("-r", "--runs", dest="runs", type=int,
                          help="number of iterations to run")
    l_parser.add_argument("--runconfig", dest="runconfiguration", type=str,
                          help="json configuration file containing environment"
                               " information for each run")
    l_parser.add_argument("--verbose", dest="verbose", default=False,
                          action='store_true',
                          help="output more full vehicle parking data")
    l_parser.add_argument("--timestamp", dest="resulttimestamped",
                          default=False, action='store_true',
                          help="create timestamped folders for output")
    # new parser configuration for mixed traffic
    l_parser.add_argument("--mixed_traffic", dest="mixed_traffic", nargs=3,
                          help="run simulation with new mixed traffic. "
                               "The ratio defines how many connected vehicles will be created."
                               "please set additional arguments for ratio [float], coopPhase3 [bool], coopPhase2 [bool]")

    # if display GUI, restrict to one run (implies --run 1)
    # for more than one run, disallow use of --gui
    l_mutexgroup = l_parser.add_mutually_exclusive_group(required=False)
    l_mutexgroup.add_argument("--gui", dest="gui", default=False,
                              action='store_true',
                              help="start simulation with SUMO GUI")
    l_mutexgroup.add_argument("--headless", dest="headless", default=False,
                              action='store_true',
                              help="start simulation in headless mode without "
                                   "SUMO GUI")

    l_args = l_parser.parse_args()

    # get config
    l_config = configuration.Configuration(l_args, l_configdir)

    print("* pre-testing runcfg for all runs")
    sim_conf = l_config.getCfg("simulation")
    if l_config.existRunCfg():
        tmp_iter = xrange(sim_conf.get("runs"))
        if [run for run in tmp_iter if not l_config.isRunCfgOk(run)]:
            raise BaseException("Error(s) in run configuration")
        else:
            print("  -> passed.")
    else:
        print("  -> no runcfg found/loaded.")


    l_resultSum = 0
    l_successesSum = 0
    l_searchTimesSum = 0
    l_walkingTimesSum = 0
    l_totalTimesSum = 0
    l_searchDistancesSum = 0.0
    l_walkingDistancesSum = 0.0
    l_totalDistancesSum = 0.0
    l_parkedInPhase2Sum = 0
    l_parkedInPhase3Sum = 0
    l_maxTimeSum = 0
    l_maxDistanceSum = 0.0

    l_numParkingSpaces = sim_conf.get("parkingspaces")['free']
    l_numVehicles = sim_conf.get("vehicles")
    l_numCoopPhase2 = sim_conf.get("coopratioPhase2")
    l_numCoopPhase3 = sim_conf.get("coopratioPhase3")
    l_numRuns = sim_conf.get("runs")
    l_externalPlanned = l_config.getCfg("vehicle").get("weights").get("coop").get("externalplanned")
    l_externalVisit = l_config.getCfg("vehicle").get("weights").get("coop").get("externalvisit")
    l_selfVisit = l_config.getCfg("vehicle").get("weights").get("coop").get("selfvisit")

    l_runtime = runner.Runtime(l_config)

    l_mainresultdir = "results"

    if not os.path.isdir(l_mainresultdir):
        os.mkdir(l_mainresultdir)

    if sim_conf.get("resulttimestamped"):
        l_resultdir = time.strftime("%Y%m%d%H%M%S")
        if not os.path.isdir((os.path.join(l_mainresultdir, l_resultdir))):
            os.mkdir((os.path.join(l_mainresultdir, l_resultdir)))

    l_resultfile = "details-s" + str(l_numVehicles) + \
        "-p" + str(l_numParkingSpaces) + \
        "-c" + str(int(l_numCoopPhase2)) + \
        "-" + str(int(l_numCoopPhase3)) + \
        "-r" + str(l_numRuns) + \
        "-ep" + str(l_externalPlanned) + \
        "-ev" + str(l_externalVisit) + \
        "-sv" + str(l_selfVisit) + ".csv"

    l_summaryfile = "summary-s" + str(l_numVehicles) + \
        "-p" + str(l_numParkingSpaces) + \
        "-c" + str(int(l_numCoopPhase2)) + \
        "-" + str(int(l_numCoopPhase3)) + \
        "-r" + str(l_numRuns) + \
        "-ep" + str(l_externalPlanned) + \
        "-ev" + str(l_externalVisit) + \
        "-sv" + str(l_selfVisit) + ".txt"

    l_convergencefile = "convergence-s" + str(l_numVehicles) + \
        "-p" + str(l_numParkingSpaces) + \
        "-c" + str(int(l_numCoopPhase2)) + \
        "-" + str(int(l_numCoopPhase3)) + \
        "-r" + str(l_numRuns) + \
        "-ep" + str(l_externalPlanned) + \
        "-ev" + str(l_externalVisit) + \
        "-sv" + str(l_selfVisit) + ".csv"

    if sim_conf.get("resulttimestamped"):
        rf = open(os.path.join(l_mainresultdir, l_resultdir, l_resultfile), 'w')
        cf = open(os.path.join(l_mainresultdir, l_resultdir, l_convergencefile), 'w')
    else:
        rf = open(os.path.join(l_mainresultdir, l_resultfile), 'w')
        cf = open(os.path.join(l_mainresultdir, l_convergencefile), 'w')

    rf.write("numVeh,numParkSp,run,coopPhase2,coopPhase3,searchTime,walkTime,"
             "totalTime,searchDist,walkDist,totalDist,phase,"
             "maxSearchTimeThisRun,maxSearchDistThisRun\n")

    cf.write("run,avgSearchTime,avgWalkTime,avgTotalTime,avgSearchDist,"
             "avgWalkDist,avgTotalDist,avgParkPhase2,avgMaxSearchTime,"
             "avgMaxSearchDist\n")

    l_successfulruns = True
    for i_run in xrange(sim_conf.get("runs")):
        print("PID", os.getpid(), "RUNCFG:",
              sim_conf.get("runconfiguration"),
              "RUN:", i_run+1, "of", sim_conf.get("runs"))
        try:
            l_successes, l_searchTimes, l_walkingTimes, l_searchDistances, \
                    l_walkingDistances, l_searchPhases = l_runtime.run(i_run)

            for i_result in range(len(l_searchTimes)):
                rf.write(str(l_numVehicles) + ",")
                rf.write(str(l_numParkingSpaces) + ",")
                rf.write(str(i_run + 1) + ",")
                rf.write(str(l_numCoopPhase2) + ",")
                rf.write(str(l_numCoopPhase3) + ",")
                rf.write(str(l_searchTimes[i_result]) + ",")
                rf.write(str(l_walkingTimes[i_result]) + ",")
                rf.write(str((l_searchTimes[i_result]+l_walkingTimes[i_result])) + ",")
                rf.write(str(l_searchDistances[i_result]) + ",")
                rf.write(str(l_walkingDistances[i_result]) + ",")
                rf.write(str((l_searchDistances[i_result]+l_walkingDistances[i_result])) + ",")
                rf.write(str(l_searchPhases[i_result] ) + ",")
                rf.write(str(max(l_searchTimes)) + ",")
                rf.write(str(max(l_searchDistances)) + "\n")
                if l_searchPhases[i_result] == 2:
                    l_parkedInPhase2Sum += 1
                elif l_searchPhases[i_result] == 3:
                    l_parkedInPhase3Sum += 1
            l_successesSum += l_successes
            l_searchTimesSum += sum(l_searchTimes) #/ float(len(searchTimes))
            l_walkingTimesSum += sum(l_walkingTimes)
            l_totalTimesSum += sum(l_searchTimes) + sum(l_walkingTimes)
            l_searchDistancesSum += sum(l_searchDistances) #/ float(len(searchDistances))
            l_walkingDistancesSum += sum(l_walkingDistances)
            l_totalDistancesSum += (sum(l_searchDistances)+sum(l_walkingDistances))
            l_maxTimeSum += max(l_searchTimes)
            l_maxDistanceSum += max(l_searchDistances)

            l_searchTimesAvg = l_searchTimesSum / float(l_successesSum)
            l_walkingTimesAvg = l_walkingTimesSum / float(l_successesSum)
            l_totalTimesAvg = l_totalTimesSum / float(l_successesSum)
            l_searchDistancesAvg = l_searchDistancesSum / float(l_successesSum)
            l_walkingDistancesAvg = l_walkingDistancesSum / float(l_successesSum)
            l_totalDistancesAvg = l_totalDistancesSum / float(l_successesSum)
            l_parkedInPhase2Rate = l_parkedInPhase2Sum / float(l_successesSum)
            l_parkedInPhase3Rate = l_parkedInPhase3Sum / float(l_successesSum)
            l_maxTimeAvg = l_maxTimeSum / float(i_run+1)
            l_maxDistAvg = l_maxDistanceSum / float(i_run+1)

            cf.write(str(i_run+1) + ",")
            cf.write(str(l_searchTimesAvg) + ",")
            cf.write(str(l_walkingTimesAvg) + ",")
            cf.write(str(l_totalTimesAvg) + ",")
            cf.write(str(l_searchDistancesAvg) + ",")
            cf.write(str(l_walkingDistancesAvg) + ",")
            cf.write(str(l_totalDistancesAvg) + ",")
            cf.write(str(l_parkedInPhase2Rate*100) + ",")
            cf.write(str(l_maxTimeAvg) + ",")
            cf.write(str(l_maxDistAvg) + "\n")
        except BaseException as e:
            print("/!\\ gracefully shutting down simulation /!\\")
            print("/!\\ exception was {}".format(e))
            print("/!\\ stack trace:")
            print(traceback.format_exc())
            print("/!\ recovering...")
            # cleanup open file streams and write run cfg if not exists
            rf.close()
            cf.close()
            if not os.path.isfile(sim_conf.get("runconfiguration")):
                l_config.writeRunCfg()
            else:
                print("There exists a run cfg at {}! Refusing to overwrite it!".format(
                    os.path.isfile(sim_conf.get("runconfiguration"))))
            raise BaseException("/!\\ Unhandled exception in run id {} occurred /!\\".format(i_run))

    rf.close()
    cf.close()

    # write run cfg - make sure not to overwrite an existing one
    if not os.path.isfile(sim_conf.get("runconfiguration")):
        l_config.writeRunCfg()
    else:
        print("There exists a run cfg at {}! Refusing to overwrite it!".format(
            os.path.isfile(sim_conf.get("runconfiguration"))))

    if sim_conf.get("resulttimestamped"): 
        sf = open(os.path.join(l_mainresultdir, l_resultdir, l_summaryfile), 'w')
    else:
        sf = open(os.path.join(l_mainresultdir, l_summaryfile), 'w')

    l_successRate = 100 * l_successesSum/(sim_conf.get("runs") * sim_conf.get("vehicles"))

    sf.write("")
    sf.write("==== SUMMARY AFTER " + str(l_numRuns) + " RUNS ====\n")
    sf.write("parameters:          " + str(l_numVehicles) + " vehicles\n")
    sf.write("                     " + str(l_numParkingSpaces) + " parking spaces\n")
    sf.write("                     " + str(int(l_numCoopPhase2 * 100)) + " percent of drivers cooperate in phase 2\n")
    sf.write("                     " + str(int(l_numCoopPhase3 * 100)) + " percent of drivers cooperate in phase 3\n")
    if l_successesSum:
        l_searchTimesAvg = l_searchTimesSum / float(l_successesSum)
        l_walkingTimesAvg = l_walkingTimesSum / float(l_successesSum)
        l_totalTimesAvg = l_totalTimesSum / float(l_successesSum)
        l_searchDistancesAvg = l_searchDistancesSum / float(l_successesSum)
        l_walkingDistancesAvg = l_walkingDistancesSum / float(l_successesSum)
        l_totalDistancesAvg = l_totalDistancesSum / float(l_successesSum)
        l_parkedInPhase2Rate = l_parkedInPhase2Sum / float(l_successesSum)
        l_parkedInPhase3Rate = l_parkedInPhase3Sum / float(l_successesSum)
        l_maxTimeAvg = l_maxTimeSum / float(i_run + 1)
        l_maxDistAvg = l_maxDistanceSum / float(i_run + 1)
        sf.write("avg search time      " + str(l_searchTimesAvg) + " seconds\n")
        sf.write("avg walking time     " + str(l_walkingTimesAvg) + " seconds\n")
        sf.write("AVG TOTAL TIME       " + str(l_totalTimesAvg) + " SECONDS\n")
        sf.write("avg search distance  " + str(l_searchDistancesAvg) + " meters\n")
        sf.write("avg walking distance " + str(l_walkingDistancesAvg) + " meters\n")
        sf.write("AVG TOTAL DISTANCE   " + str(l_totalDistancesAvg) + " METERS\n")
        sf.write("parked in phase 2    " + str(l_parkedInPhase2Sum) + " vehicles (" + str(l_parkedInPhase2Rate*100) + ") percent\n")
        sf.write("parked in phase 3    " + str(l_parkedInPhase3Sum) + " vehicles (" + str(l_parkedInPhase3Rate*100) + ") percent\n")
        sf.write("avg max search time  " + str(l_maxTimeAvg) + " seconds\n")
        sf.write("avg max search dist  " + str(l_maxDistAvg) + " meters\n")
        sf.write("\n")
        sf.write("additional parameter info:\n")
        sf.write("externalplanned      " + str(l_externalPlanned) + "\n")
        sf.write("externalvisit        " + str(l_externalVisit) + "\n")
        sf.write("selfvisit            " + str(l_selfVisit) + "\n")
    sf.close()
