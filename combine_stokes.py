#!/usr/bin/env python

import sys
import hanlert.io

jobpath = sys.argv[1]

allstokes, th, mu, ph, L = hanlert.io.combine_stokes(jobpath)
outfile = hanlert.io.stokes_to_fits(jobpath, uniform=True, overwrite=True)
print("Wrote", outfile)
