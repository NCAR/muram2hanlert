import os.path
import muram2hanlert as m2h
import numpy as np

jobroot = os.path.expanduser("~/muram2hanlert")
jobname = 'MgII_uniformB'
project = "P22100000"
email = "egeland@ucar.edu"


def make_B(dB=1., Bmax=200., dinc=15., incmax=180., azi=180.): 
    result = [] 
    for inc in np.arange(0., incmax + dinc, dinc): 
        for B in  np.arange(dB, Bmax + dB, dB): 
            Bvec = np.array([B, inc, azi]) 
            result.append(Bvec) 
    return np.vstack(result) 

B = make_B()

print("Preparing", len(B), "jobs...")
jobpaths = m2h.prepare_uniformB_jobs(jobroot, jobname, B, project, email,
                                     intemp="INPUT_MgII_uniformB.template")
print(len(jobpaths), "jobs prepared.\n")

for j in jobpaths:
    print("Starting job:", j)
    m2h.start_jobpath(j)
