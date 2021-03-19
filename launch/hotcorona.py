import os.path
import muram2hanlert as m2h

dir3D = "/glade/p/hao/radmhd/rempel/SSD_CHR/dyn_25x16Mm_32_pdmp_1_zxy_tvd_low_eps/3D"
jobroot = os.path.expanduser("~/muram2hanlert")
jobname = os.path.basename(__file__)[0:-3] # name of file, minus .py suffix
iteration = 40000
project = "P22100000"
email = "egeland@ucar.edu"

N = 192 # last is 768; domain is 768
start = 0
step = 4
for y in range(start, N*step, step):
    for z in range(start, N*step, step):
        m2h.prepare_job(dir3D, jobroot, jobname, iteration, y, z, project, email, 
                        min_height=-192.0, N_ixs=73, N_ixs_ref='min', zerovel=True)
        m2h.start_job(jobroot, jobname, iteration, y, z)
