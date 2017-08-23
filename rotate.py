#!/usr/bin/env python3
# Author: Adam Light <la002@mail.cryst.bbk.ac.uk>
"""MRes Bioinformatics with Systems Biology Project

Rotate the coordinates of a subset of a PDB or xyzqr file.  The original
purpose was to set up boxed charges for instability testing, but it is
written like shift.py to allow for rotating charge subsets within a mesh.

Example use:
	rotate.py -i input-file -o output-file -f fmt -b pattern -e pattern ax1 ax2
fmt is either pdb or xyz and determines where on each line the coordinates
to be shifted are sought:  pdb works with pdb-like files, xyz with xyzr,
xyzqr and gts files.  The patterns provide the inclusive begin and
end lines on which to match.  The rotation is two axes, from which the
required normalised rotation from ax1 to ax2 is computed and applied to
the coordinates.
Note that an RE on a shell line needs suitable protection.  However, argparse
has trouble with leading '-', so an initial '#' is ignored in this script, i.e.
'#-5\.2860*\s+' is interpreted as '-5\.2860*\s+'.  Note that the #
is a comment character and must be escaped or quoted!
"""
__version__ = '0.1'
__all__ = [
	'shift',
]

from typing import Iterable, Tuple
from sys import stdout, stdin, stderr
from pybeep import Vector, Quaternion
from math import sqrt, fabs
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
		x, y, z = map(float, s.split(','))
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
				"Rotate the coordinates of a subset of PDB or xyz atoms.",
				epilog="Hint: # is ignored at the start of a pattern.")
	# -loglevel
	parser.add_argument('--loglevel', metavar='(INFO|WARNING|ERROR)',
					dest='loglevel', required=False, default="INFO",
					help="minimum log level to capture: INFO, WARNING, ERROR")
	# --logfile
	parser.add_argument('--logfile', metavar='log', type=argparse.FileType('a'),
						dest='log', default=stderr, help="name of log file")
	# -i
	parser.add_argument('-i', metavar='IN', type=argparse.FileType('r'),
						dest='in', default=stdin, help="name of input file")
	# -o
	parser.add_argument('-o', metavar='OUT', type=argparse.FileType('w'),
						dest='out', default=stdout, help="name of output file")
	# -f
	parser.add_argument('-f', metavar='FORMAT', type=str, dest='fmt',
						choices=('pdb', 'xyz'), default='pdb',
						help="format as pdb or xyz")
	# -b
	parser.add_argument('-b', metavar='PATTERN', type=str, dest='beg',
						default=".",
						help="the inclusive beginning line pattern")
	# -e
	parser.add_argument('-e', metavar='PATTERN', type=str, dest='end',
						default="!!!",
						help="the inclusive end line pattern")
	# Axes
	parser.add_argument('axis', metavar='AXIS', type=vector, nargs=2,
						help="rotate as from first axis to second")

	# Interpret arguments
	args = vars(parser.parse_args())
	loglevel = args['loglevel']
	logstream = args['log']
	ifs = args['in']
	ofs = args['out']
	if args['fmt'] == 'pdb':
		fmt = 0
		ofmt = str().join(["{:8.3f}" for i in range(3)]) # [-999.999,9999.999]
	elif args['fmt'] == 'xyz':
		fmt = 1
		ofmt = " ".join(["{:.6f}" for i in range(3)])
	else:
		print(f"This should not have happened - bad format {args['fmt']}")
		exit(1)
	beg = args['beg']
	end = args['end']
	ax = [Vector(*args['axis'][i]) for i in range(2)]
	qa = ax[0].cross(ax[1])	# a for axis
	qd = ax[0].dot(ax[1])	# d for dot
	# To get half-way, add (1,0,0,0) but ql not normalised yet, so adjust unit
	unit = sqrt(qd*qd + qa.length2())
	ql = Quaternion(unit + qd, qa.x, qa.y, qa.z)
	ql.normalise()

	# Set up logging - if to stdout, assume caller handles time and module name
	if logstream == stdout:
		lfmt="%(levelname)s:%(message)s"
	else:
		lfmt="%(asctime)s %(module)s %(levelname)s:%(message)s"
	log.basicConfig(stream=logstream, format=lfmt,
					level=getattr(log, loglevel.upper()))

	# Set up REs
	floatrest = r"(-?[0-9\.]+(?:e-?[0-9]+)?)"
	locrest = (floatrest+r"\s+")*3
	locre = re.compile(locrest)
	try:
		pat = beg[1:] if beg[0] == "#" else beg
		begre = re.compile(pat)
		pat = end[1:] if end[0] == "#" else end
		endre = re.compile(pat)
	except:
		print(f"Unable to interpret pattern \"{pat}\"")
		exit(1)

	state = 0
	lineno = 1
	c = Vector(0.0,0.0,0.0)	# centre of rotation, initially origin
	nc = 0			# number of coordinates to rotate
	rc = list()		# coordinates to rotate
	lines = list()	# first part of each line containing coordinates to rotate
	linee = list()	# last part of each line containing coordinates to rotate
	rest = list()	# remainder of file after vector subset
	for line in ifs:
		line = line[0:-1] # lose \n

		# Locate the beginning pattern
		if state == 0:
			m = begre.search(line)
			if m:
				state = 1
			else:
				print(line, file=ofs)
			
		# Add this line to the average for the centre of rotation
		if state == 1:
			# Test for end pattern
			m = endre.search(line)
			if m:
				state = 2

			# Extract coordinates
			if fmt == 0:
				test = [s.strip() for s in \
									[line[30:38], line[38:46], line[46:54]]]
			else:
				test = line.split()[0:3]

			# Sum coordinates
			try:
				rc.append(Vector(*[float(test[i]) for i in range(3)]))
			except:
				print(f"Failed to interpret float {test[i]} line {lineno}")
				exit(0)
			c = c + rc[-1]
			nc += 1

			# Save other parts of line
			if fmt == 0:
				lines.append(line[0:30])
				linee.append(line[54:])
			else:
				lines.append(str())
				linee.append(" ".join(line.split()[3:]))

		# Remainder of file
		elif state == 2:
			rest.append(line)

		lineno += 1

	# Rotate coordinates and output modified lines
	c /= nc	# Average is centre
	for i in range(nc):
		v = Vector(*rc[i])
		v.change_coordinate_frame(c, ql, c)
		if fmt == 0:
			rotc = ofmt.format(*v)
		else:
			rotc = ofmt.format(*v)+" "
		print(lines[i]+rotc+linee[i], file=ofs)
	for line in rest:
		print(line, file=ofs)

	# Close the files
	ifs.close()
	ofs.close()
