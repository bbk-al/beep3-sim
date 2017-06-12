#!/usr/bin/env python3
from pybeep import Vector


u=Vector(23.3805,-24.5801,-0.105747)
v=Vector(15.558,-3.13598,-6.21348)
inc=(u-v)
inc.normalise()
s=v-inc*24.0
print(s,v,inc)
