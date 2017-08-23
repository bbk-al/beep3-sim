#!/usr/bin/env python3
# Author: Adam Light <la002@mail.cryst.bbk.ac.uk>
"""MRes Bioinformatics with Systems Biology Project

Change the volume of a mesh.  The intended purpose is to investigate
the effect of volume on calculated BEEP energy.

Example use:
	expand.py -p 1.1 1.2 1.3 -f mesh.gts
where the list of numbers are the factors of expansion (or <1 for
contraction) required and mesh.gts is the initial file.  The output
files are named mesh-1.1x.gts, ...
"""
__version__ = '0.1'
__all__ = [
	'expand',
]

from typing import Iterable, Tuple
from sys import stdout
import logging as log
import re

#=============================================================================
# Global variables

#=============================================================================
# Functions
def vector(s):
	s.lstrip('( ')
	s.rstrip(' )')
	try:
		x, y, z = map(int, s.split(','))
		return x, y, z
	except:
		raise argparse.ArgumentTypeError("Direction must be x,y,z")

#=============================================================================
# Main
if __name__== "__main__":
	from sys import stdout
	import argparse
	
	# Set up command line parsing
	parser = argparse.ArgumentParser(description=\
				"Expand (or contract) the vertices of a GTS mesh.",
				epilog="Direction a,b,c gives (1+(p-1)a)x,(1+(p-1)b)y,....")
	# -loglevel
	parser.add_argument('--loglevel', metavar='(INFO|WARNING|ERROR)',
					dest='loglevel', required=False, default="INFO",
					help='minimum log level to capture: INFO, WARNING, ERROR')
	# --logfile
	parser.add_argument('--logfile', metavar='log', type=argparse.FileType('a'),
						dest='log', default=stdout, help='name of log file')
	# -p
	parser.add_argument('-p', metavar='PROPORTION', type=float, dest='p',
						nargs='+',
						help='expansion factors')
	# -d
	parser.add_argument('-d', metavar='X,Y,Z', type=vector, dest='d',
						default=(1,1,1),
						help='direction of expansion')
	# -f
	parser.add_argument('-f', metavar='FILE', type=str, dest='f',
						help='GTS file name', required=True)

	# Interpret arguments
	args = vars(parser.parse_args())
	loglevel = args['loglevel']
	logstream = args['log']
	proportion = args['p']
	direction = args['d']
	gts = args['f']

	# Set up logging - if to stdout, assume caller handles time and module name
	if logstream == stdout:
		fmt="%(levelname)s:%(message)s"
	else:
		fmt="%(asctime)s %(module)s %(levelname)s:%(message)s"
	log.basicConfig(stream=logstream, format=fmt,
					level=getattr(log, loglevel.upper()))

	# Set up REs
	nvrest = r"^([0-9]{1,10})\s+([0-9]{1,10})\s+([0-9]{1,10})\s+" \
				"GtsSurface GtsFace GtsEdge GtsVertex"
	floatrest = r"(-?[0-9\.]+(?:e-?[0-9]+)?)"
	vertrest = r"^"+floatrest+"\s+"+floatrest+"\s+"+floatrest+"\s*$"
	frootrest = r"^(.*)\.gts$"
	nvre = re.compile(nvrest)
	vertre = re.compile(vertrest)
	frootre = re.compile(frootrest)

	# For each proportion in the list expand the coordinates
	proplen = len(proportion)
	pf = list()
	m = frootre.search(gts)
	if (not m):
		print("Require a .gts extension")
		exit(1)
	froot = m.group(1)
	for p in range(proplen):
		pf.append(open(f"{froot}-{proportion[p]}x.gts", 'w'))
	with open(gts) as f:
		line = f.readline().strip()
		m = nvre.search(line)
		if (not m):
			print("Oops, this doesn't look like a gts file!")
			exit(1)
		try:
			nvert = int(m.group(1))
		except:
			print("Failed to interpret number of vertices")
			exit(1)
		
		# Prep for expansion and write out the header to each output file
		fmt = " ".join(["{:.6g}" for i in range(3)])
		ac = [0, 0, 0]
		ec = dict()
		for p in range(proplen):
			print(line.strip(), file=pf[p])
			ec[p] = list()

		# Multiply up each vertex
		for n in range(nvert):
			# Interpret the next line as a coordinate
			try:
				m = vertre.search(f.readline())
			except:
				print(f"Unexpected failure  at line {n+2}")
				exit(1)
			if (not m):
				print(f"Unexpected line format at line {n+2}")
				exit(1)
			try:
				c = [float(m.group(i)) for i in range(1,4)]
			except:
				print(f"Unexpected vertex format at line {n+2}")
				exit(1)

			# Maintain the average coodinate as the centre
			ac = [ac[i] + (c[i]-ac[i])/(n+1) for i in range(3)]

			# Expand the coordinate for each proportion
			for p in range(proplen):
				ec[p] += [[(1+(proportion[p]-1)*direction[i])*c[i] \
							for i in range(3)]]

		# Pause to adjust all the expanded coordinates and write them out
		print("Centred at "+fmt.format(*ac))
		for p in range(proplen):
			for ecv in ec[p]:
				ecv = [ecv[i]-ac[i]*((1+(proportion[p]-1)*direction[i])-1.0) \
						for i in range(3)]
				os = fmt.format(*ecv)
				print(os, file=pf[p])

		# Write out the remaining lines unchanged - all indices
		for line in f:
			for p in range(proplen):
				print(line.strip(), file=pf[p])

	# Close the files
	for p in range(proplen):
		pf[p].close()

