#!/usr/bin/env python3
# Author: Adam Light <la002@mail.cryst.bbk.ac.uk>
"""MRes Bioinformatics with Systems Biology Project

This module provides the capability to run a complete scenario consisting
of specified subject and crowder proteins, crowder concentration, and
subject separation.  The output is the calculated energy.

Example use:
	phase1 -s <spec>
where <spec> is the path of a file containing lines of the form:
	<pdb> location=<VectorRange> [rotation=<XYZR>] [mass=<float>]
	<pdb> proportion=<floatRange> [mass=<float>]
with <pdb> being a PDB Id.  Comment lines begin with '#'.

All spatial dimensions are measured in Angstroms.
A location is specified for subject proteins, and scenarios are run
for each Vector in the VectorRange specification.  If the VectorRanges are
of differing lengths then scenarios are run for the maximum length with
the other location ranges being cycled.
[TBD] The specified rotation is applied to the associated subject protein.
A proportion is specified for crowders, being the proportion of
molecules amongst crowders.  These are placed with random,
non-overlapping locations and orientations.
[TBD] If a mass is specified this is in kDa;  otherwise this is
estimated from the protein mesh volume and the RhoProtein density
parameter.  Masses are only used to report mass proportions achieved.
The crowding scenarios are run using a Metropolis-Hastings Monte
Carlo algorithm to obtain stable energy levels.

In addition, the specification file may include a number of parameters
of the form <parameter>=<value>:

Parameter	& Meaning						& Default value
ArenaRadius	& Radius of arena				& 3x maximum subject separation	\\
RhoProtein	& Default density of protein	& 1.35 (g/cm3)	\\
RhoSolvent	& Density of solvent			& 1.02 (g/cm3)	\\
MCwarmup	& Discounted MC iterations		& 10x crowder count	\\
MCiter		& Maximum total MC iterations	& 40x crowder count	\\
DSolvent	& Dielectric for solvent		& 80.0	\\
DProtein	& Dielectric for protein		& 2.0	\\
Kappa		& Debye screening parameter*	& 0.102	\\
GMREStol	& GMRES solver tolerance*		& 1e-6	\\
GMRESmaxit	& GMRES max iterations*			& 100	\\
QualPts		& Qualocation points*			& 0	\\
QuadPts		& Quadrature points*			& 0	\\
NbSize		& BEM neighbourhood size*		& 2200	\\

* See documentation for explanation.
[TBD] These features are not currently implemented.

This module contains the following functions:
	- tbd -- tbd
"""
#TODO documentation referenced above!
__version__ = '0.1'
__all__ = [
	'tbd',
]

# imports
from sys import stdout,getsizeof,getallocatedblocks
from resource import getrusage,RUSAGE_SELF
import os.path as path
from typing import Iterable, Tuple
from math import exp
import argparse
import re
from pybeep import BEEP, Mesh, Vector, Quaternion
from scenario import Scenario
from packed_sphere_arena import PackedSphereArena
from pipeline import readPipeline, runPipeline
import random
import logging as log
from centre import calculate_mass
import gc

# User-defined types

#=============================================================================
# Global variables
RT = 0.0083144598 * 300 # kJ K-1 mol-1 * K as BEEP produces kJ mol-1


#=============================================================================
# Functions
	
#=============================================================================
# Utility classes and helpers
# Results data storage and dumping
from pickle import Pickler

class ResultsData:
	def __init__(self, f): #f is _io.BufferedWriter
		self._exprs = list()
		self._types = list()
		self._out = f
		self._results = Pickler(f)

	def add(self, s: str) -> None:
		self._exprs += [(0,s)]

	def addVectorList(self, s: str) -> None:
		self._exprs += [(1,s)]

	def addVectorDict(self, s: str) -> None:
		self._exprs += [(-1,s)]

	def addQuaternionList(self, s: str) -> None:
		self._exprs += [(2,s)]

	def addQuaternionDict(self, s: str) -> None:
		self._exprs += [(-2,s)]

	# Used to write the header record
	def write(self, record):
		self._results.dump(record)

	def dump(self):
		self._results.clear_memo()
		for e in self._exprs:
			if e[0] == 0:
				self._results.dump(eval(e[1]))
			elif e[0] == -1:
				vl = vectorDict(eval(e[1]))
				self._results.dump((len(vl), vl))
			elif e[0] == 1:
				vl = vectorList(eval(e[1]))
				self._results.dump((len(vl), vl))
			elif e[0] == -2:
				ql = quaternionDict(eval(e[1]))
				self._results.dump((len(ql), ql))
			elif e[0] == 2:
				ql = quaternionList(eval(e[1]))
				self._results.dump((len(ql), ql))
		self._out.flush()

