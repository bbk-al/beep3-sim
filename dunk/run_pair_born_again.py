#!/usr/bin/python
from pybeep import BEEP, Mesh, Vector, Quaternion
from geometry import _rand_rot
from constants import calculate_kappa
import sys
from string import atof

qual_pts = 0
quad_pts = 1
nbsize = 2000
Dsolvent = 80.0
Dprotein = 1.0
kappa = 0.0
GMRES_tolerance = 1e-6
GMRES_max_iterations = 100

no_rotation = Quaternion(1,0,0,0)
centre_crystal_ache = Vector(0.0,0.0,0.0)
centre_crystal_fas = Vector(1.0,0.0,0.0)
axis = (centre_crystal_fas - centre_crystal_ache)
crystal_separation = axis.length() 
axis.normalise()
minimum_separation = 3.0
ache_location = Vector(0,0,0)

mtz1 = sys.argv[1]
mtz2 = sys.argv[2]

for dummy in [0]:
    beep = BEEP(Dsolvent, kappa, quad_pts, qual_pts, nbsize, False)
    beep.load_library_mesh(mtz1)
    #beep.load_library_mesh(mtz2)

    for iteration in range(0,50,2):
        
        fas_location = ache_location + axis*(crystal_separation+minimum_separation + iteration)
        beep.clear_mesh_instances()
        beep.insert_mesh_instance(0, ache_location, no_rotation, Dprotein)
        #beep.insert_mesh_instance(1, fas_location, no_rotation, Dprotein)
        beep.solve(GMRES_tolerance, GMRES_max_iterations)
        beep.reset_library_fh_vals();
        total_energy = beep.calculate_energies()
