#!/usr/bin/env python3
# Author: Adam Light <la002@mail.cryst.bbk.ac.uk>
"""MRes Bioinformatics with Systems Biology Project

This script handles simplification of a molecular mesh.

Example use:
	simpli.py -i <gts> -o <gts-d>
with <gts> being a GTS file and <gts-d> the output GTS file.
"""
__version__ = '1.0'
__all__ = [
]

# imports
from sys import stdout
from os import environ, path, sep as pathsep
from pipeline import runCommand
import argparse
import re
import shutil
import logging as log

# Main program

# Set up command line parsing
parser = argparse.ArgumentParser(description=\
				'Simplify a surface representation.',
				epilog="If multiple PERCENT supplied, prepare.py is also " \
						"run for each case.")
# -i input gts file
parser.add_argument('-i', metavar='in-gts', dest='igts', required=True,
                    help='name of input gts file')
# -o output gts file
parser.add_argument('-o', metavar='out-gts', dest='ogts', required=True,
                    help='name of input gts file')
# --decimate target percentage decimation
parser.add_argument('--decimate', metavar="PERCENT", type=int,
                    nargs='+', required=False,
                    help='target percentage for decimation')
# --loglevel
parser.add_argument('--loglevel', metavar='(INFO|WARNING|ERROR)',
					dest='loglevel', default="INFO",
                    help='minimum log level to capture: INFO, WARNING, ERROR')
# --logfile
parser.add_argument('--logfile', metavar='log', type=argparse.FileType('a'),
					dest='log', default=stdout, help='name of log file')
# -d dummy run - only log the commands that would be run
parser.add_argument('-d', action='store_true',
					help='dummy run, log commands to be run only')

# Interpret arguments
args = vars(parser.parse_args())
decimation = [d for d in args['decimate']] if args['decimate'] != None else []
igts = args['igts']
ogts = args['ogts']
loglevel = args['loglevel']
logstream = args['log']
dummy = args['d']

# Set up logging - if to stdout, assume caller handles time and module name
if logstream == stdout:
	fmt="%(levelname)s:%(message)s"
else:
	fmt="%(asctime)s %(module)s %(levelname)s:%(message)s"
log.basicConfig(stream=logstream, format=fmt,
                level=getattr(log, loglevel.upper()))

# Output filename substitutions
extre = re.compile(r'(\.[^.]*)$')
here = environ['PWD']
if igts[0] != pathsep:
	igts = path.join(here, igts)
if ogts[0] != pathsep:
	ogts = path.join(here, ogts)
mlx = path.join(path.dirname(ogts), "decimate-replaced.mlx")

# Decimation
action = None  # Record what action has been taken
for dec in decimation:
	retcode = runCommand("cat decimate.mlx | "
           f"sed 's/TARGET_PERCENTAGE/{dec/100.0}/' >{mlx}",
           dummy)
	if retcode != 0:
		log.error(f"Failed to create decimate-replaced.mlx [{retcode}]")
		exit(1)

	odf = extre.sub(f"-{dec}" r'\1', ogts) if len(decimation) > 1 else ogts
	retcode = runCommand("xvfb-run meshlab/meshlabserver "
                         f"-i {igts} -o {odf} -s {mlx}",
                         dummy)
	if retcode != 0:
		log.error(f"Failed to run meshlab decimate-replaced.mlx [{retcode}]")
		exit(1)
	action = 1

	# Run prepare if there were multiple decimations, else leave to pipeline
	if len(decimation) > 1:
		xyzqr = extre.sub(f".xyzqr", ogts)
		mtz = extre.sub(f"-{dec}.mtz", ogts)
		retcode = runCommand(f"prepare.py {odf} {xyzqr} {mtz}", dummy)

# No action
if action == None:
	if igts != ogts and not dummy:
		shutil.copyfile(igts, ogts)

# Exit cleanly
exit(0)

