#!/usr/bin/env python

import argparse
import glob, os
from multiprocessing import Pool

l_parser = argparse.ArgumentParser(description="get the directory containing config files.")
l_parser.add_argument("-d" ,"--dir", dest="confdir", type=str, default="./")

l_args = l_parser.parse_args()

p = Pool()
p.map(os.system, ["python parking.py --config " + x for x in glob.glob(l_args.confdir + "*.json")])
p.terminate()