def vectorList(vl):
	return [(v.x, v.y, v.z) for v in vl]

def vectorDict(vl):
	return [(vl[v].x, vl[v].y, vl[v].z) for v in vl]

def quaternionList(ql):
	return [(q.a, q.b, q.c, q.d) for q in ql]

def quaternionDict(ql):
	return [(ql[q].a, ql[q].b, ql[q].c, ql[q].d) for q in ql]


#=============================================================================
# Main program

# Set up command line parsing
parser = argparse.ArgumentParser(description=\
				'Calculate the energy of a complete scenario of '
				'subject and crowder proteins.')
# -s scenario spec
parser.add_argument('-s', metavar='spec', type=argparse.FileType('r'),
					dest='spec', required=True,
                    help='name of scenario specification file')
# -p pipeline config file
parser.add_argument('-p', metavar='pipeline', type=argparse.FileType('r'),
					dest='pipeline', default=open("pipeline.cfg"),
                    help='name of pipeline specification file')
# -o output file
parser.add_argument('-o', metavar='outfile', type=argparse.FileType('wb'),
                    dest='outfile', default=stdout,
                    help='name of results file')
# -w working directory
parser.add_argument('-w', metavar='work-dir',
					dest='workdir', default=".",
                    help='working directory (and location of PDB files)')
#[TBD] -a <arena-type> for (PackedSphere|...)
# --loglevel
parser.add_argument('--loglevel', metavar='(INFO|WARNING|ERROR)',
					dest='loglevel', default="INFO",
                    help='minimum log level to capture: INFO, WARNING, ERROR')
# -f force refresh of pipeline
parser.add_argument('-f', action='store_true', dest='refresh',
                    help='force refresh of whole pipeline')

# Interpret arguments
args = vars(parser.parse_args())
spec = args['spec']
pcfg = args['pipeline']
refresh = args['refresh']
loglevel = args['loglevel']
workdir=args['workdir']

# Set up output
out = args['outfile']
results = ResultsData(out)
results.add("(l, r, it, this_energy)")
results.addVectorList("[scenario.locnlist[s][l] for s in range(cbase)]")
results.addVectorDict("cloc")
results.addQuaternionDict("crot")
results.add("(c, next_energy, vectorList([location]), "
			"quaternionList([rotation]), status)")


# Set up logging
log.basicConfig(filename=path.join(workdir,"phase1.log"), filemode='w',
                format="%(asctime)s %(module)s %(levelname)s:%(message)s",
                level=getattr(log, loglevel.upper()))
log.info("Arguments parsed")

#-----------------------------------------------------------------------------
# Read configuration file
scenario = Scenario(spec)
spec.close()
log.info("Scenario configuration read")

# Read pipeline configuration
pipeline = readPipeline(pcfg)
pcfg.close()
log.info("Pipeline configuration read")

# Initialise BEEP
beep = BEEP(scenario.parameters['Dsolvent'], scenario.parameters['Kappa'],
            scenario.parameters['QuadPts'], scenario.parameters['QualPts'],
            scenario.parameters['NbSize'], scenario.parameters['Planar'])
log.info("BEEP initialised: Dsolvent=%f, Kappa=%f, QuadPts=%d, QualPts=%d,"
		 "NbSize=%d, Planar=%r" % ( \
			scenario.parameters['Dsolvent'], scenario.parameters['Kappa'],
            scenario.parameters['QuadPts'], scenario.parameters['QualPts'],
            scenario.parameters['NbSize'], scenario.parameters['Planar']))

