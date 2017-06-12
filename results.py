#!/usr/bin/env python3
# Status:  this is an evolving script;  it needs re-designing!

# There are two formats in play - version 2 missed storing the energy of
# rejected proposals, but is recovered from the log file by results.sh and
# stored in r2.txt.
# Version 3 onwards has all the data in the results.dat.
# There was a version 1 for the incomplete run 1, not used here.  That missed
# storing any reject/accept data, though this could be recovered by results.sh.

import argparse
from typing import List
from math import acos,pi,sqrt,inf
from enum import IntEnum
from copy import deepcopy

# Rotations Utilities
# Quaternion multiplication (= compound rotation)
def qmult(p, q):
	return (p[0]*q[0]-p[1]*q[1]-p[2]*q[2]-p[3]*q[3], \
			p[0]*q[1]+p[1]*q[0]+p[2]*q[3]-p[3]*q[2], \
			p[0]*q[2]+p[2]*q[0]+p[3]*q[1]-p[1]*q[3], \
			p[0]*q[3]+p[3]*q[0]+p[1]*q[2]-p[2]*q[1])

# Quaternion axis of rotation
def qaxis(q):
	s = sqrt(1-q[0]*q[0])
	return (q[1]/s,q[2]/s,q[3]/s) if s != 0 else (0,0,0)

# Vector dot product
def vdot(u, v):
	return u[0]*v[0]+u[1]*v[1]+u[2]*v[2]

# Vector difference
def vdiff(u, v):
	return (u[0]-v[0],u[1]-v[1],u[2]-v[2])

# Vector length adjustment
def vlen(v, l):
	norm = sqrt(vdot(v, v))
	return (v[0]*l/norm,v[1]*l/norm,v[2]*l/norm) if norm != 0 else (0,0,0)

# Angle between vectors
def angle(u, v):
	norm = sqrt(vdot(u, u) * vdot(v, v))
	return acos(vdot(u, v) / norm) if norm != 0 else 0

# Is l <= t < u for angle t, wrapping around [0,pi)?
def tband(l, t, u):
	return (t < (u if u < pi else pi) and t >= (l if l > 0 else 0)) or \
			((t > pi + l) if l < 0 else (t < u - pi))

# Rainbow colour scheme
# This is a little biased to the dark end?  And may produce some sillies...
def rainbow(n: int) -> list:
	primary = [int(v*255/n) for v in range(n)]
	colours = [(255-v,v,0) for v in primary] + [(0,255-v,v) for v in primary] \
			+ [(v,0,255-v) for v in primary]
	return [f"#{r:02x}{g:02x}{b:02x}" for (r,g,b) in colours]

# Construct integer list from string specs
# Note don't want s=str, so use List not Sequence
def intList(s: List[str], length: int) -> List[int]:
	retval = list()
	# al = [i for i in range(length)] # Quick route, expensive if length >> 0
	try:
		for sv in s:
			# Get the raw specification - note guaranteeing len(il) >= 1
			il = [int(i) if i else None for i in sv.split(":")]
			# NB quick route (see above):
			#retval += (al[slice(*il)] if len(il) > 1 else [al[il[0]]])
			# Make the increment explicit
			inc = (il[2] if len(il) > 2 and il[2] != None else 1) # 0 is invalid
			# Specify explicit beginning and end of list based on inc direction
			beg = il[0] if il[0] != None else (0 if inc > 0 else length)
			if len(il) > 1:
				end = (il[1] if il[1] != None else (0 if inc < 0 else length))
			else:
				end = (beg+inc if beg != -1 or inc != 1 else length)
			# Convert any negative numbers in the first two places
			il[0:2] = [ilv if ilv >= 0 else length+ilv for ilv in [beg,end]]
			# Add the numbers to the return list
			retval += [rv for rv in range(*il)]
	except:
		print("Bad integer specifier: ", *s if type(s) == list else ["???"])
		exit(1)
	# Eliminate duplicates and sort the resulting list for return
	return sorted(list(set([rv for rv in retval if rv < length])))

# Program start =============================================

# Filters are needed to weed out improbable BEEP results
elim = None # Filter energy difference limit
OffsetMethod = IntEnum('Offset', 'avg fur min zer sel', start=0)
Fig = IntEnum('Fig', 'i s p b e a c d f t ad at dt', start=0)

# Set up command line parsing
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter, \
					  argparse.RawTextHelpFormatter):
    pass

parser = argparse.ArgumentParser(description=\
				"Analyse data from phase 1 processing.",
				formatter_class=CustomFormatter)
				#formatter_class=argparse.ArgumentDefaultsHelpFormatter)

# eliminations
parser.add_argument('--elim', nargs='?', default=None,
					metavar="ENERGY-DIFFERENCE",
					help="filter energies too far from first value")

# offset method
parser.add_argument('--offset', nargs='?', default='fur', dest='offset',
					metavar="METHOD",
					help="offset method for energy differences:\n" \
						"fur(thest); avg; min; zer(o)")

# subject selector
parser.add_argument('--subsel', default=-1, dest='subsel', type=int,
					help="subject selector for separations, 0-base index;\n" \
						"absent or negative for net centre of subjects\n")

# BEEP scenario configuration files
parser.add_argument('--bsc', nargs='*', default=None, dest='bsc',
					metavar="ITS",
                    help="output results-l-r.bsc for each l-location and " \
						"r-run\nfor iterations slice ITS (Python format), " \
						"including \nonly the moved crowders; " \
						"first and last iterations \nonly if ITS absent, " \
						"with all crowders.")

# plot selector
parser.add_argument('--plot', nargs='*', default=None, dest='plot',
					metavar="PLOT",
                    help="specify which plots to display (if enough data)\n"
"""Code File name Meaning
i    2DEI      Subject energy by iteration
s    2DES      Subject energy by separation
p    2SE       Energy by simplification level
b    2BH       Bug-hunting energy by iteration
e    2DE       Energy by iteration
a    3DE       3D plot of proposals
c    3DC       3D plot of crowding
d    2Dd       Distance by iteration and energy
f    2Df       Energy by distance
t    2Ddav     Angle between rotation axis and position
               by iteration and energy
ad   2Da       Average distance by energy
at   2Ddat     Average angle by energy
dt   2Ddad     Angle density by energy
""")

# results-file
parser.add_argument('results', nargs='?', default="results",
					help='name of results file (.dat assumed)')

# Interpret arguments
args = parser.parse_args()
print(args)
dfn = args.results + ('' if args.results[-4:] == '.dat' else '.dat')
dat = open(dfn,'rb')
elim = float(args.elim) if args.elim != None else None
offmet = OffsetMethod.fur
if args.offset[0:3] == 'avg':
	offmet = OffsetMethod.avg
