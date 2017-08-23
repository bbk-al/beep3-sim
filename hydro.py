#!/usr/bin/env python3
# Author: Adam Light <la002@mail.cryst.bbk.ac.uk>
"""MRes Bioinformatics with Systems Biology Project

This script assigns hydrophobicities and Lennard-Jones parameters to an
xyzqr file.

Example use:
	hydro.py -a <hydrophobicities-file> -p <x.pqr> -o <o.xyzqr>
with <x.pqr> the pqr file (including H's), and <o.xyzqr> the output file.
The hydrophobicities-file has the format: RRR A PM1 HC
where RRR is the three-letter residue, A is the PDB file atom specifier,
PM1 is -1 for hydrophobic or +1 for hydrophilic, and HC is the hydrophobic
charge to assign (-0.5, +1.0 or +2.0);  PM1 is ignored.
"""
__version__ = '1.0'
__all__ = [
]

# imports
from typing import Iterable, Tuple, List, Dict
from sys import stdout
from os import environ, path, sep as pathsep
from math import log10, floor
import argparse
import logging as log

# Types
Coord = Tuple[float, float, float] # Coordinates x,y,z

# Utilities
def float4(fs: str) -> float:
	x = float(fs)
	return round(x, 3-int(floor(log10(abs(x)))))  # 4 sig fig

def length2(p1: Coord,p2: Coord) -> float:
	diff = [p1[i]-p2[i] for i in range(3)]
	return sum([dv*dv for dv in diff])

def rgAsString(rg: Dict) -> str:
	return rg[0].strip() + f" {rg[1]:.1f} {rg[2][0]:.2f} {rg[2][1]:.2f}"

def nearest(c: Coord, atomcoords: List[Coord]) -> Coord:
	minl2 = None
	rc = None
	for ac in atomcoords:
		l2 = length2(ac, c)
		if minl2 == None or l2 < minl2:
			minl2 = l2
			rc = ac
	return tuple(rc)


# Main program

# Set up command line parsing
parser = argparse.ArgumentParser(description=\
				'From PQR, assign hydrophobicities and LJ parameters to xyzqr.')
# -a hydrophobicities file
parser.add_argument('-a', metavar='hydrophobicities-file', dest='ahf',
					required=True,
                    help='name of hydrophobicities file')
# -p PQR file
parser.add_argument('-p', metavar='pqr-file', dest='pqrf', required=True,
                    help='name of pqr file (should include H)')
# -g GTS file - optional, used to exclude non-surface atoms
parser.add_argument('-g', metavar='gts-file', dest='gtsf', default=str(),
                    help='reference gts file used to exclude non-surface atoms')
# -s scale factor
parser.add_argument('-s', metavar='scale-factor', dest='scale', default=1.0,
					type=float,
                    help='factor by which to scale the charge')
# -o output xyzqr file
parser.add_argument('-o', metavar='out-xyzqr', dest='oxyzqr', required=True,
                    help='name of input xyzqr file')
# --loglevel
parser.add_argument('--loglevel', metavar='(INFO|WARNING|ERROR)',
					dest='loglevel', default="INFO",
                    help='minimum log level to capture: INFO, WARNING, ERROR')
# --logfile
parser.add_argument('--logfile', metavar='log', type=argparse.FileType('a'),
					dest='log', default=stdout, help='name of log file')

# Interpret arguments
args = vars(parser.parse_args())
ahf = args['ahf']
pqrf = args['pqrf']
gtsf = args['gtsf']
scale = args['scale']
oxyzqr = args['oxyzqr']
loglevel = args['loglevel']
logstream = args['log']

# Set up logging - if to stdout, assume caller handles time and module name
if logstream == stdout:
	fmt="%(levelname)s:%(message)s"
else:
	fmt="%(asctime)s %(module)s %(levelname)s:%(message)s"
log.basicConfig(stream=logstream, format=fmt,
                level=getattr(log, loglevel.upper()))

# Output filename substitutions
here = environ['PWD']
if ahf[0] != pathsep:
	ahf = path.join(here, ahf)
if pqrf[0] != pathsep:
	pqrf = path.join(here, pqrf)
if gtsf != str() and gtsf[0] != pathsep:
	gtsf = path.join(here, gtsf)
if oxyzqr[0] != pathsep:
	oxyzqr = path.join(here, oxyzqr)

# Read in the hydrophobicities
ah = dict()
with open(ahf, 'r') as f:
	n = 0
	for line in f:
		n += 1
		ll = line.split()
		if len(ll) == 0 or ll[0][0] == '#':
			continue
		if len(ll) < 3:
			log.error(f"Invalid line {n} in {ahf}: {line}")
			exit(1)
		try:
			ah[ll[0].upper()+ll[1].upper()] = float(ll[-1])
		except:
			log.error(f"Unexpected non-float field line{n} in {ahf}: {line}")
			exit(1)

# Set up the simple Lennard-Jones parameterisation
lj = dict(C=(3.40,0.10), H0=(2.53,0.02), N=(3.04,0.19), O=(3.25,0.17),	\
			S=(2.06,0.43), H1=(0.36,0.01))

