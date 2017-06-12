#!/usr/bin/python
# -*- coding: utf-8 -*-

from pybeep import *

if __name__=="__main__":
    import sys

    # usage: ./dunk-kinemage.py fasciculin.mtz
    beep = BEEP(80.0, 0.0, 1, 0, 500, False)
    beep.load_library_mesh(sys.argv[1])
    beep.load_library_mesh(sys.argv[2])
    beep.insert_mesh_instance(0, Vector(0,0,0), Quaternion(1,0,0,0), 1.0)
    beep.insert_mesh_instance(1, Vector(3,0,0), Quaternion(1,0,0,0), 1.0)
    beep.solve(1e-6, 100)
    beep.reset_library_fh_vals()
    beep.calculate_energies()
    beep.kinemage("/d/user5/gd001/output.kin")