elif args.offset[0:3] == 'min':
	offmet = OffsetMethod.min
elif args.offset[0:3] == 'zer':
	offmet = OffsetMethod.zer
elif args.offset[0:3] != 'fur':
	print(f"Unrecognised offset method {args.offset}, defaulting to furthest")
subsel = args.subsel
bsccrwd = False if len(args.bsc) > 0 else True  # all crowders? else movers
dropbsc = (None if args.bsc == None \
			else (args.bsc if len(args.bsc) > 0 else  ['0','-1']))
plotfigs = ([fgn.name for fgn in Fig] if args.plot == None \
			else (args.plot if len(args.plot) > 0 else list()))


# Unpickle results data
# A single header record (if present) lists:
#	program,version,[(subject-pdb,radius)],[(crowder-pdb,radius)]
# program := string;  version := int; *-pdb := string; radius := float
# Note there must be only one header for all runs (even if it is repeated).
# After the header, the layout is of 5-line records:
#	line 1: energy := (location-idx, run-idx, iteration, accepted-energy)
#	line 2: subjects := (count, [subject-locations])
#	line 3: crowders := {crowder-instance-id: crowder-type}
#	line 4: locations := (count, [crowder-locations])
#	line 5: rotations := (count, [crowder-rotations])
#	line 6: outcomes := (crowder-idx, energy, [location], [rotation], status)
# All lines become lists after the unpickling below.
# idx, iteration and count values are non-negative integers.
# status is 0 (accepted) or 1 (rejected).
# energy is float.
# location := (x,y,z).
# rotation := (a,b,c,d).
# plural indicates a list of values.
# subjects and crowders are in header order.
# Note that line 5 relates to proposals, and is missing in version 1 (not used).
# Version 2 is missing the proposal energy in line 5, which is corrected below.
# Version 3 and below have no header record.
# Version 4 and below have no crowders (crowder-types) records
from pickle import Unpickler
header = list()
energy = list()
subjects = list()
crowders = list()
locations = list()
rotations = list()
outcomes = list()

results = Unpickler(dat)
header = None
version = 3	# Assumption for now
while True:
	try:
		record = results.load()
		if type(record[0]) == int:
			energy += [record]
		else:
			if header == None:	# All headers should be the same
				header = record
				version = header[1]
			energy += [results.load()]
	except EOFError:
		break
	subjects += [results.load()]
	if version > 4:
		crowders += [results.load()]
	locations += [results.load()]
	rotations += [results.load()]
	outcomes += [results.load()]
dat.close()
if header == None:
	ns = len(subjects[0]) if len(subjects) > 0 else 0
	nc = locations[0][0] if len(locations) > 0 else 0
	# Provisional and dummy header - just enough to get through processing
	header = ["phase1.py",version,	\
			  [(f"unk{n}",1.0) for n in range(ns)],	\
			  [(f"unk{n}",1.0) for n in range(nc)]]

# Just for testing the unpickling...
fred = False
if fred:
	if True:
		for e in energy:
			#for res in e[1]:
			print(e[0],e[1],e[3])
	else:
		for r in rotations:
			for res in r[1]:
				print(sum([x*x for x in res]))

# Test if this is a version 2 file and correct if possible
if version == 3 and len(outcomes[0]) == 4:  # 5 values in version 3+
	# Check for additional energy data - detected by the presence of run2.txt
	extra = list()
	try:
		with open("run2.txt") as f:
			for line in f:
				extra += [float(line)]
		extra = [extra[0]] + extra	# First value will be missing
		extra += [extra[-1]]		# Last value also missing
	except:
		pass
	extrac = len(extra)-1
	version = 2 if extrac > 0 else 1
	print(f"Read {extrac} lines from r2.txt, version 2 is {version2}")
if version == 2:		# Need to merge r2.txt values
	for n in range(len(outcomes)):
		outcomes[n] = (outcomes[n][0], extra[n], outcomes[n][1], \
						outcomes[n][2], outcomes[n][3])

# If there is no crowder-types information, make it up
nct = len(header[3])	# Number of crowder types
if version < 5:
	# Assume equal numbers of each type;  no types implies no locations either
	n = locations[0][0]//(max(nct,1)) if len(locations) > 0 else 0
	tmpcl = [sum([[c]*n for c in range(nct)],[]) for _ in locations]
	if len(tmpcl) != len(locations):
		print("Error:  unable to assume equal crowder numbers in version "
				f"{version} data")
		exit(1)
	elif nct > 1:
		print(f"Warning:  assuming equal numbers of {nct} crowder types - "
			  "this may lead to an error")
	# Construct crowders from tmpcl list, set cid from index and subject count
	crowders = list()
	ns = len(subjects[0]) if len(subjects) > 0 else 0
	for n in range(len(tmpcl)):
		tmpc = dict()
		for i in range(len(tmpcl[n])):
			tmpc[ns+i] = tmpcl[n][i]
		crowders += [tmpc]

# No scenario data in versions below 5
if version < 6:
	# Use first crowder radius for sphere radius if possible, else no matter
	arenaGrainSize = header[3][0][1] if len(header[3]) > 2 else 1.0
	arenaRadius = arenaGrainSize  # This will save processing time for kin only
	nsl = sum([s[0] for s in subjects]) if len(subjects) > 0 else 0
	sl = [s[1] for s in subjects]
	arenaCentre = [sum([u[cd] for ul in sl for u in ul])/nsl
					for cd in range(3)] if nsl > 0 else [0.0,0.0,0.0]
else:
	arenaGrainSize = header[4][0]
	arenaRadius = header[4][1]	# Permits solve as well as kin
	arenaCentre = header[4][2]


# Header processing for later plots
forsubjpdbs = "for " + ":".join([subj[0] for subj in header[2]]) \
				if version > 3 else ""

# Warn of the filtering and selecting applied
print(f"Filtering set to {elim}")


# There are different scenarios to cater for.
# Subject movement tests
#	If there is more than one location-idx, a subject movement plot is required.
#	The main interest is the variation of energy with separation, but also
#	the variation of energy by iteration owing to bugs in BEEP.
#	Each location-idx indicates a new separation;  each run-idx may indicate
#	a different crowding scenario.  The minimum energy across iterations is
#	used.  Plots are per run of energy by separation.
# Crowding tests
#	If there are multiple iterations per combination of location-idx and
#	and run-idx along with crowders then crowding analysis is required.
#	These were the original aim of the project! 
#	Repeats for the same iteration are silently folded into the analysis.
# Bug hunting tests
#	If there are iterations for one location-idx and run-idx but no crowders
#	then a plot of variability in energy is required.
#	These are just plain repeats of the same thing over and over.
# Simplification tests
#	If there are multiple repeats with the same location-idx, run-idx and
#	iteration then a simplification test plot is required.
#	The data is a concatenation of separate runs with no simplification keys.
#	It is therefore assumed that simplifications follow a fixed pattern.
#	In practice, there should be no crowders and only one subject, but in any
#	case each repeat is plotted on the one chart.
#
# Summary:
# Test		loc	run	ite	rep	crowd
# Subj-sep	>1	per	min	min	any
# Crowding	per	per	[ >1  ]	>0
# Bug-hunt 	per	per	[ >1  ]	0
# Simpli	per	per	per	>1	any (but usually none)
#

