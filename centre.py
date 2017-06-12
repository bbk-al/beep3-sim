#!/usr/bin/env python3
# Author: Adam Light <la002@mail.cryst.bbk.ac.uk>
"""MRes Bioinformatics with Systems Biology Project

This module provides utilities to calculate the mass and centre of mass
of a PDB structure, and the axis and steps between two PDB structures.

Example use:
	centre pdb1 [pdb2]
where <pdbN> is the path of a PDB file, preferably including H atoms.

This module contains the following functions:
	- calculate_mass
"""
#TODO documentation referenced above!
__version__ = '0.1'
__all__ = [
	'calculate_mass',
]

from typing import Iterable, Tuple
from pybeep import Vector
import logging as log

#=============================================================================
# Global variables
MolMass = dict( C=12.011, N=14.007, O=15.999, H=1.0079, S=32.065 )

#=============================================================================
# Functions
# Calculate mass and centre of protein from PDB-H file
def calculate_mass(pdb: str) -> Tuple[float,Vector]:
	mass = 0.0
	com = Vector(0,0,0)
	atom = "none"
	try:
		with open(pdb) as f:
			for line in f:
				if line[0:6] != "ATOM  ":
					continue
				pos = Vector(float(line[31:39]), float(line[39:47]),
							 float(line[47:55]))
				atom = line[77] if line[76] == " " else line[76:78]
				matom = MolMass[atom]
				mass += matom
				com -= (com-pos)*matom/mass
	except Exception as e:
		log.warning(f"Zero mass assumed for {pdb} atom {atom} because {e}")
	return (mass,com)

def calculate_charge(qr: str) -> float:
	charge = 0.0
	(c, t) = (0.0, charge) # Kahan correction
	try:
		with open(qr) as f:
			for line in f:
				field = line.split(' ')
				x = float(field[3])
				y = x - c
				charge = t + y
				c = (charge - t) - y
				t = charge
	except:
		return "Unknown"
	return f"{charge:.3f}"


#=============================================================================
# Main
if __name__== "__main__":
	from sys import stdout
	import argparse
	
	# Set up command line parsing
	parser = argparse.ArgumentParser(description=\
					'Calculate the energy of a complete scenario of '
					'subject and crowder proteins.')
	# -loglevel
	parser.add_argument('--loglevel', metavar='(INFO|WARNING|ERROR)',
					dest='loglevel', required=False, default="INFO",
					help='minimum log level to capture: INFO, WARNING, ERROR')
	# --logfile
	parser.add_argument('--logfile', metavar='log', type=argparse.FileType('a'),
						dest='log', default=stdout, help='name of log file')
	# -n
	parser.add_argument('-n', metavar='n', type=int, dest='n', default=1,
						help='number of steps along axis')
	# -s
	parser.add_argument('-s', metavar='s', type=float, dest='s', default=0.0,
						help='step size')
	# PDB Ids
	parser.add_argument('pdblist', metavar='PDB-Id',
						nargs='+',
						help='list of PDB files, exactly two for axis data')

	# Interpret arguments
	args = vars(parser.parse_args())
	loglevel = args['loglevel']
	logstream = args['log']
	steps = args['n']-1
	stepsize = args['s']
	pdblist = args['pdblist']

	# Set up logging - if to stdout, assume caller handles time and module name
	if logstream == stdout:
		fmt="%(levelname)s:%(message)s"
	else:
		fmt="%(asctime)s %(module)s %(levelname)s:%(message)s"
	log.basicConfig(stream=logstream, format=fmt,
					level=getattr(log, loglevel.upper()))

	# For each PDB file on the list, calculate mass and centre
	pdbnum = len(pdblist)
	(mass,com) = ([None]*pdbnum,[None]*pdbnum)
	for n in range(pdbnum):
		(mass[n],com[n]) = calculate_mass(pdblist[n])

		# And try calculating net charge
		charge = "Unknown"
		if pdblist[n][-5:] == "H.pdb":
			xyzqr = pdblist[n][0:-5] + ".xyzqr"
			charge = f"{calculate_charge(xyzqr)}"

		# Output findings
		print(f"{pdblist[n]} mass {mass[n]} centre {com[n]} charge {charge}")

	# If there are exactly two PDB files, provide the scenario axis data
	if pdbnum == 2:
		axis = com[1]-com[0]
		axis.normalise()
		coms = com[1]+axis*(10.165+steps*stepsize)
		come = com[1]+axis*10.165
		comi = axis*(-stepsize)
		print("")
		print("Axis information:")
		vec = [com[0],coms,come,comi]
		vecnum = len(vec)
		vecstr = [None]*vecnum
		for i in range(vecnum):
			vecstr[i] = f"({vec[i].x:.4f},{vec[i].y:.4f},{vec[i].z:.4f})"
		print(f"{pdblist[0]}={vecstr[0]},{vecstr[0]},(2,0,0)")
		print(f"{pdblist[1]}={vecstr[1]},{vecstr[2]},{vecstr[3]}")

