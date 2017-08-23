#!/usr/bin/env python3
# Author: Adam Light <la002@mail.cryst.bbk.ac.uk>
"""MRes Bioinformatics with Systems Biology Project

This script converts EDTSurf PLY files to GTS format.
It does a basic job and is not a general PLY to GTS converter.

Example use:
	ply2gts.py file-prefix
converts file-prefix.ply to file-prefix.gts and file-prefix.xyz
"""
__version__ = '1.0'
__all__ = [
]

# imports
from typing import Iterable, Tuple, List, Dict
from pybeep import Vector
from sys import stdout
import argparse
import logging as log

# Types
Coord = Tuple[float, float, float] # Coordinates x,y,z

# Utilities

# Main program

# Set up command line parsing
parser = argparse.ArgumentParser(description=\
				'Convert EDTSurf PLY file to GTS format.')
# --loglevel
parser.add_argument('--loglevel', metavar='(INFO|WARNING|ERROR)',
					dest='loglevel', default="INFO",
                    help='minimum log level to capture: INFO, WARNING, ERROR')
# --logfile
parser.add_argument('--logfile', metavar='log', type=argparse.FileType('a'),
					dest='log', default=stdout, help='name of log file')
# file-prefix
parser.add_argument('file-prefix', metavar='file-prefix',
                    help='prefix of input ply file')

# Interpret arguments
args = vars(parser.parse_args())
plyfile = args['file-prefix']+".ply"
gtsfile = args['file-prefix']+".gts"
xyzfile = args['file-prefix']+".xyz"
loglevel = args['loglevel']
logstream = args['log']

# Set up logging - if to stdout, assume caller handles time and module name
if logstream == stdout:
	fmt="%(levelname)s:%(message)s"
else:
	fmt="%(asctime)s %(module)s %(levelname)s:%(message)s"
log.basicConfig(stream=logstream, format=fmt,
                level=getattr(log, loglevel.upper()))

# Produce the GTS file first
perm = (1, 2, 2, 0, 0, 1)
(fn, vn, en, ec) = (0, 0, 0, 0)
(edge, face, vertex, normal, vertri) = (dict(), list(), list(), list(), dict())
out = open(gtsfile,'w')
with open(plyfile) as f:
	state = 0
	n = 0
	for line in f:
		n += 1
		line.strip()

		# Read header
		if state == 0:
			if line[0:15] == "element vertex ":
				try:
					vn = int(line[15:])
				except:
					log.error(f"Integer not found for vertex count, line {n}")
					exit(1)
			elif line[0:13] == "element face ":
				try:
					fn = int(line[13:])
				except:
					log.error(f"Integer not found for face count, line {n}")
					exit(1)
				if fn % 2 != 0:
					log.error(f"Weird face count {fn}, line {n}")
					exit(1)
			elif line[0:10] == "end_header":
				en = int(3*fn/2)
				print(f"{vn} {en} {fn} GtsSurface GtsFace GtsEdge GtsVertex",
					  file=out)
				state = 1
		# Vertices
		elif state == 1:
			ll = line.split()
			print(f"{ll[0]} {ll[1]} {ll[2]}", file=out)
			try:
				vertex.append(Vector(*[float(ll[i]) for i in range(3)]))
			except:
				log.error(f"Bad vertex {ll[0:3]}, line {n}")
				exit(1)
			vn -= 1
			if vn == 0:
				state = 2
		# Faces, er, edges
		elif state == 2:
			ll = line.split()
			if ll[0] != "3":
				log.error(f"Weird face vertex count {ll[0]}, line {n}")
				exit(1)
			# define and store unique edges and define faces in terms of these
			try:
				vix = [int(ll[i]) for i in range(1,4)]
			except:
				log.error(f"Bad face vertex index {ll[1:4]}, line {n}")
				exit(1)
			face.append(list())
			for i in range(3):
				k = tuple(sorted((vix[perm[2*i]],vix[perm[2*i+1]])))
				if k not in edge:
					ec += 1
					edge[k] = ec
					print(f"{k[0]+1:d} {k[1]+1:d}", file=out)
				face[-1].append(edge[k])

				# Add the triangle (face) to the list for each vertex
				v = vertex[vix[i]]
				if v in vertri:
					vertri[v].append(len(face)-1)
				else:
					vertri[v] = [len(face)-1]
			if ec > en:
				log.error(f"Sorry, goofed on edge count {ec} > {en}, line {n}")
				exit(1)
			# Calculate the normal to this face and record it
			v1 = vertex[vix[1]]-vertex[vix[0]]
			v2 = vertex[vix[2]]-vertex[vix[0]]
			norm = v1.cross(v2)
			#norm.normalise() -- unnormalised makes value proportional to area
			normal.append(norm)

# Finally, output the new faces in the gts file
for nf in face:
	print(f"{nf[0]:d} {nf[1]:d} {nf[2]:d}", file=out)
out.close()

# Now generate the xyz file
out = open(xyzfile,'w')
for v in vertex:
	norm = Vector(0,0,0)
	for fix in vertri[v]:
		norm = norm + normal[fix] # weighted by face area
	norm.normalise()
	print(f"{v.x:.6f} {v.y:.6f} {v.z:.6f} " +
		  f"{norm.x:.6f} {norm.y:.6f} {norm.z:.6f}", file=out)
out.close()

# Exit cleanly
exit(0)

