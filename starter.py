#!/usr/bin/env python
from __future__ import print_function

import argparse
import glob
import os
from multiprocessing import Pool
import time

if __name__ == "__main__":
    l_parser = argparse.ArgumentParser(description="get the directory containing config files.")
    l_parser.add_argument("-d", "--dir", dest="confdir", type=str, default="./")

    l_args = l_parser.parse_args()

    now = time.time()
    p = Pool(4)
    p.map(os.system, ["python3 parking.py --config " + x for x in glob.glob(l_args.confdir + "*.json")])
    p.terminate()

    print("Running time", (time.time() - now)/3600, "hours")
