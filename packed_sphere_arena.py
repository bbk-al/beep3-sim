#!/usr/bin/env python3
# Author: Adam Light <la002@mail.cryst.bbk.ac.uk>
"""BEEP Packed Sphere Arena class

This module provides a subclass of Arena based on hexagonally close-packed
spheres, each of which provides a space in which molecule models can be
freely rotated without risk of collision.

Example use:
    from packed_sphere_arena import PackedSphereArena

	psa = PackedSphereArena(...)
	psa.insertMesh(...)
	psa.clear()

The module contains the following public classes:
    - PackedSphereArena -- close-packed spheres as spaces for molecules
"""
__version__ = '1.0'
__all__ = [
    'PackedSphereArena',
]

from arena import Arena, CollisionError
from math import sqrt
from typing import Iterable, Tuple
from pybeep import MeshInstance, Vector, Quaternion
import logging as log

class PackedSphereArena(Arena):
	""" Creates an Arena formed of packed spheres and manages occupancy.

	Position Arguments:
    - radius -- the radius of the entire arena (float)
	Errors are logged via the standard logging module.
	
    Class Attributes:
    - no class attributes are part of the interface

    Class Methods:
    - no class methods are part of the interface

    Object Attributes:
    - radius -- radius of the arena
    - all others are implementation-dependent

    Object Methods:
    - >>> (see Arena)
    """
	# User-defined types
	PSARef = Iterable[Tuple[int, int, int]] # Index into self._psa and pso


	### Private class attributes

	### Constructors
	""" Constructor from non-XML specification text stream """
	def	__init__(self, a: float, size: float, centre: Vector):
		""" Constructor with packed sphere radius a, arena radius size """
		# Set the arena size
		if size <= a:
			size = a
		self.radius = size
		self.centre = centre
		# Packed sphere radius, half row height and half layer height
		(self._rx, self._ry, self._rz) = (a, sqrt(3)*a/2, sqrt(2/3.0)*a)
		log.debug(f"Packed sphere radius {self._rx}, centre {self.centre}")
		# Arena dimensions in packed spheres, rows and layers
		self._psx = int((self._rx+size-1e-3) / (2*self._rx))
		self._psy = int((self._ry+size-1e-3) / (2*self._ry))
		self._psz = int((self._rz+size-1e-3) / (2*self._rz))
		# Build the arena: x,y,z at least 1, and 1 means only 1 sphere/row/layer
		self._psa = dict()
		for layer in range(-self._psz+1, self._psz):
			for row in range(-self._psy+1, self._psy):
				start = centre + Vector(((layer+row)%2)*a,
										sqrt(3)*(row+(layer%2)/3.0)*a,
										2*sqrt(2/3.0)*layer*a)
				for sphere in range(self._psx): # Reflection captured below
					# Intention is that arena is spherical (roughly)
					pv = start+Vector(2*a,0,0)*sphere
					if (pv-self.centre).length() > self.radius:
						continue
					# As plus is in sphere, so is minus...
					self._psa[(sphere,row,layer)] = pv
					log.debug(f"init ({sphere},{row},{layer}) = %s" % \
								(_asString(self._psa[(sphere,row,layer)])))
					self._psa[(-sphere,row,layer)] = \
						start-Vector(2*a,0,0)*sphere
					log.debug(f"init (-{sphere},{row},{layer}) = %s" % \
								(_asString(self._psa[(-sphere,row,layer)])))

		# Initialise sphere occupancy
		self._pso = dict()
		self.clear()

		# Calculate the volume of the arena
		self._psvoleq = 4*(a**3)*sqrt(2) # Volume equivalent of packed sphere
		self.volume = len(self._psa)*self._psvoleq

	""" Return the number of free slots """
	def capacity(self) -> int:
		return sum([1 for s in self._pso if self._pso[s][0] == 0])

	""" Clear all occupants from arena """
	def clear(self, reftype: int = None, refid: int = None) -> None:
		keys = [k for k in self._psa \
			if ((self._pso[k][0] == reftype) if reftype != None else True) \
			and ((self._pso[k][1] == refid) if refid != None else True)]
		for k in keys:
			self._pso[k] = (0,0)  # (Type, Id) Type 0 means no occupant

	""" Indicate if a 3-D position is inside an occupation region (sphere).
	Note:  spaces in between spheres permit collisions, in theory. """
	def isOccupied(self, location: Vector) -> bool:
		ref = self._getRef(location)
		return self._pso[ref][0] != 0 if ref != None else False

	""" Return the v-th vacant slot """
	def vacancy(self, v: int) -> PSARef:
		# Note that the order is irrelevant, v is just to randomise
		vacant = [r for r in self._psa if self._pso[r][0] == 0]
		if v >= len(vacant) or v < 0:
			return None
		return vacant[v]

	""" Convert a sphere reference to a 3-D position
	Note this does not imply the reference exists in the arena """
	def getLocation(self, ref: PSARef) -> Vector:
		if ref in self._psa:
			return self._psa[ref]
		a = self._rx
		(sphere, row, layer) = ref
		return self.centre + Vector((2*sphere+(layer+row)%2)*a,
									sqrt(3)*(row+(layer%2)/3.0)*a,
									2*sqrt(2/3.0)*layer*a)

	""" Insert Mesh into arena, marking overlapped spheres as occupied.
	Note that this only inserts the mesh, not its interior!
	Objects can extend outside the arena and additional spheres are added. """
	def insertMesh(self, m: MeshInstance, t: int, n: int) -> None:
		# Check which packed sphere each vertex is in, if any
		#[TBD] Issue: a triangle could slice the edge of a sphere...
		# -- ignore it:  small triangles and large spheres...rare issue
		log.debug(f"insertMesh {t} {n}, {m.num_node_patches} patches")
		#meshrad = 0.0
		for i in range(m.num_node_patches):
			vert = m.get_node_patch(i).vector()
			#meshrad = max(meshrad, (vert-m.get_xyz_offset()).length())
			ref = self._getRef(vert)
			# Check the vertex is inside the packed sphere before occupying
			vrs = vert-self.getLocation(ref)
			# Insert and occupy a sphere to cover a mesh point outside the arena
			if vrs.length() <= self._rx:
				self.occupy(ref, t, n)
				#log.debug(f"Vertex {vert}, ref {ref}, centre {self._psa[ref]}, "
				#		  f"difference {vrs}, separation {vrs.length()}")
			# log.debug(f"vert {vert}, centre %s" % (self._psa[ref]))
		#log.debug(f"radius: insertMesh {meshrad} vs mesh {m.get_radius()}")

	# Throws custom exception CollisionError if a collision would occur
	# and rejects the occupation
	def occupy(self, ref: PSARef, occupantType: int, occupantId: int) -> Vector:
		if ref not in self._psa:
			self._insertSphere(ref)
		if self._pso[ref][0] != 0:
			if self._pso[ref] != (occupantType, occupantId):
				log.warning(f"Collision at {ref} type {occupantType}/ "
							f"{self._pso[ref][0]}, id {occupantId}/"
							f"{self._pso[ref][1]}")
				raise CollisionError
		else:
			log.debug(f"occupy {ref} type {occupantType}, id {occupantId}")
			self._pso[ref] = (occupantType, occupantId)
		return self._psa[ref]

	""" Move existing occupant at ref to vacant=int vacancy, or to to=ref
	sphere """
	def move(self, ref: PSARef, **kwargs) -> Tuple[Vector, PSARef]:
		(cty,cid) = (self._pso[ref][0], self._pso[ref][1])
		self._pso[ref] = (0, 0)		# Empty the 'from' first for null moves
		if 'vacant' in kwargs:
			v = kwargs['vacant']
			rv = self._occupy(v, cty, cid)
		elif 'to' in kwargs:
			to = kwargs['to']
			self.occupy(to, cty, cid)
			rv = (self._psa[to], to)
		return rv

	# Non-interface methods
	""" Output arena for plotting in R or matplotlib """
	def plot(self, filename: str) -> None:
		with open(filename, 'w') as f:
			s = self._rx
			print("x y z c s", file=f)
			r = 1	# record number for r data table input
			for ref in self._psa:
				c = self._pso[ref][0]
				if c == 0:	# unoccupied
					continue
				if c > 0:	# subject - decrement to get to library id
					c -= 1
				v = self._psa[ref]
				print(f"{r} {v.x:.3f} {v.y:.3f} {v.z:.3f} {c} {s:.3f}", file=f)
				r += 1


	### Private methods

	""" Occupy v-th vacant sphere with the specified type.
	Raises CollisionError if v is larger than the number of vacancies. """
	def _occupy(self, v: int, t: int, n: int) -> Tuple[Vector, PSARef]:
		vacant = [r for r in self._psa if self._pso[r][0] == 0]
		if v < len(vacant) and v >= 0:
			ref = vacant[v]
		else:
			log.debug(f"Collision because no room left, type {t} id {n}")
			raise CollisionError
		self.occupy(ref, t, n)
		return (self._psa[ref], ref)

	# Convert a 3-D position to a sphere reference (PSARef)
	# Note this does not check the reference exists in the arena
	def _getRef(self, location: Vector) -> PSARef:
		a = self._rx
		(cx,cy,cz) = (self.centre.x,self.centre.y,self.centre.z)
		layer = intRef(location.z-cz-(a-self._rz), self._rz)
		row = intRef((location.y-cy-(a-self._ry)-sqrt(3)*(layer%2)*a/3.0), self._ry)
		sphere = intRef((location.x-cx-((layer+row)%2)*a), self._rx)
		mind2 = 3*a*a
		ref = (sphere, row, layer)
		for l in [layer,layer+1]:
			dz = location.z-cz-2*sqrt(2/3.0)*l*a
			for r in [row,row+1]:
				dy = location.y-cy-sqrt(3)*(r+(l%2)/3.0)*a
				for s in [sphere,sphere+1]:
					dx = location.x-cx-(2*s+(l+r)%2)*a
					d2 = dx*dx+dy*dy+dz*dz 
					if d2 < mind2:
						ref = (s, r, l)
						mind2 = d2
		#log.debug(f"getRef({location.x},{location.y},{location.z})={ref}")
		return ref

	# Insert a sphere at the specified reference
	def _insertSphere(self, ref: PSARef) -> None:
		if ref in self._psa:
			return
		self._psa[ref] = self.getLocation(ref)
		log.debug(f"Added {ref} at " \
			  f"({self._psa[ref].x},{self._psa[ref].y},{self._psa[ref].z})")
		# Set new sphere as unoccupied
		self._pso[ref] = (0, 0)
		# Update the arena volume
		self.volume += self._psvoleq

