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

    print "\tarea=%f\trad=%f\tvol=%f" %(total_area, m.get_radius(), m.calculate_volume() / 6)
    #print "area=%f rad=%f vol=%f" %(total_area, m.get_radius(), m.calculate_volume() / 6)

