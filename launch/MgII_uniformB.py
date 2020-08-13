import os.path
import muram2hanlert as m2h
import numpy as np

jobroot = os.path.expanduser("~/muram2hanlert")
jobname = 'MgII_uniformB'
project = "P22100000"
email = "egeland@ucar.edu"


dB = 1.
Bmax = 100.
inc = 60. # degrees
azi = 180. # degrees
Bmag = np.arange(dB, Bmax + dB, dB)
Binc = np.ones(Bmag.size) * inc
Bazi = np.ones(Bmag.size) * azi


B = np.array([Bmag, Binc, Bazi]).T
jobpaths = m2h.prepare_uniformB_jobs(jobroot, jobname, B, project, email,
                                     intemp="INPUT_MgII_uniformB.template")
for j in jobpaths:
    m2h.start_jobpath(j)
