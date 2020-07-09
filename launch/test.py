import os.path
import muram2hanlert as m2h

dir3D = os.path.expanduser("~/Pointers/MURaM4CSAC/3D")
jobroot = os.path.expanduser("~/muram2hanlert")
jobname = 'test'
iteration = 12000
y = 0
z = 0
project = "NHAO0016" # "P22100000"
email = "egeland@ucar.edu"

m2h.prepare_job(dir3D, jobroot, jobname, iteration, y, z, project, email, N_ixs=140, sample=2, zerovel=True)
m2h.start_job(jobroot, jobname, iteration, y, z)
