#!/usr/bin/env python3
# Author: Adam Light <la002@mail.cryst.bbk.ac.uk>
"""MRes Bioinformatics with Systems Biology Project

Shift the coordinates of a subset of a PDB or xyzqr file.  The intended
purpose is to investigate the effect on BEEP of a combined mesh for a
bound complex as opposed to separate meshes.

Example use:
	shift.py -i input-file -o output-file -f fmt -b pattern -e pattern shift
fmt is either pdb or xyz and determines where on each line the coordinates
to be shifted are sought:  pdb works with pdb-like files, xyz with xyzr,
xyzqr and gts files.  The patterns provide the inclusive begin and
end lines on which to match.  The shift is three numbers for x, y and z shifts.
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
import logging as log
import re

#=============================================================================
# Global variables

#=============================================================================
# Functions

#=============================================================================
# Main
if __name__== "__main__":
	from sys import stdout
	import argparse
	
	# Set up command line parsing
	parser = argparse.ArgumentParser(description=\
				"Shift the coordinates of a subset of PDB or xyz atoms.",
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
	# shift
	argshift = ['x', 'y', 'z']
	for i in range(len(argshift)):
		parser.add_argument(argshift[i], metavar=argshift[i].upper(),
							type=float,
							help="the "+argshift[i]+" shift to apply")

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
	shift = [0.0]*3
	for i in range(3):
		try:
			shift[i] = float(args[argshift[i]])
		except:
			print(f"Bad shift {args[argshift[i]]}")
			exit(1)

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
	for line in ifs:
		line = line[0:-1] # lose \n

		# Locate the beginning pattern
		if state == 0:
			m = begre.search(line)
			if m:
				state = 1
		# Shift this line
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

			# Shift coordinates
			c = [0.0]*3
			for i in range(3):
				try:
					c[i] = float(test[i])
				except:
					print(f"Failed to interpret float {test[i]} line {lineno}")
					exit(0)
				c[i] += shift[i]

			# Output revised line
			if fmt == 0:
				line = line[0:30]+ofmt.format(*c)+line[54:]
			else:
				line = ofmt.format(*c)+" "+" ".join(line.split()[3:])

		# Output line
		print(line, file=ofs)
		lineno += 1

	# Close the files
	ifs.close()
	ofs.close()