pct = [ 10, 20, 30, 40, 50, 60, 70, 80, 90, 100 ] # Fixed simplification levels
# Colour, marker and line scheme
#cs = ['r', 'y', 'g', 'c', 'b', 'm']	# colours
ps = rainbow((len(pct)+2) // 3)		# pct spectrum (colour scheme)
cs = rainbow(nct)					# crowder spectrum

ms = ['^', 'o']						# marker styles
ls = ['solid', 'dotted']			# corresponding line styles
lab = ["accepted", "rejected"]		# legend labels

# Indexing analysis
# lrit dict by location-idx then run-idx then iteration of repeat count
# ser dict by run-idx then location-idx of minimum energy across iterations
# sim dict by location-idx then run-idx then iteration of energy
lrit = dict()	# general indexing nested dictionary
ser = dict()	# separation energy records: list of repeats (simplifications)
sim = dict()	# simplification energy record
lrrep = dict()	# repeat counter, assumed to run in sequence against pct
for (l,r,it,e) in energy:
	# lrit processing - runs are only unique per location
	if not l in lrit:
		lrit[l] = dict()
	if not r in lrit[l]:
		lrit[l][r] = dict()
	if not it in lrit[l][r]:	# NB iterations should be safely consecutive
		lrit[l][r][it] = 1
	else:
		lrit[l][r][it] += 1

	# Repeats processing
	if not (l,r) in lrrep:
		lrrep[(l,r)] = [it]
	else:
		# if it < max(lrrep[(l,r)]): continue  # Skip earlier iterations
		lrrep[(l,r)] += [it]
	#ctr = lrrep[(l,r)]
	#ctr = len([1 for i in lrrep[(l,r)] if i == max(lrrep[(l,r)])])-1
	ctr = len([1 for i in lrrep[(l,r)] if it == i])-1

	# TODO lose old ser[r][l] processing commented out
	# ser processing - runs link across locations in this case
	if not r in ser:
		ser[r] = [dict()]*len(pct)
		ser[r][ctr] = {l: e}	# Safer as a dict() as l may not be consecutive
		#ser[r] = {l: e}	# Safer as a dict() as l may not be consecutive
	if len(ser[r][ctr]) == 0:
		ser[r][ctr] = {l: e}
	# If filtering silly values, then skip this record entirely if bad
	# Note that the first energy value is reliable even if others are not
	#if elim != None and abs(e-ser[r][min([k for k in ser[r]])]) >= elim:
	if elim != None and \
			abs(e-ser[r][ctr][min([k for k in ser[r][ctr]])]) >= elim:
		print("Skipping", l, r, it, e)
		lrrep[(l,r)] = lrrep[(l,r)][0:-1]  # Lose this iteration record
		continue
	#print("Including", l, r, it, e)
	#if not l in ser[r]:
	if not l in ser[r][ctr]:
		#ser[r][l] = e
		ser[r][ctr][l] = e
	#ser[r][l] = min(e,ser[r][l])
	# min is wrong here - should be last iteration!!
	#ser[r][ctr][l] = min(e,ser[r][ctr][l])
	# store e if it is for the same iteration as the maximum found so far
	if it >= max(lrrep[(l,r)]):
		ser[r][ctr][l] = e

	# sim processing
	if not l in sim:
		sim[l] = dict()
	if not r in sim[l]:
		sim[l][r] = dict()
	#if not it in sim[l][r]:
	#	sim[l][r][it] = list()
	#sim[l][r][it] += [e]
	if not ctr in sim[l][r]:
		sim[l][r][ctr] = list()
	sim[l][r][ctr] += [e]

# Subject separation processing
sep = dict()	# dict by run of list of separations
see = dict()	# dict by run of list of minimum energies in separation order
seq = dict()	# dict by run of list of minimum energies in location-idx order
# If there is more than one energy per location and run, then plot minimum
subjectsl = len(subjects)
for r in ser:
	# Calculate separation as average distance of subjects from mutual centre
	# Note len(energy) == len(subjects)
	tmpd = dict()  # Not used outside of this preparatory phase
	# TODO this is better as set of locations...
	for l in sorted(lrit):
		# Select subject locations for this location-idx l and run-idx r
		# There could be repeats, but same value, so just take the first one
		# i.e. location-idx and run-idx fix the subject location across its/reps
		sbj = [subjects[n][1] for n in range(subjectsl) \
				if energy[n][0] == l and energy[n][1] == r][0]
		if len(sbj) < 1:	# Not enough subjects to have a separation
			continue
		elif len(sbj) == 1:	# Still not enough, but useful check on variability
			sbjl = 1
			sbjd = sbj
		elif subsel >= 0:	# Separations to be from selected subject
			sbjd = [vdiff(sbj[i],sbj[subsel])
						for i in range(len(sbj)) if i != subsel]
			sbjl = len(sbjd) # Guaranteed above to be at least 1
		else:				# Separations can be calculated across all
			# Find separation for this location
			# for >=2 subjects this should be avg sep of all
			n = len(sbj)
			sbjs = [[(sbj[j],sbj[i]) for j in range(i+1,n)] for i in range(n-1)]
			sbjd = [vdiff(sbj1,sbj0) for sbjsv in sbjs for (sbj1,sbj0) in sbjsv]
			# relative locations
			sbjl = len(sbjd) # Guaranteed above to be at least 1
		# This is the first complication:  elimination above may create gaps
		tmpd[sum([sqrt(vdot(sbjdv,sbjdv)) for sbjdv in sbjd])/sbjl] = \
			[(ser[r][ctr][l] if l in ser[r][ctr] else None) \
				for ctr in range(len(pct))]
		#ser[r][l]

	# Save the separations and energies in lists ordered by separation
	# This would have been straightforward were it not for the need to cope
	# with gaps from elimination...
	# Instead, sep[r] and see[r] must be dictionaries by percent counter
	# By construction each r is encountered only once...
	(sep[r], see[r], seq[r]) = (dict(), dict(), dict())
	for ctr in range(len(pct)):
		# Check there are valid locations for this counter
		tmpk = sorted([k for k in tmpd if tmpd[k][ctr] != None])
		#tmpk = [tmpd[k][ctr] for k in tmpd if tmpd[k][ctr] != None]
		if len(tmpk) == 0:
			continue
		# Get the offset energy for this counter
		if offmet == OffsetMethod.avg:
			offe = sum([tmpd[k][ctr] for k in tmpk])/len(tmpk)
		elif offmet == OffsetMethod.fur:
			offe = tmpd[max([k for k in tmpk])][ctr]
		elif offmet == OffsetMethod.min:
			offe = min([tmpd[k][ctr] for k in tmpk])
		else:
			offe = 0
		# Store the ctr values - again, each ctr encountered per r only once
		sep[r][ctr] = tmpk
		see[r][ctr] = [tmpd[k][ctr]-offe for k in tmpk]
		# and energies in sequence of locations
		seq[r][ctr] = [ser[r][ctr][k]-offe for k in sorted(ser[r][ctr])]
		
	#mine = min([tmpd[k] for k in tmpd])
	#sep[r] = [k for k in sorted(tmpd)]
	#see[r] = [tmpd[k]-mine for k in sorted(tmpd)]
	## and energies in sequence of locations
	#seq[r] = [ser[r][k]-mine for k in sorted(ser[r])]


# Crowding Analysis
# The analysis produces a lot of plottable data, which is stored as lists in
# dictionaries.  These are explained on assignment later.
# lrit provides the detailed indexing, here only need tuple indexes
(lre, lra) = (dict(), dict())
(lrsx, lrsy, lrsz) = (dict(), dict(), dict())
(lrccs, lrcli, lrclf) = (dict(), dict(), dict())
(lrvc, lrqc) = (dict(), dict())
(lrd, lrits, lrtheta) = (dict(), dict(), dict())
(lrpe, lrave, lrpc, lrcc) = (dict(), dict(), dict(), dict())
(lrdtx, lrdty) = (dict(), dict())
(lravd, lrsdd) = (dict(), dict())
(lravt, lrsdt) = (dict(), dict())
lrct = dict()
lrebc = dict()
(lrlb, lrca, lrlbc) = (dict(), dict(), dict())

for l in sorted(lrit):
	for r in sorted(lrit[l]):
		# Select the record indices for main plots by l, r and elim filter
		rec = [n for n in range(len(energy)) \
				if energy[n][0] == l and energy[n][1] == r and \
					((abs(outcomes[n][1]-outcomes[0][1]) < elim) \
										if elim != None else True)]

		# Construct outcomes and energy list for further processing
		ctyp = [[crowders[n][k] for k in sorted(crowders[n])] for n in rec]
		cloc = [locations[n][1] for n in rec]	# Accepted crowder locations
		crot = [rotations[n][1] for n in rec]	# Accepted crowder rotations
		oc = [outcomes[n] for n in rec]			# Proposal data
		# Construct filter for buggy values
		#flt = [n for n in range(len(oc)) if ((abs(oc[n][1]-oc[0][1]) < elim) \
		#								if elim != None else True)]
		#oc = [oc[n] for n in flt]				# Filter
		e = [oc[n][1] for n in range(len(oc))]  # Calculated energy
		a = [energy[n][3] for n in rec]			# Accepted energy
		#a = [a[n] for n in flt]					# Filter

		# Remaining analysis is for crowder energies, so skip if no crowders
		#if sum([len(cv[1]) for cv in locations]) == 0:
		#	continue

		# Data for proposal plots: energy/position, distance and angle
		crwd = [oc[n][2][0] for n in range(len(oc))]	# crowder location lists
		rot = [oc[n][3][0] for n in range(len(oc))]	# crowder rotation lists
		acpt = [-oc[n][4] for n in range(len(oc))]	# acceptance status list
		(mine,maxe) = (min(e),max(e)) if len(e) > 0 else (0,0)
		m = mine if mine < maxe else maxe+1-len(ps)
		# Bands are fixed, not quantiles
		b = (maxe - m) / (len(ps)-1)				# Band width
		ib = [int((ev-m) // b) for ev in e]			# Index bands
		fb = [1-ibv/(len(ps)-1) for ibv in ib]		# Fractional bands
		cb = [ps[ibv] for ibv in ib]				# Colour bands
		eb = [b*csv+m for csv in range(len(ps))]	# Floor values for labels...
		lb = [f"{ebv:.1f}-{ebv+b:.1f} kJ/mol" for ebv in eb]	# ...Band labels
		eb = [ebv+b/2 for ebv in eb]				# Adjust to midpoints

		# Subject locations:  will be fixed for the same location l for all r
		# sx = list of x-coordinates, sy = ...
		(sx,sy,sz) = [[s[cd] for s in subjects[rec[0]][1]] for cd in range(3)] \
						if len(rec) > 0 else (list(), list(), list())
		# Crowder locations:  same counts for same l and r
		#nc = locations[rec[0]][0]			# number of crowders in total
		nc = len(ctyp[0]) if len(ctyp) >0 else 0 # number of crowders in total
		ccs = [0]*nct						# crowder colour set
		(cli,clf) = (ccs[:],ccs[:])			# crowder locations (init, final)
		for c in range(nct):
			# Note crowders cannot change type as part of a move! (= use first)
			ctn = [n for n in range(nc) if ctyp[0][n] == c]
			ccs[c] = [cs[ctyp[0][n]] for n in ctn]
			cli[c] = [[cloc[0][n][cd] for n in ctn] for cd in range(3)]
			clf[c] = [[cloc[-1][n][cd] for n in ctn] for cd in range(3)]

		# Obtain the "centre" of the arena
		# Centre is a specific subject if subsel set, else average of all
		if subsel >= 0:
			if subsel > len(sx):
				print("Bad choice of subject selector! Using centre (0,0,0)")
				centre = (0,0,0)
			else:
				centre = (sx[subsel],sy[subsel],sz[subsel])
		else:
			centre = (sum(sx)/len(sx), sum(sy)/len(sx), sum(sz)/len(sx)) \
						if len(sx) != 0 else (0,0,0)
		# Rotations - accumulate with accepted moves
		base = (1, 0, 0, 0)	# Start with no rotation

		# Interlude:  drop out bsc files for kin generation via phase1.py
		if dropbsc != None:
			print("Reminder: rotations not in bsc output yet")
			bsc=open(f"results-{l}-{r}.bsc",'w')
			# Subjects
			for n in range(len(sx)):
				sl=f"({sx[n]},{sy[n]},{sz[n]})"
				sl=f"{header[2][n][0]} location={sl},{sl},(1,0,0)"
				print(sl, file=bsc)
			# Iterations
			maxit = max([k for k in lrit[l][r]]) if len(lrit[l][r]) > 0 else 0
			il = intList(dropbsc,maxit+1) # iterations list of interest
			# Crowders
			ns = len(subjects[0]) if len(subjects) > 0 else 0	# index offset
			# cixl = all crowders or only movers in specified iterations:
			if bsccrwd:
				cixl = range(len(cloc[0]))
			else:
				cixl = [oc[i][0]-ns for i in il if oc[i][0] > ns]
				il += ([il[-1]+1] if il[-1] < maxit else [maxit]) #Add last move
			# Now output locations for each molecule
			for n in cixl:
				cl=f"{header[3][ctyp[0][n]][0]} location="
				lcl = len(cl)
				inc = [0,0,0]
				output = False
				rej = None
				for i in il+[il[-1]]:  # odd/2; guaranteed len(il) > 0
					# TODO include rotations!
					loc = cloc[i][n]
					loc = (crwd[rej] if rej != None else cloc[i][n])
					rej = i if n == (oc[i][0]-ns) and acpt[i] != 0 else None
					inc = [loc[cd]-inc[cd] for cd in range(3)]
					# Write out pairs in start,end,incr lines
					cl=f"{cl}({loc[0]},{loc[1]},{loc[2]}),"
					if output:
						cl=f"{cl}({inc[0]},{inc[1]},{inc[2]})"
						print(cl, file=bsc)
						cl=" "*lcl
						inc = [0,0,0]
					output = not output
			# Hopefully helpful parameters...
			print(f"ArenaGrainSize={arenaGrainSize}", file=bsc)
			print(f"ArenaRadius={arenaRadius}", file=bsc)
			print(f"ArenaCentre={arenaCentre}", file=bsc)
			print("MCiter=0", file=bsc)
			bsc.close()

		# Back to main results processing
		# Oversight in matplotlib: won't accept a marker list
		# Lists split by acceptance status, used to differentiate markers
		pc = list()		# List of point colour lists
		cc = list()		# List of crowder colour lists
		pb = list()		# List of point band lists
		pe = list()		# List of point energies
		its = list()	# List of iteration number lists
		v = list()		# List of vector lists of moved crowder locations
		#w = list()		# List of vector lists of averaged crowder distances
		q = list()		# List of quaternion lists of crowder rotations
		d = list()		# List of distance lists
		theta = list()	# List of angle lists
		for i in lab:
			pc += [list()]
			cc += [list()]
			pb += [list()]
			pe += [list()]
			its += [list()]
			v += [list()]
			#w += [list()]
			q += [list()]
			d += [list()]
			theta += [list()]
		for n in range(len(cloc)):
			i = acpt[n]
			cid = oc[n][0] - len(subjects[0])
			pc[i] += [cb[n]]
			# Kludge as last oc[n][0]=0:
			cc[i] += [cs[ctyp[n][max(cid,0)]]] if len(ctyp[n]) > 0 else []
			pb[i] += [fb[n]]
			pe[i] += [e[n]]
			its[i] += [n]
			# Moved crowder positions as v, rotations as q
			v[i] += [(crwd[n][0], crwd[n][1], crwd[n][2])]
			q[i] += [(rot[n][0], rot[n][1], rot[n][2], rot[n][3])]
			# Average crowder positions as d: with proposed move
			tclocn = deepcopy(cloc[n])			# Temp copy...
			tcrotn = deepcopy(crot[n])			# Temp copy...
			if cid > 0:	# There may not be any crowders? Or this is last record
				tclocn[cid] = list(v[i][-1])	# ...to avoid overwriting cloc
				tcrotn[cid] = list(q[i][-1])	# ...to avoid overwriting cloc
			w = [vdiff(tclocn[c], centre) for c in range(len(tclocn))]
			d[i] += [sum([sqrt(vdot(w[c], w[c])) \
							for c in range(len(tclocn))]) / max(len(tclocn),1)]
			#w[i] += [[sum([tclocn[c][cd] for c in range(len(tclocn))]) / \
			#			max(len(tclocn),1) for cd in range(3)]]
			theta[i] += [sum([angle(vdiff(tclocn[c],centre),qaxis(tcrotn[c])) \
							for c in range(len(tcrotn))]) / max(len(tcrotn),1)]
			#q[i] += [qmult(rot[n],base)]
			#if i == 0:			# Meaning this move was accepted
			#	base = q[i][-1]	# Accumulate accepted rotations
		# Also turn the vector lists inside out so that coordinates are listed
		vc = [[[vv[n][cd] for n in range(len(vv))] for cd in range(3)] \
				for vv in v if len(vv) > 0]
		# Locations relative to centre
		#wd = [[vdiff(wvv,centre) for wvv in wv] for wv in w]
						

		# Directions for axial arrows
		# Adjust lengths by energy band scaled to 0.2 maximum axis length
		al = max([max([max(vcv[cd]) for vcv in vc]) \
				 -min([min(vcv[cd]) for vcv in vc]) for cd in range(3)]) /5.0 \
				if len(vc) > 0 else 0.0
		qa = [[vlen(qaxis(q[i][n]), al*pb[i][n]) for n in range(len(q[i]))] \
				for i in range(len(q))]
		# Turn inside out to match vc
		qc = [[[qav[n][cd] for n in range(len(qav))] for cd in range(3)] \
				for qav in qa]

		# Table of accepted moves
		#for n in range(len(v[0])):
		#	print(v[0][n][0], v[0][n][1], v[0][n][2], pc[0][n])

		# Distances and angles
		avd = [0]*len(ps)
		ave = avd[:]
		avt = avd[:]
		ct = avd[:]
		sdd = avd[:]
		sdt = avd[:]
		for i in range(len(v)):		# Bands
			# Distance and angle per point
			#for n in range(len(v[i])):
				# Distance from location to centre
				#d[i] += [sqrt(vdot(wd[i][n], wd[i][n]))]
				# Calculate angle from axis to centre of arena
				#theta[i] += [angle(wd[i][n], qaxis(q[i][n]))]
			# Totals and counts from this band
			for c in range(len(ps)):
				ci = [n for n in range(len(d[i])) if pc[i][n] == ps[c]] # Match
				avd[c] += sum([d[i][n] for n in ci])
				ave[c] += sum([pe[i][n] for n in ci])
				avt[c] += sum([theta[i][n] for n in ci])
				sdd[c] += sum([d[i][n]*d[i][n] for n in ci])
				sdt[c] += sum([theta[i][n]*theta[i][n] for n in ci])
				ct[c] += len(ci)
		# Colour, averages and counts across bands
		ctc = [c for c in range(len(ps)) if ct[c] != 0]  # Exclude empties
		ca = [ps[c] for c in ctc]
		sdd = [sqrt(sdd[c]/(ct[c]-(1 if ct[c]>1 else 0))-(avd[c]/ct[c])**2) \
				for c in ctc]
		sdt = [sqrt(sdt[c]/(ct[c]-(1 if ct[c]>1 else 0))-(avt[c]/ct[c])**2) \
				for c in ctc]
		avd = [avd[c]/ct[c] for c in ctc]
		ave = [ave[c]/ct[c] for c in ctc]
		avt = [avt[c]/ct[c] for c in ctc]
		ct = [ct[c] for c in ctc]
		ebc = [eb[c] for c in ctc]
		lbc = [lb[c] for c in ctc]

		# For angles it is also useful to consider densities
		dg = 11			# density granularity
		db = 8			# width to count across is pi/db
		dty = [list()]*len(ps)	# list of density lists
		dtx = dty[:]			# list of density angle lists
		for c in range(len(ps)):	# Split by colour band
			dty[c] = [0]*dg			# density list for this band
			dtx[c] = dty[c][:]		# density angle list for this band
			for nt in range(dg):	# To construct the density list
				dtx[c][nt] = nt*pi/dg
				lo = dtx[c][nt]-pi/db	# Lower bound
				up = dtx[c][nt]+pi/db	# Upper bound
				# sum of counts of angles in the band and within the interval
				for i in range(len(theta)):
					for n in range(len(theta[i])):
						if pc[i][n] == ps[c]:
							dty[c][nt] += tband(lo, theta[i][n], up)
			# Convert counts to densities
			dts = sum(dty[c])
			dty[c] = [dtv/dts if dts > 0 else 0 for dtv in dty[c]]
			# Complete the cycle for plotting
			dty[c] += [dty[c][0]]
			dtx[c] += [pi]

		# Save the useful calculations by location-idx and run-idx
		k = (l,r)
		(lre[k], lra[k]) = (e, a)	# propose/accept energy
		(lrsx[k], lrsy[k], lrsz[k]) = (sx, sy, sz) # Subj coords
		# Crowder type records, colours and initial and final coords
		(lrccs[k], lrcli[k], lrclf[k]) = (ccs, cli, clf)
		# Crowder move vector starts and ends
		(lrvc[k], lrqc[k]) = (vc, qc)
		# Distance from centre and angle distn
		(lrd[k], lrits[k], lrtheta[k]) = (d, its, theta)
		# point energy, averaged energy in band and point/crowder colour to use
		(lrpe[k], lrave[k], lrpc[k], lrcc[k]) = (pe, ave, pc, cc)
		# Exclusion of empties:
		(lrdtx[k], lrdty[k]) = (dtx, dty)	# Density plot for angles
		(lravd[k], lrsdd[k]) = (avd, sdd)	# Av distance
		(lravt[k], lrsdt[k]) = (avt, sdt)	# Av angle
		lrct[k] = ct						# Counts of points
		# Labelling and colours
		lrebc[k] = ebc						# Energy band midpoints
		(lrlb[k], lrca[k], lrlbc[k]) = (lb, ca, lbc)

#######################
# Plots
#######################
# Core plotting requirements
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

# figure: filename, legend-position
figInfo = [
	[f"{args.results}-2DEI", 'upper left'],
	[f"{args.results}-2DES", 'upper right'],
	[f"{args.results}-2SE", 'lower left'],
	[f"{args.results}-2BH", None],
	[f"{args.results}-2DE", 'lower left'],
	[f"{args.results}-3DE", 'upper left'],
	[f"{args.results}-3DC", 'upper left'],
	[f"{args.results}-2Dd", 'lower left'],
	[f"{args.results}-2Df", 'lower left'],
	[f"{args.results}-2Ddav", None],
	[f"{args.results}-2Da", 'upper left'],
	[f"{args.results}-2Ddat", None],
	[f"{args.results}-2Ddad", 'upper left']
	]
# Make provision for a set of figures in each case
figures = dict()
for fgn in Fig:
	figures[fgn] = [dict(), figInfo[fgn][0], figInfo[fgn][1]]

# 2D Subject-separation energy - plot separations by location for
# each run present.  Note:  this plot does make sense for single subjects
# as it shows how calculations vary by position (when they should not).
seqc = dict()
sepc = dict()
if offmet == OffsetMethod.avg:
	ylab = "Energy variation (kJ/mol)"
elif offmet == OffsetMethod.fur:
	ylab = "Energy difference with farthest separation (kJ/mol)"
elif offmet == OffsetMethod.min:
	ylab = "Energy difference from minimum (kJ/mol)"
else:
	ylab = "Energy (kJ/mol)"
for r in sep:
	# Skip if there is only one location-idx for this run
	if  len(seq[r]) < 1 or \
		max([len(seq[r][ctr]) for ctr in seq[r]]) <= 1:
		continue
	if not r in figures[Fig.i][0]:
		figures[Fig.i][0][r] = plt.subplots()
		axi = figures[Fig.i][0][r][1]
		axi.set_xlabel("Location Sequence")
		axi.set_ylabel(ylab)
		axi.set_title("Subject energy " + forsubjpdbs)
	axi = figures[Fig.i][0][r][1]

	# Plot the energy by sequence, different colour per repeat on same plot
	if not r in seqc:
		seqc[r] = 0		# index for sequential plot colours
	corner = 0.0		# used to decide where to put the legend
	for ctr in seq[r]:
		axi.plot(list(range(len(seq[r][ctr]))), seq[r][ctr], \
				c=ps[seqc[r]%len(ps)], label=pct[ctr])
		seqc[r] += 1
		furthest = len(seq[r][ctr])-1
		corner += seq[r][ctr][furthest]-seq[r][ctr][0]
	figures[Fig.i][2] = 'lower right' if corner > 0 else 'upper right'

	# Skip if all the locations are the same - no use plotting single points...
	if max([len(sep[r][ctr]) for ctr in sep[r]]) <= 1:
		continue
	if not r in figures[Fig.s][0]:
		figures[Fig.s][0][r] = plt.subplots()
		axs = figures[Fig.s][0][r][1]
		axs.set_xlabel("Separation (A)")
		axs.set_ylabel(ylab)
		axs.set_title("Subject energy " + forsubjpdbs)
		#axs.set_ylim([-25,65])
	axs = figures[Fig.s][0][r][1]

	# Plot the energy by separations per repeat
	if not r in sepc:
		sepc[r] = 0		# index for sequential plot colours
	corner = 0.0		# used to decide where to put the legend
	for ctr in sep[r]:	# simplification percent counter
		axs.plot(sep[r][ctr], see[r][ctr], \
				c=ps[sepc[r]%len(ps)], label=pct[ctr])
		sepc[r] += 1
		furthest = len(sep[r][ctr])-1
		corner += sep[r][ctr][furthest]-sep[r][ctr][0]
	figures[Fig.s][2] = 'lower right' if corner > 0 else 'upper right'

# Plots by location
(lrec, ec) = (0, 0)	# Colour indices
simc = dict()		# Simplification plot counts
for l in sorted(lrit):
	for r in sorted(lrit[l]):
		k = (l,r)
		lastit = max(sorted(lrit[l][r]))

		# Simplification is indicated by repeated iterations
		if not r in simc:
			simc[r] = 0		# index for sequential plot colours
		for it in []:  #sorted(lrit[l][r],reverse=True):
			# The last energy record is a further repeat if no iterations and
			# then concatenations duplicate whole l-r-it - so skip these
			if lrit[l][r][it] <= 1 or \
				it not in sim[l][r] or len(sim[l][r][it]) == 0:
				continue
			# Assume repeated iterations are in pct order
			if not r in figures[Fig.p][0]:
				figures[Fig.p][0][r] = plt.subplots()
				axp = figures[Fig.p][0][r][1]
				axp.set_xlabel("Simplification Level")
				axp.set_ylabel("Energy")
				axp.set_title(f"{args.results} Simplification effect")
			axp = figures[Fig.p][0][r][1]
			axp.plot(pct[0:len(sim[l][r][it])], sim[l][r][it], \
					c=ps[simc[r] % len(ps)]) #, label=sep[r][0][l])
			simc[r] += 1
			break	# Only plot the final iteration in each case

		# More than one iteration indicates crowding or bug-hunting
		if lastit <= 1:
			continue	# No more plots without the iterations

		# Bug-hunting?
		if sum([len(cv[1]) for cv in locations]) == 0 and len(lre[k]) > 0:
			if not k in figures[Fig.b][0]:
				figures[Fig.b][0][k] = plt.subplots()
				axb = figures[Fig.b][0][k][1]
				axb.set_xlabel("Iteration")
				axb.set_ylabel("Energy")
				axb.set_title(f"{args.results}")
			# Could bring down rec via lrrec to specify actual iterations?
			axb = figures[Fig.b][0][k][1]
			axb.plot(list(range(len(lre[k]))), lre[k], c=ps[lrec])
			lrec += 1
			continue
			
		# TODO Add crowder and subject pdb ids into plot titles?
		# 2D Crowder energy
		if len(lre[k]) > 0:
			if not k in figures[Fig.e][0]:
				figures[Fig.e][0][k] = plt.subplots()
				axe = figures[Fig.e][0][k][1]
				axe.set_xlabel("Iteration")
				axe.set_ylabel("Energy")
				axe.set_title("Proposal and accepted energy evolution")
			axe = figures[Fig.e][0][k][1]
			axe.plot(lre[k], c=ps[ec], label="Proposal")
			axe.plot(lra[k], c=ps[ec], linestyle='dashed', label="Accepted")
			ec += 1
			corner = 0.0
			for x in lre[k]:
				corner += x-lre[k][0]
			figures[Fig.e][2] = 'lower right' if corner > 0 else 'upper right'

		# 3D scatter for proposal positions and energies
		if len(lrsx[k]) > 0:
			if not k in figures[Fig.a][0]:
				fg3 = plt.figure()
				ax3 = fg3.add_subplot(111, projection='3d')
				figures[Fig.a][0][k] = (fg3, ax3)
				ax3.set_xlabel('x')
				ax3.set_ylabel('y')
				ax3.set_zlabel('z')
				ax3.set_title("Distribution of proposals")
			ax3 = figures[Fig.a][0][k][1]
			ax3.scatter(lrsx[k], lrsy[k], lrsz[k], c='k', marker='*')
			for i in range(len(lrvc[k])):
				(vc, qc, pc) = (lrvc[k][i], lrqc[k][i], lrpc[k][i])
				# The ridiculous colors charade is to fix matplotlib limitation
				# At least no null arrows here to be skipped, but see axc...
				ax3.quiver(vc[0], vc[1], vc[2], qc[0], qc[1], qc[2], \
							colors=pc+[cv for cv in pc for _ in range(2)], \
							linestyles=ls[i], label=lab[i])

		# This should move away from plots?
		# Dump 3D data to an 'R' table file - above 3D plot is weak
		if len(lrsx[k]) > 0:
			with open(f"results-{l}-{r}.txt", 'w') as f:
				ctr = 0
				print(f"status x y z u v w colour marker label", file=f)
				for n in range(len(sx)):
					ctr += 1
					print(f"{ctr} -1 {lrsx[k][n]} {lrsy[k][n]} {lrsz[k][n]} " \
						"0.0 0.0 0.0 k * subject", file=f)
				for i in range(len(lrvc[k])):
					for n in range(len(lrvc[k][i][0])):
						ctr += 1
						(vc, qc, pc) = (lrvc[k][i], lrqc[k][i], lrpc[k][i])
						print(f"{ctr} {i} {vc[0][n]} {vc[1][n]} {vc[2][n]} "
										f"{qc[0][n]} {qc[1][n]} {qc[2][n]} "
										f"{pc[n]} {ms[i]} {lab[i]}", file=f)

		# 3D scatter for initial and final positions
		if len(lrcli[k][0]) > 0:
			if not k in figures[Fig.c][0]:
				fgc = plt.figure()
				axc = fgc.gca(projection='3d')#add_subplot(111, projection='3d')
				figures[Fig.c][0][k] = (fgc, axc)
				axc.set_xlabel('x')
				axc.set_ylabel('y')
				axc.set_zlabel('z')
				axc.set_title("Initial and final crowder distribution")
			axc = figures[Fig.c][0][k][1]
			axc.scatter(lrsx[k], lrsy[k], lrsz[k], c='k', marker='*',
						label='subject')
			# Plot each crowder type
			for c in range(nct):
				(ccs, cli, clf) = (lrccs[k][c], lrcli[k][c], lrclf[k][c])
				qc = [[clf[cd][n]-cli[cd][n] for n in range(len(cli[0]))] \
						for cd in range(3)]
				# matplotlib skips null arrows but does not skip colours!
				f = [ccs[n] for n in range(len(qc[0])) \
						if [qc[cd][n] for cd in range(3)] != [0,0,0]]
				axc.quiver(cli[0], cli[1], cli[2], qc[0], qc[1], qc[2], \
								colors=f+[cv for cv in f for _ in range(2)], \
								label=header[3][c][0]+' move')
				# Now print dots for the unmoved crowders
				f = [n for n in range(len(qc[0])) \
						if [qc[cd][n] for cd in range(3)] == [0,0,0]]
				cli = [[cli[cd][n] for n in f] for cd in range(3)]
				f = [ccs[n] for n in f]
				axc.scatter(cli[0], cli[1], cli[2], \
							c=f+[cv for cv in f for _ in range(2)], \
							marker='o', label=header[3][c][0]+' unmoved')


		# 2D distance from centre by iteration and energy band
		if len(lrd[k][0]) > 0:
			if not k in figures[Fig.d][0]:
				figures[Fig.d][0][k] = plt.subplots()
				axd = figures[Fig.d][0][k][1]
				axd.set_xlabel("Iteration")
				axd.set_ylabel("Distance from centre (A)")
				axd.set_title("Distribution of distance by iteration and band")
			axd = figures[Fig.d][0][k][1]
			for i in range(len(lrd[k])):
				(d, its, pc) = (lrd[k][i], lrits[k][i], lrpc[k][i])
				axd.scatter(y=d, x=its, c=pc, marker=ms[i], label=lab[i])

		# 2D energy by distance from centre
		if len(lrpe[k][0]) > 0:
			if not k in figures[Fig.f][0]:
				figures[Fig.f][0][k] = plt.subplots()
				axf = figures[Fig.f][0][k][1]
				axf.set_xlabel("Distance from centre (A)")
				axf.set_ylabel("Energy (kJ/mol)")
				axf.set_title("Distribution of energy by distance")
			axf = figures[Fig.f][0][k][1]
			for i in range(len(lrpe[k])):
				(pe, d, cc) = (lrpe[k][i], lrd[k][i], lrcc[k][i])
				axf.scatter(y=pe, x=d, c=cc, marker=ms[i], label=lab[i])
			#(ave, avd) = (lrave[k], lravd[k])
			ave = [lrave[k][c] for c in range(len(lrct[k])) if lrct[k][c] > 3]
			avd = [lravd[k][c] for c in range(len(lrct[k])) if lrct[k][c] > 3]
			axf.plot(avd, ave, c='k', label="mean")

		# 2D average distance from centre
		if len(lravd[k]) > 0:
			if not k in figures[Fig.ad][0]:
				figures[Fig.ad][0][k] = plt.subplots()
				axad = figures[Fig.ad][0][k][1]
				axad.set_xlabel("Energy (kJ/mol)")
				axad.set_ylabel("Average Distance from centre (A)")
				axad.set_title("Average distance by energy")
			#ax.legend(loc='lower left', shadow=True)
			#edge = (max(ebc)-min(ebc))/10
			#ax.set_xlim(left=min(ebc)-edge,right=max(ebc)+edge)
			#ax.set_ylim(bottom=10*(min(avd)//10),top=10*(1+max(avd)//10))
			axad = figures[Fig.ad][0][k][1]
			corner = 0.0
			for c in range(len(lravd[k])):
				#	ax.text(eb[c], avd[c], ct[c], color=ca[c])
				(ebc, avd, sdd) = (lrebc[k][c], lravd[k][c], lrsdd[k][c])
				(ca, lbc, ct) = (lrca[k][c], lrlbc[k][c], lrct[k][c])
				axad.errorbar(ebc, avd, yerr=sdd, color=ca, label=lbc, \
								fmt=('o' if ct > 1 else 'D'))
				corner += avd-lravd[k][0]
			figures[Fig.ad][2] = 'lower right' if corner > 0 else 'upper right'
			#ax.scatter(y=avd, x=list(range(len(avd))), c=ps)


		# 2D rotation relative to vector to centre
		if len(lrtheta[k][0]) > 0:
			if not k in figures[Fig.t][0]:
				figures[Fig.t][0][k] = plt.subplots()
				axt = figures[Fig.t][0][k][1]
				axt.set_xlabel("Iteration")
				axt.set_ylabel("Axis angle to centre (radians)")
				axt.set_title("Distribution of axis angle by iteration")
			axt = figures[Fig.t][0][k][1]
			for i in range(len(lrtheta[k])):
				(theta, its, pc) = (lrtheta[k][i], lrits[k][i], lrpc[k][i])
				axt.scatter(y=theta, x=its, c=pc, marker=ms[i], label=lab[i])

		# 2D average rotation relative to vector to centre
		if len(lravt[k]) > 0:
			if not k in figures[Fig.at][0]:
				figures[Fig.at][0][k] = plt.subplots()
				axat = figures[Fig.at][0][k][1]
				axat.set_xlabel("Energy (kJ/mol)")
				axat.set_ylabel("Average axis angle to centre (radians)")
				axat.set_title("Average angle by energy")
				#axat.legend(loc='lower left', shadow=True)
			#edge = (max(ebc)-min(ebc))/10
			#ax.set_xlim(left=min(ebc)-edge,right=max(ebc)+edge)
			#ax.set_ylim(bottom=0,top=pi)
			axat = figures[Fig.at][0][k][1]
			for c in range(len(lravt[k])):
				#	ax.text(eb[c], avt[c], ct[c], color=ca[c], label=lb[c])
				(ebc, avt, sdt) = (lrebc[k][c], lravt[k][c], lrsdt[k][c])
				(ca, lbc, ct) = (lrca[k][c], lrlbc[k][c], lrct[k][c])
				axat.errorbar(ebc, avt, yerr=sdt, color=ca, label=lbc, \
								fmt=('o' if ct > 1 else 'D'))
			#ax.scatter(y=avt, x=list(range(len(avt))), c=ps)

		# 2D density plot for angles
		if len(lrdtx[k]) > 0:
			if not k in figures[Fig.dt][0]:
				figures[Fig.dt][0][k] = plt.subplots()
				axdt = figures[Fig.dt][0][k][1]
				axdt.set_xlim(left=0,right=pi)
				axdt.set_xlabel("Axis angle to centre (radians)")
				axdt.set_ylabel("Density")
				axdt.set_title("Angle densities by energy")
			axdt = figures[Fig.dt][0][k][1]
			for c in range(len(ps)):
				(dtx, dty) = (lrdtx[k][c], lrdty[k][c])
				axdt.plot(dtx, dty, c=ps[c], label=lb[c])


# Show and save figures
for fgn in figures:
	ctr = 0
	fgl = figures[fgn]
	for k in fgl[0]:
		fg = fgl[0][k]
		if len(fg) == 0:
			continue
		if fgn.name not in plotfigs:
			fg[0].clf()
			plt.close(fg[0])
			continue
		if fgl[2] != None:
			fg[1].legend(loc=fgl[2], prop={'size':6}, shadow=True)
		fg[0].savefig(fgl[1] + ("" if ctr == 0 else f"-{ctr}") + '.png')
		ctr += 1

# Display all figures
plt.show()

