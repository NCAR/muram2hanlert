import os.path
import muram2hanlert as m2h

dir3D = os.path.expanduser("~/Pointers/MURaM4CSAC/3D")
jobroot = os.path.expanduser("~/muram2hanlert")
jobname = 'first100'
iteration = 12000
project = "NHAO0016"
email = "egeland@ucar.edu"

N = 10
step = 4
for y in range(0, N*step, step):
    for z in range(0, N*step, step):
        m2h.prepare_job(dir3D, jobroot, jobname, iteration, y, z, project, email, sample=2)
        m2h.start_job(jobroot, jobname, iteration, y, z)
