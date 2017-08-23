#!/usr/bin/env python3
# Author: Adam Light <la002@mail.cryst.bbk.ac.uk>
"""BEEP Scenario configuration management

This module provides utilities to read and write BEEP scenarios.
[TBD] write and XML
See phase1.py for details of configuration file layouts.

Example use:
    from scenario import Scenario

	f = open(file, "r")
    s = Scenario(f)
    for (subj in s.subjlist)
		...

The module contains the following public classes:
    - Scenario -- Builds the scenario specification for BEEP processing
"""
__version__ = '1.0'
__all__ = [
    'Scenario',
]

from typing import Iterable, Tuple, List
import re
from numpy import arange
from math import copysign
from pybeep import Vector, Quaternion
from io import TextIOWrapper
from distutils.util import strtobool
import logging as log

class Scenario:
	""" Reads a scenario configuration and provides access to its details

	Position Arguments:
    - spec -- text stream from which to read the scenario configuration file.
	Errors are logged via the standard logging module.
	
    Class Attributes:
    - no class attributes are part of the interface

    Class Methods:
    - no class methods are part of the interface

    Object Attributes:
    - subjlist -- list of subject PDB ids
	- locnlist -- list of subject locations, aligned to subjlist
		Each location list has same length, final position repeated as needed
    - crwdlist -- list of crowder PDB ids
	- proplist -- list of crowder proportions, aligned to crwdlist
		Each proportion list has same length, final value repeated as needed
    - centre -- Vector location of arena centre
    - radius -- radius of the arena
    - all others are implementation-dependent

    Object Methods:
    - [TBD]
    """

	# Private class attributes
	# Subject and Crowder RegExps to scan specification lines
	#_pdbrest = r'^\s*([0-9][a-z0-9A-Z]{3})'			# PDB RE string
	_pdbrest = r'^\s*([-a-z0-9\.A-Z]+)'				# PDB RE string
	_numrest = r'([+-]?[0-9]+\.?[0-9.]*)'			# Number RE string
	_seprest = r'\s*,\s*'							# Separator RE string
	_rngrest = (_numrest + _seprest)*2 + _numrest	# Number triad RE string
	_qutrest = (_numrest + _seprest)*3 + _numrest	# Number quad RE string
	_locrest = r'\(' + _rngrest + r'\)'				# Location RE string
	_lcrrest = (_locrest + _seprest)*2 + _locrest	# Location range RE string
	_rotrest = r'\(' + _qutrest + r'\)'				# Location RE string
	_rtrrest = (_rotrest + _seprest)*2 + _rotrest	# Location range RE string
								# as loc,loc,loc for start,end,increment
	# Subject specification RE
	_subjre = re.compile(_pdbrest +
						r'\s+location=' + _lcrrest +
						r'(?:\s+rotation=' + _rtrrest + r')?' +
						r'\s*$' # mass to follow
					)
	# Subject continuation specification RE
	_contre = re.compile(r'^\s+' + _lcrrest +
						r'(?:\s+rotation=' + _rtrrest + r')?' +
						r'\s*$' # mass to follow
					)
	# Crowder specification RE
	_crwdre = re.compile(_pdbrest +
						r'\s+proportion=' + _rngrest +
						r'\s*$' # mass to follow
					)
	# Parameter specification RE
	_parmre = re.compile(r'^\s*([A-Z][A-Za-z0-9]*)\s*=\s*(.*?)\s*$')

	# Default rotation is none
	_no_rotation = Quaternion(1,0,0,0)

	### Constructors

	# Constructor from non-XML specification text stream
	def __init__(self, spec: TextIOWrapper):
		# Public object attributes
		self.centre = Vector(0.0, 0.0, 0.0)
		self.radius = 0.0
		self.subjlist = list()
		self.crwdlist = list()
		self.proplist = list()
		self.locnlist = list()
		self.rotnlist = list()
		self.parameters = {
			'ArenaRadius': -1,
			'ArenaGrainSize': 0.0,
			'ArenaCentre': None,
			'CrowderRotate': True,
			'RhoProtein': 1.35,
			'RhoSolvent': 1.02,
			'MCwarmup': -1,
			'MCiter': -1,
			'Dsolvent': 80.0,
			'Dprotein': 2.0,
			'Kappa': 0.102,
			'GMREStol': 1e-6,
			'GMRESmaxit': 100,
			'QualPts': 4,
			'QuadPts': 0,
			'NbSize': 2200,
			'Planar': False
		}
		self._paramTypes = {
			'ArenaRadius': float,
			'ArenaGrainSize': float,
			'ArenaCentre': Vector,
			'CrowderRotate': strtobool,
			'RhoProtein': float,
			'RhoSolvent': float,
			'MCwarmup': int,
			'MCiter': int,
			'Dsolvent': float,
			'Dprotein': float,
			'Kappa': float,
			'GMREStol': float,
			'GMRESmaxit': int,
			'QualPts': int,
			'QuadPts': int,
			'NbSize': int,
			'Planar': bool
		}

		# Read scenario specification file
		lastmatch = 0 # Type of active configuration line last matched
		n = 0
		for line in spec:
			n += 1
			if len(line.split()) == 0 or line.split()[0][0] == '#':
				continue

			ml = self._subjre.match(line)
			if ml:
				lastmatch = 1	# Subject code
				self.subjlist += [ml.group(1)]
				self.locnlist += [Scenario._makeVectorRange(ml, 2)]
				self.rotnlist += [Scenario._makeQuaternionRange(ml, 11)]
				continue

			ml = self._contre.match(line)
			if ml:
				if lastmatch != 1:
					log.warning(f"Continuation line out of order, "
								f"line {n} -- ignored")
					continue
				self.locnlist[-1] += Scenario._makeVectorRange(ml, 1)
				self.rotnlist[-1] += Scenario._makeQuaternionRange(ml, 10)
				continue

			mc = self._crwdre.match(line)
			if mc:
				lastmatch = 2	# Crowder code
				self.crwdlist += [mc.group(1)]
				self.proplist += [Scenario._makeRange(mc, 2, 3, 4)]
				continue

			mp = self._parmre.match(line)
			if mp:
				lastmatch = 3	# Parameter code
				if mp.group(1) in self.parameters:
					self.parameters[mp.group(1)] = \
						self._paramTypes[mp.group(1)](mp.group(2))
				else:
					log.warning(f"Unrecognised parameter {mp.group(1)}, "
								f"line {n} -- ignored")
				log.debug(f"parameter {mp.group(1)}="
							f"{self.parameters[mp.group(1)]}, line {n}")
			else:
				log.warning(f"Invalid line [{n}] in scenario specification: "
							f"{line} -- ignored")

		# Extend the shorter lists so all are the same length
		llen = Scenario._makeSameLength(self.locnlist + self.rotnlist)
		plen = Scenario._makeSameLength(self.proplist)

		# Scenario specification checks
		# There has to be at least one subject protein
		if len(self.subjlist) == 0:
			log.error("No subject proteins in specification")
			exit(1)

		# Ensure crowder proportions are in [0,1]
		# Divide by the largest sum of proportions if outside this
		maxsum = max([0] + \
					 [sum([x[n] for x in self.proplist]) for n in range(plen)])
		if maxsum > 1:
			log.warning(f"Maximum proportions {maxsum} greater than one "
						"- corrected")
			self.proplist = [[y / maxsum for y in x] for x in self.proplist ]

		# Calculate the arena radius and the centre if not provided
		n = sum([len(locn) for locn in self.locnlist])
		maxsep = 0.0
		for i in range(len(self.locnlist)):
			for u in self.locnlist[i]:
				self.centre += u
				for j in range(i+1,len(self.locnlist)):
					for v in self.locnlist[j]:
						maxsep = max(maxsep, (u-v).length())
		if maxsep == 0.0:
			maxsep = 2/3  # to get a default of 1.0 below
		self.centre /= n
		if self.parameters['ArenaCentre'] != None:
			self.centre = self.parameters['ArenaCentre']
		if self.parameters['ArenaRadius'] <= 0:
			self.radius = 3*maxsep/2  # Default value
		else:
			self.radius = self.parameters['ArenaRadius']
		log.debug(f"Arena radius {self.radius}, centre {self.centre}")


	### Public methods


	### Private static methods

	@staticmethod
	def _makeRange(m: re.match, s: int, e: int, i: int) -> List[float]:
		# For a pythonesque ranging:
		#list(arange(float(m.group(s)),float(m.group(e)),float(m.group(i))))
		# BUT probably more expected ranging includes end point...

		# Check if there is no interval and ensure minimal return is start
		tol = 1e-3  # Attempt to allow for just missing the end
		sign = lambda x: copysign(1, x)
		(vs, ve, vi) = (float(m.group(s)), float(m.group(e)), float(m.group(i)))
		# Tolerate the interval being the wrong way round for the increment
		if vi == 0.0 or sign(vi)*(ve-vs) <= 0:  # arange will now be ok
			return [vs]
		return list(arange(vs, ve+(ve-vs)*tol, vi))

	# Assumes matches in the order: sx, sy, sz, ex, ey, ez, ix, iy, iz
	@staticmethod
	def _makeVectorRange(m: re.match, sx: int) -> List[Vector]:
		vr = [ Scenario._makeRange(m, n, n+3, n+6) for n in range(sx, sx+3) ]
		vl = max([len(r) for r in vr])  # Length of longest coordinate list
		# Extend each coordinate list to the length of the longest one
		vr = [vr[n]+[vr[n][-1]]*(vl-len(vr[n])) for n in range(3)]
		return [ Vector(vr[0][n], vr[1][n], vr[2][n]) for n in range(vl) ]

	# Assumes matches in the order: sa, sb, sc, sd, ea, eb, ec, ed, ia, ib, ...
	# Two changes from makeVector:  normalise and default
	@staticmethod
	def _makeQuaternionRange(m: re.match, sa: int) -> List[Quaternion]:
		# Check there is such a group first
		if m.group(sa+11) == None:
			# No such group, so default
			return [Scenario._no_rotation]
		# There is, so process it
		qr = [ Scenario._makeRange(m, n, n+4, n+8) for n in range(sa, sa+4) ]
		ql = max([len(r) for r in qr])  # Length of longest coordinate list
		# Extend each coordinate list to the length of the longest one
		qr = [qr[n]+[qr[n][-1]]*(ql-len(qr[n])) for n in range(4)]
		lq = [ Quaternion(qr[0][n], qr[1][n], qr[2][n], qr[3][n]) \
														for n in range(ql) ]
		# Normalise the quaternions (used for rotations only)
		for q in lq:
			q.normalise()
		return lq

	#>>> How to handle variable list of args?
	@staticmethod
	def _makeSameLength(ll: List[List[any]]) -> int:
		target = max([0] + [len(l) for l in ll])
		for l in ll:
			l += [l[-1]]*(target-len(l))
		return target

# No main program, so used for testing
if __name__== "__main__":
	sf = open("scenario-test.bsc", 'w')
	print("1xpb proportion=0,1,0.2", file=sf)
	print("3c7u location=(0,0,0),(1,2,3),(0.5,1,1.5)", file=sf)
	print("3t0c location=(0,0,0),(1,2,3),(0.5,1,1.5) "
		  "rotation=(-0.749932,-0.431118,-0.328328,0.379394),"
			"(-0.749932,-0.431118,-0.328328,0.379394),(1,0,0,0)", file=sf)
	sf.close()
	log.basicConfig(level=getattr(log, "DEBUG"))
	spec = open("scenario-test.bsc", 'r')
	log.debug("test spec opened")
	s = Scenario(spec)
	log.debug("scenario initialised")
	print("Subjects: ", s.subjlist)
	print("Locations: ", s.locnlist)
	print("Crowders: ", s.crwdlist)
	print("Proportions: ", s.proplist)
	print("Rotations: ", s.rotnlist)
	import os
	os.remove("scenario-test.bsc")



