import os.path
import muram2hanlert as m2h
import numpy as np

jobroot = os.path.expanduser("~/muram2hanlert")
jobname = 'test_uniformB'
project = "P22100000"
email = "egeland@ucar.edu"

Bmag = np.array([20.])
Binc = np.array([12.0])
Bazi = np.array([180.0])
B = np.array([Bmag, Binc, Bazi]).T
jobpaths = m2h.prepare_uniformB_jobs(jobroot, jobname, B, project, email,
                                     intemp="INPUT_MgII_uniformB.template", overwrite=True)
m2h.start_jobpath(jobpaths[0])