# Run pipeline for each PDB Id to get meshes and load into BEEP library
masslist = dict()
pvollist = dict()
ressubj = list()	# To hold subject results header info
rescrwd = list()	# To hold crowder results header info
idx = 0
crowding = False
maxcr = 0.0  # Maximum crowder radius
for pdbid in scenario.subjlist + [str()] + scenario.crwdlist:
	if pdbid == str():
		crowding = True
		continue
	mtz = path.join(workdir,pdbid) + ".mtz"
	if not path.isfile(mtz):
		retcode = runPipeline(pipeline, path.join(workdir,pdbid), refresh)
		if retcode < len(pipeline) - 1:
			print(retcode, len(pipeline))
			log.error("Failed to generate mesh files, exiting")
			exit(1)
	# Load the mesh into the BEEP library, ignore Mesh object return
	# An exception will be thrown if the load fails
	m = beep.load_library_mesh(mtz)

	# Get mass and volume data
	(masslist[idx],mc) = calculate_mass(path.join(workdir,pdbid) + "H.pdb")
	pvollist[idx] = m.calculate_volume()
	radius = m.get_radius()
	#mc = m.get_centre()
	log.debug(f"Load subject {pdbid}, mass {masslist[idx]:.3f}, "
			  f"volume {pvollist[idx]:.3f}, radius {radius:.3f}, centre {mc}")
	if crowding:
		rescrwd += [(pdbid, radius)]
		maxcr = max(maxcr, radius)
	else:
		ressubj += [(pdbid, radius)]
	idx +=1
log.info("BEEP library loaded")

# Calculate subject protein mass and volume, needed for reporting later
msubj = sum([masslist[s] for s in range(len(scenario.subjlist))])
vsubj = sum([pvollist[s] for s in range(len(scenario.subjlist))])

# Output results header
results.write(["phase1.py", 4, ressubj, rescrwd])

# Arena initialisation
# Calculate packed sphere radius
#[TBD] Futures...minimum separation => enlarged spheres by sep/2
cbase = len(scenario.subjlist)  # crowder ids start after subjects
#a = 0.0  # packed sphere radius
#for n in range(cbase, cbase+len(scenario.crwdlist)):
#	m = beep.get_library_mesh(n);
#	r = m.get_radius()
#	a = max(a, r)
a = maxcr  # packed sphere radius
if a == 0.0:
	a = scenario.parameters['ArenaGrainSize']
if a == 0.0 or a > scenario.radius:	# Having no crowders is ok, use arena size
	a = scenario.radius

# Build the arena
psa = PackedSphereArena(a, scenario.radius, scenario.centre)
log.info(f"Arena initialised with {psa.capacity()} packed spheres")

# Load BEEP with subject mesh instances as these persist
origin = Vector(0,0,0)
no_rotation = Quaternion(1,0,0,0)
for s in range(cbase):
	log.debug(f"Insert mesh instance {s}")
	m = beep.insert_mesh_instance(s, scenario.locnlist[s][0],
								no_rotation, scenario.parameters['Dprotein'])
log.info("Subject instances created, "
		 f"Dprotein={scenario.parameters['Dprotein']}")

# Outline of the rest of the program:
# For each subject-location
	# Clear crowder instances
	# Move the subjects to new locations
	# For each crowder count
		# Load the crowder instances
		# MCMC loop: BEEP, propose crowder instance moves
leakcount = 100;
		
