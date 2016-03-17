#!/usr/bin/env python
from __future__ import print_function

import sys
import runner
import argparse

# Main entry point for the wrapper module.
# For now: starts repetitive simulation runs with identical parameters, 
# and presents the results afterwards.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process parameters for headless simulation runs.")
    parser.add_argument("-r","--runs", dest="runs", type=int, default=10, help="number of iterations to run")
    parser.add_argument("-p","--parkingspaces", dest="parkingspaces", type=int, default=5, help="number of available parking spaces")
    parser.add_argument("-s","--parking-search-vehicles", dest="psv", type=int, default=5, help="number of parking search vehicles")
    parser.add_argument("-c","--cooperative-ratio", dest="coopratio", type=float, default=0.0, help="cooperative driver ratio [0,1]")

    args = parser.parse_args()

    resultSum = 0
    for run in xrange(args.runs):
        print("RUN:", run, "OF", args.runs)
        result = runner.wrapper(args.parkingspaces, args.psv, args.coopratio)
        resultSum += result
    successRate = 100*resultSum/(args.runs*args.psv)
    print("")
    print("==== SUMMARY AFTER", args.runs, "RUNS ====")
    print("PARAMETERS:        ", args.parkingspaces, "parking spaces")
    print("                   ", args.psv, "searching vehicles")
    print("                   ", args.coopratio*100, "percent of drivers cooperate")
    print("TOTAL SUCCESS RATE:", successRate, "percent",
        "of cars found an available parking space")
    print("")