# Module utilities
def _asString(v: Vector) -> str:
	return "(%f, %f, %f)" % (v.x, v.y, v.z)

def intRef(coord: float, radius: float):
	return int((coord + radius) // (2*radius))


# Declare the subclass status
#PackedSphereArena.register(Arena)

# No main program, so used for testing
if __name__== "__main__":
	log.basicConfig(level=getattr(log, "DEBUG"))
	psa = PackedSphereArena(1,10,Vector(0,0,0))
	print("Capacity starting at ", psa.capacity())
	(v, ref) = psa._occupy(0, 1, 0)
	print("Occupied at ", v, ref)
	(v, ref2) = psa.move(ref, vacant=2)
	print("Moved to ", v, ref2)
	(v, ref3) = psa.move(ref2, to=ref)
	print("Moved back to ", v, ref3)
	print("isOccupied=", psa.isOccupied(v))
	print("Capacity is now ", psa.capacity())
	print(f"Ref for {v} is ", psa._getRef(v))
	try:
		psa.occupy(ref, 1, 0)
		print("No collision")
	except:
		print("Error: collision detected")
	try:
		psa.occupy(ref, 1, 1)
		print("Error: no collision detected")
	except:
		print("Collision detected ok")
	psa.clear()
	print("Cleared, capacity is now ", psa.capacity())
	print("isOccupied=", psa.isOccupied(v))
