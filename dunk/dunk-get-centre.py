#!/usr/bin/python
# -*- coding: utf-8 -*-

from pybeep import *

import pqrtools
pqr2xyzqr = pqrtools.pqr2xyzqr

import os
import shutil
import tempfile
from os.path import basename, splitext

def print_centre(mesh_filename, pqr_filename):

    temp_dir = tempfile.mkdtemp(suffix=".beep-prepare")
    
    try:
        stem_filename, ext = splitext(basename(pqr_filename)) # remove the extension
        stem_filename = os.path.join(temp_dir, stem_filename)
        xyzqr_filename = "%s.xyzqr" %(stem_filename)
        pqr2xyzqr(pqr_filename, xyzqr_filename)
        
        stem_filename, ext = splitext(basename(mesh_filename))
        assert(ext == ".gts" or ext == ".off")
        
        mesh = Mesh(mesh_filename, xyzqr_filename, True)

        print "centre is"
        print mesh.get_centre()
        
    finally:
        shutil.rmtree(temp_dir)
    
    return

if __name__=="__main__":
    import sys
    # usage: ./dunk-get-centre.py fasciculin.gts fasciculin.pqr
    print_centre(sys.argv[1], sys.argv[2])
    
