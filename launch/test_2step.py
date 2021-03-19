import os.path
import muram2hanlert as m2h

dir3D = "/glade/p/hao/radmhd/rempel/SSD_CHR/dyn_25x8Mm_16_pdmp_1_ext_zxy_pdm/3D"
jobroot = os.path.expanduser("~/muram2hanlert")
jobname = os.path.basename(__file__)[0:-3] # name of file, minus .py suffix
iteration = 16000
project = "NHAO0016"# "P22100000"
email = "egeland@ucar.edu"

from scipy.signal import savgol_filter
def smooth(x):
    return savgol_filter(x, 17, 1)

y = 0
z = 0
m2h.prepare_job(dir3D, jobroot, jobname, iteration, y, z, project, email,
                N_ixs=140, sample=2, zerovel=False, smooth=smooth,
                intemp=['INPUT-step1.template', 'INPUT-step2.template'],
                subtemp='qsub-2step.template')
m2h.start_job(jobroot, jobname, iteration, y, z)