# Run the scenario for each subject protein location
# -- location ranges have been set by Scenario to be of equal length
locnLen = len(scenario.locnlist[0])
rotnLen = [len(r) for r in scenario.rotnlist]
for l in range(locnLen):
	log.info(f"Initialising subjects for location {l}")

	# Clear the arena of all occupants and instances
	psa.clear()

	# Set up the subjects for this run
	occErr = False
	for s in range(cbase):
		# Translate to specified position, rotate by amount specified
		log.debug(f"Move subject {s} to location {l}")
		gc.collect()
		log.debug(f"PreProcess size {getrusage(RUSAGE_SELF).ru_maxrss/1000}, "
				  f"python size {getallocatedblocks()}")
		for i in range(leakcount):
			beep.move_mesh_instance(s, scenario.locnlist[s][l],
									scenario.rotnlist[s][l],
									scenario.parameters['Dprotein'])
		gc.collect()
		log.debug(f"PostProcess size {getrusage(RUSAGE_SELF).ru_maxrss/1000}, "
				  f"python size {getallocatedblocks()}")
		# Arena subject allocation
		log.info(f"Placed subject {scenario.subjlist[s]} "
				 f"at {scenario.locnlist[s][l]}, "
				 f"rotation {scenario.rotnlist[s][l]}")
		try:
			psa.insertMesh(beep.get_mesh_instance(s), 1, s) # Type 1 for subjects
		except:
			#TODO improve error messages!
			log.error(f"Occupancy error for mesh {s} location {l}")
			occErr = True
			break
	if occErr:
		log.warning(f"Abandoning location {l}")
		continue

	# Can now set the crowd counts as the scenario is staged
	#[TBD] add limitCrowdSize as a parameter for non-packed-sphere arena?
	# Number of unoccupied packed spheres sets upper limit on crowding
	climit = psa.capacity()
	# Convert proportions to counts
	crwdsize = [[int(v*climit) for v in p] for p in scenario.proplist]

	# Generate crowds -- this is incremental so no clearing of BEEP mesh
	# For each crowd size specification
	rlen = len(crwdsize[0]) if len(crwdsize) > 0 else 1
	log.info(f"Run count {rlen} with crowd limit {climit}")
	for r in range(rlen):
		# Clear the BEEP crowders, but leave the subject instances alone
		#[TBD] can this be improved to incrementally add/remove?
		log.debug(f"Clear mesh instances from {cbase} onwards")
		psa.clear(-1)  # Clear all type -1 occupants
		beep.clear_mesh_instances(cbase, -1)  # Clear after end of subjlist
		cloc = dict()	# crowder location in BEEP keyed by cid
		crot = dict()	# crowder rotation in BEEP keyed by cid
		cref = dict()	# crowder reference from PSA keyed by cid

		# Set up the crowders for this run
		log.info(f"Initialising crowders for run {r}")
		cid = cbase
		for c in range(len(crwdsize)):  # Same length as crwdlist, but safer
			cc = crwdsize[c][r]  # count for this crowder
			log.debug(f"Initialising {cc} {scenario.crwdlist[c]} crowders for run {r}")
			for i in range(cc):
				vc = psa.capacity()  # vacant capacity
				if vc == 0:
					log.error("No more room for crowders!")
					raise ValueError
				# Occupy a random location
				v = random.randrange(vc)  # Vacant slot
				(cloc[cid], cref[cid]) = psa.occupy(v, -1, cid)  # -1 for crowd
				crot[cid] = Quaternion.rand()
				# Add to BEEP
				log.debug(f"Insert {scenario.crwdlist[c]} instance {cid} "
						  f"at {cloc[cid]}, rotation {crot[cid]}")
				m = beep.insert_mesh_instance(cbase+c, cloc[cid], crot[cid],
				                          scenario.parameters['Dprotein'])
				# Next crowder instance
				cid += 1

		# Report crowd configuration
		#TODO

		# Report mass proportions...
		mass = msubj + sum([masslist[cbase+c]*crwdsize[c][r] \
								for c in range(len(crwdsize))])
		pvol = vsubj + sum([pvollist[cbase+c]*crwdsize[c][r] \
								for c in range(len(crwdsize))])
		if pvol > psa.volume:
			pvol = psa.volume
		log.debug(f"mass={mass:.1f}, pvol={pvol:.1f}, "
				  f"psa.volume={psa.volume:.1f}")
		mprop = mass /  \
				(mass + (psa.volume - pvol)*scenario.parameters['RhoSolvent'])
		log.info(f"Protein mass proportion is {100*mprop:4.2f}%")

		# Drop out a kinemage of the starting point
		#beep.kinemage(path.join(workdir, f"{l}-{r}-start.kin"))

		# Metropolis-Hastings MC: find stable energy
		log.info("Starting MC...")
		warmup = scenario.parameters['MCwarmup'] if \
			scenario.parameters['MCwarmup'] >= 0 else 10*cid
		iters = scenario.parameters['MCiter'] if \
			scenario.parameters['MCiter'] >= 0 else 40*cid
		log.info(f"Iterations count {iters}")

		# Calculate initial energy
		log.info(f"BEEP solve... initial")
		beep.reset_fh_vals()
		beep.solve(scenario.parameters['GMREStol'], \
				   scenario.parameters['GMRESmaxit'])
		#beep.reset_library_fh_vals()
		this_energy = beep.calculate_energies()
		gc.collect()
		log.debug(f"Process size {getrusage(RUSAGE_SELF).ru_maxrss/1000}, "
				  f"python size {getallocatedblocks()}")
 
		# Run iterations
		(c, location, rotation) = (-1, origin, no_rotation)  # defaults
		for it in range(iters):
			# Propose a move
			# Pick a crowder at random, random move and rotate
			if cid > cbase:
				c = random.randrange(cbase, cid)
				vc = psa.capacity()  # vacant capacity
				if vc > 0:	# move if there is room, else rotate only
					v = random.randrange(vc)  # Vacant slot
					(location, ref) = psa.move(cref[c], vacant=v)
				else:
					location = cloc[c]
				rotation = Quaternion.rand()
				log.info(f"[{it}] Propose move {cloc[c]} to {location}, "
						f"rotating by {rotation}")

				# Translate to specified position, rotate by amount specified
				log.debug(f"Move mesh instance {c}")
				gc.collect()
				log.debug(f"2PreProcess size {getrusage(RUSAGE_SELF).ru_maxrss/1000}, "
						f"python size {getallocatedblocks()}")
				for i in range(leakcount):
					beep.move_mesh_instance(c, location, rotation,
											scenario.parameters['Dprotein'])
				gc.collect()
				log.debug(f"2PostProcess size {getrusage(RUSAGE_SELF).ru_maxrss/1000}, "
						f"python size {getallocatedblocks()}")

			# Calculate new energy
			log.info(f"BEEP solve... {it}")
			gc.collect()
			log.debug(f"BPreProcess size {getrusage(RUSAGE_SELF).ru_maxrss/1000}, "
					  f"python size {getallocatedblocks()}")
			for i in range(10):
				beep.reset_fh_vals()
				beep.solve(scenario.parameters['GMREStol'], \
						scenario.parameters['GMRESmaxit'])
			#beep.reset_library_fh_vals()
			gc.collect()
			log.debug(f"BPostProcess size {getrusage(RUSAGE_SELF).ru_maxrss/1000}, "
					  f"python size {getallocatedblocks()}")
			next_energy = beep.calculate_energies()
			gc.collect()
			log.debug(f"EProcess size {getrusage(RUSAGE_SELF).ru_maxrss/1000}, "
					  f"python size {getallocatedblocks()}")

			# Accept/reject move
			log.info(f"New energy {next_energy}, current energy {this_energy}")
			if next_energy >= this_energy and \
				exp((this_energy-next_energy)/RT) <= random.random():
				# Reject the move
				status = -1
				gc.collect()
				log.debug(f"DumpRPreProcess size {getrusage(RUSAGE_SELF).ru_maxrss/1000}, "
						f"python size {getallocatedblocks()}")
				results.dump() # Output results
				gc.collect()
				log.debug(f"DumpRPostProcess size {getrusage(RUSAGE_SELF).ru_maxrss/1000}, "
						f"python size {getallocatedblocks()}")
				if c >= 0:
					log.debug(f"Move mesh instance {c} back")
					gc.collect()
					log.debug(f"3PreProcess size {getrusage(RUSAGE_SELF).ru_maxrss/1000}, "
							f"python size {getallocatedblocks()}")
					for i in range(leakcount):
						beep.move_mesh_instance(c, cloc[c], rotation.inverse(),
												scenario.parameters['Dprotein'])
					gc.collect()
					log.debug(f"3PostProcess size {getrusage(RUSAGE_SELF).ru_maxrss/1000}, "
							f"python size {getallocatedblocks()}")
					psa.move(ref, to=cref[c])
				log.info("Move rejected")
			else:
				# Accept the move
				status = 0
				gc.collect()
				log.debug(f"DumpAPreProcess size {getrusage(RUSAGE_SELF).ru_maxrss/1000}, "
						f"python size {getallocatedblocks()}")
				results.dump() # Output results
				gc.collect()
				log.debug(f"DumpAPostProcess size {getrusage(RUSAGE_SELF).ru_maxrss/1000}, "
						f"python size {getallocatedblocks()}")
				this_energy = next_energy
				if c >= 0:
					(cloc[c], crot[c], cref[c]) = (location, rotation, ref)
				log.info("Move accepted")

			# Garbage collection
			gc.collect()
			
		# Output final results and kinemage
		# Set values for final results dump - no proposal data
		(c, next_energy, location,      rotation,    status) = \
		(0, this_energy, origin, no_rotation, 0)
		it = iters  # for dump
		results.dump()
		#beep.kinemage(path.join(workdir, f"{l}-{r}-finish.kin"))
		log.info("Iterations completed")

# Tidy up and exit
out.close()