# Read the pqr atoms
pqr = list()		# the PQR data
atomcoords = list()	# the PQR coords more conveniently
with open(pqrf, 'r') as f:
	n = 0								# line number for reporting
	het = 0								# for tracking groups of hetatms
	for line in f:
		n += 1
		if line[0:6] != 'ATOM  ' and line[0:6] != 'HETATM':
			continue
		# "Officially" the file format is white-space-separated fields:
		#	 Field_name Atom_number Atom_name Residue_name Chain_ID (optional)
		#		Residue_number X Y Z Charge Radius
		# (http://apbs-pdb2pqr.readthedocs.io/en/latest/formats/pqr.html)
		# But actually there are unspecified limits e.g. may have no white
		# space after HETATM: "attempt to preserve the PDB format
		# as much as possible" - whatever that means...
		if line[0:6] == 'HETATM':
			line = line[0:6] + " " + line[6:]
			het += 1
		else:
			het = 0
		ll = line.split()
		if len(ll) < 10:
			log.error(f"Insufficient fields at line {n} in {pqrf}: {line}")
			exit(1)
		elif len(ll) > 11:
			log.error(f"Additional fields at line {n} in {pqrf}: {line}")
			exit(1)
		elif len(ll) == 11:
			ll = ll[0:4] + ll[5:]	# Not interested in optional chain id here

		# Store the data
		try:
			ll = ll[0:5] + [float(ll[i]) for i in range(5,10)]
		except:
			log.error(f"Invalid coordinates at line {n} in {pqrf}")
			exit(1)
		pqr.append((het,ll))
		if het == 0:
			atomcoords.append(ll[5:8])

# Read the reference gts file if there is one
surface = set()
if gtsf != str():
	with open(gtsf, 'r') as f:
		n = 0
		nvert = 0
		for line in f:
			if n == 0:
				try:
					nvert = int(line.split()[0])
				except:
					log.error(f"Invalid first line in {gtsf}")
					exit(1)
			elif n <= nvert:
				gl = line.split()
				try:
					c = [float(gl[i]) for i in range(3)]
				except:
					log.error(f"Invalid line {n+1} in {gtsf}")
					exit(1)
				# Store the nearest atom coords in the surface set
				surface.add(nearest(c, atomcoords))
			else:
				break # rest of gts file is irrelevant
			n += 1

# Assign hydrophobicities and LJ parameters and output the results
out = open(oxyzqr, 'w')
(residue, chain) = (0, 0)			# for tracking group in sequence
(resgrp,atmord) = (dict(),list())	# for grouping output with order kept
n = 0
for (het,ll) in pqr:
	n += 1

	# Scale the charge
	ll[8] = ll[8]*scale
	# Convert xyzqr info to what seems to be the xyzqr file format:
	info = " ".join([f"{ll[i]:.6f}" for i in range(5,10)]).strip()
	# Grab the keys
	res = ll[3].strip().upper()
	atom = ll[2].strip().upper()

	# The output has to be by residue because of terminal corrections
	# Check for start of a residue - output the current one
	if (het == 0 and atom == 'N') or het == 1:
		# Output the current residue's extended lines
		for a in atmord:
			print(rgAsString(resgrp[a]), file=out)

		# Reset the residue
		(resgrp,atmord) = (dict(),list())
		if het == 0:
			if residue == 0:
				chain += 1
			residue += 1

	# Spit out HETATMs directly and get the next line
	if het > 0:
		print(rgAsString([info, 0.0, (0.0, 0.0)]), file=out)
		continue

	# Construct L-J key
	ljk = atom[0]
	if ljk == 'H':
		ljk += '0' if ll[9] == 0.0 else '1'
	if ljk not in lj:
		log.error(f"Unrecognised atom at line {n} in {pqrf}: {ll}")
		exit(1)
		
	# Group ATOM residues - provisional assignment
	resgrp[atom] = [info, 0.0, lj[ljk]]  # important 0.0 invalid
	atmord += [atom]
	# Ignore non-surface atoms
	if gtsf != str() and tuple(ll[5:8]) not in surface:
		pass
	# For an initial NH3+ all four atoms are +2.0
	elif residue == 1 and (atom == 'H2' or atom == 'H3'):
		for a in ['N','H','H2','H3']:	# H2,3 have to come after N,H
			if a in resgrp:
				resgrp[a][1] = 2.0
	# For a final COO- (OXT but not HXT) all three atoms are +2.0
	elif atom == 'OXT':
		for a in ['C','O','OXT']:		# OXT has to come after C,O
			if a in resgrp:
				resgrp[a][1] = 2.0
	# Histidine can be weakly positive if it has an HE2
	elif res == 'HIS' and atom == 'HE2':
		for a in ['NE2','HE2']:			# Hs come after all others
			if a in resgrp:
				resgrp[a][1] = 2.0
	# Otherwise assign specified hydrophobicity for now
	elif (res+atom) in ah and resgrp[atom][1] == 0.0:
		resgrp[atom][1] = ah[res+atom]
	else:
		log.error(f"Unrecognised or duplicate atom at line {n} in {pqrf}: "\
					f"{ll}")
		exit(1)
	# And move to the next chain, if there is one
	if atom == 'OXT' or atom == 'HXT':
		residue = 0

# Output any final residue's extended lines
for a in atmord:
	print(rgAsString(resgrp[a]), file=out)

out.close()

# Exit cleanly
exit(0)

