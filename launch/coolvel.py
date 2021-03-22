import os.path
import muram2hanlert as m2h
import argparse

# "Cool Corona" MURaM simulation
# Smoothed with savgol_filter(x, 9, 1)
# Sampled every 2 (every 32 km)
# 70 height points
# Velocities enabled

dir3D = "/glade/p/hao/radmhd/rempel/SSD_CHR/dyn_25x8Mm_16_pdmp_1_ext_zxy_pdm/3D"
jobroot = os.path.expanduser("~/muram2hanlert")
jobname = os.path.basename(__file__)[0:-3] # name of file, minus .py suffix
iteration = 16000
project = "NHAO0016"# "P22100000"
email = "egeland@ucar.edu"
res = 1536 # MURaM row/col resolution
step = 8 # sampling frequency

# Build ystart and ystop range from command line arguments
parser = argparse.ArgumentParser(description='Compute the coolvel HanleRT forward model on Cheyenne.')
parser.add_argument('ystart', type=int, help='starting y to submit')
parser.add_argument('Ny', type=int, help='Number of  y rows to submit')
parser.add_argument('--check-height', action='store_true', help='submit nothing; check the min(max(height))')
parser.add_argument('--print-only', action='store_true', help='submit nothing; just print what would be done')
parser.add_argument('--prepare-only', action='store_true', help='prepare job directories without submitting them')
args = parser.parse_args()
ystart = args.ystart
Ny = args.Ny
ystop = ystart +  Ny * step
N = int(res/step) # samples per row/col
zstart = 0
zstop = N*step
if ystop > (res - step):
    print(f"ERROR: requested end row {ystop} is out of bounds for this MURaM cube")
    exit(-1)

# Check min(max(height)) for cube.
if args.check_height:
    min_height = 0
    N_short = m2h.shortest_column(dir3D, iteration, min_height=min_height)
    print(f"shortest column of iteration {iteration} has N={N_short} above (including) height=0")
    exit(0)

# Define the smoothing filter
from scipy.signal import savgol_filter
def smooth(x):
    return savgol_filter(x, 17, 1)

# Iterate and prepare/submit jobs
for y in range(ystart, ystop, step):
    for z in range(zstart, zstop, step):
        print("Preparing column", (iteration, y, z))
        if args.print_only:
              continue
        m2h.prepare_job(dir3D, jobroot, jobname, iteration, y, z, project, email,
                        min_height=-192.0, N_ixs=132, N_ixs_ref='min', sample=2, zerovel=False, smooth=smooth,
                        intemp=['INPUT-step1.template', 'INPUT-step2.template'],
                        subtemp='qsub-2step.template')
        if not args.prepare_only:
            m2h.start_job(jobroot, jobname, iteration, y, z)
