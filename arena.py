# Author: Adam Light <la002@mail.cryst.bbk.ac.uk>
"""BEEP Arena base class

This module declares the Arena base class which provides the interface
for specialised forms of Arena model.

Example use:
    from arena import Arena

	class MyArena(Arena)
	raise CollisionError

The module contains the following public classes:
    - Arena -- base class for Arena models
"""
__version__ = '1.0'
__all__ = [
    'Arena',
]

from abc import ABC, abstractmethod
from typing import Tuple, Any
from pybeep import Vector, Quaternion, Mesh
import logging as log

class CollisionError(BaseException):
	pass


class Arena(ABC):
	""" Base class providing an interface for arena creation and management

	Errors are logged via the standard logging module.
	
    Class Attributes:
    - no class attributes are part of the interface

    Class Methods:
    - no class methods are part of the interface

    Object Attributes:
    - no object attributes are part of the interface

    Object Methods:
	-- clear() - Clear occupants from arena
	-- isOccupied - Indicate if a 3-D position is occupied
	-- insertMesh - Insert Mesh object into arena, marking occupancy
	-- occupy - Mark a location as occupied
	-- move - Move an occupant
    """
	### Private class attributes

	### Constructors
	# None defined, not even a default constructor

	### Abstract methods
	""" Clear occupants from arena of specified type and id """
	@abstractmethod
	def clear(self, reftype: int = None, refid: int = None) -> None:
		raise NotImplementedError

	""" Indicate if a 3-D position is inside an occupation region """
	@abstractmethod
	def isOccupied(self, location: Vector) -> bool:
		raise NotImplementedError

	""" Return the v-th vacant slot """
	@abstractmethod
	def vacancy(self, v: int) -> Any:
		raise NotImplementedError

	""" Return the corresponding location as a vector """
	@abstractmethod
	def getLocation(self, ref: Any) -> Vector:
		raise NotImplementedError

	""" Insert Mesh object into arena, marking the resulting occupancy.
	Note that only the centre of the Mesh is guaranteed to be marked.
	It is up to the caller to check if a move is to inside a Mesh. """
	@abstractmethod
	def insertMesh(self, m: Mesh, t: int, n: int) -> None:
		raise NotImplementedError

	""" Occupy referenced location with the specified type """
	@abstractmethod
	def occupy(self, ref: Any, t: int, n: int) -> Vector:
		raise NotImplementedError

	""" Move occupant to vacant=int vacancy, or to to=ref """
	@abstractmethod
	def move(self, ref: Any, **kwargs) -> Tuple:
		raise NotImplementedError

