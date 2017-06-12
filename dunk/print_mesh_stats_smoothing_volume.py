#!/usr/bin/python
# -*- coding: utf-8 -*-
import pybeep

if __name__=="__main__":

    import sys
    from math import sqrt
    from random import uniform
    import constants

    mesh_filename = sys.argv[1]
    m = pybeep.Mesh(mesh_filename)
    total_area = sum([n.bezier_area() for n in m.node_patches])

    print "vol:",m.calculate_volume() / 6

