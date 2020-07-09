from collections import OrderedDict
import os
import os.path
import time
import re
import shutil
import numpy as np
import muram
import hanlert.io
from . import utils

def write_col(col, filepath, vmicro=None, zerovel=False, density_type='rho', tau_scale=False, 
              min_height=-100.0, tau1_ix=None, max_tau=20., N_ixs=None, sample=1, **kwargs):
    
    # Atmosphere
    #
    # Select only heights above the defined minimum
    if not tau_scale:
        if tau1_ix is None:
            tau1_ix = (np.abs(col.tau - 1.0)).argmin()
        height = (col.X - col.X[tau1_ix]) / 1e5 # km
        sel = height >= min_height
    else:
        height = col.tau
        sel = height <= max_tau

    # Optionally select a fixed number of grid points from the top
    # Overrides min_height/max_tau settings
    if N_ixs is not None:
        sel = np.zeros(height.size, dtype='bool')
        sel[-N_ixs:] = True
        
    # Optionally select only every nth sample
    # Careful to keep the deepest sample from selection above
    sel2 = np.zeros_like(height, dtype='bool') # All False
    min_height_ix = np.where(sel)[0][0] # smallest height / biggest tau
    offset = min_height_ix % sample
    sel2[offset::sample] = True # Every nth True, keeping min_height_ix using offset
    sel = sel & sel2 # AND
    
    # Only pgas and rho are easily supported by MURaM
    if density_type == 'pgas':
        density = col.P # dyn/cm^2
    elif density_type == 'rho':
        density = col.rho # g/cm^3
    else:
        raise Exception("Unsupported density option: "+density_type)
    
    zeros = np.zeros_like(col.x)
    if vmicro is None:
        vmicro = zeros
    if zerovel:
        vmacro = zeros
    else:
        vmacro = col.vx / 1e5 # km/s
    
    hanlert.io.write_atmos(filepath, height[sel], col.T[sel], density[sel], vmacro[sel], vmicro[sel],
                density_type=density_type, tau_scale=tau_scale, **kwargs)
    
    # Magnetic field
    #
    # Convert from cartesian to inclination/azimuth representation
    B = np.sqrt(col.Bx**2 + col.By**2 + col.Bz**2) * np.sqrt(4 * np.pi) # TODO XXX remove when fixed in muram.py
    Binc = np.degrees(np.arccos(col.Bx/B)) # deg; range [0, 180]
    Bazi = np.degrees(np.arctan2(col.By, col.Bz)) # deg; range [-180, +180]
    Bazi[ Bazi < 0 ] += 360. # deg; range [0, 360]
    hanlert.io.write_Bfield(filepath, B[sel], Binc[sel], Bazi[sel])

def make_colpath(iteration, y, z):
    colpath = f"iter_{iteration:05d}/Y_{y:04d}/Z_{z:04d}"
    return colpath

def make_col_id(iteration, y, z):
    colpath = make_colpath(iteration, y, z)
    col_id = colpath.replace("/", "_")
    return col_id
    
def make_jobpath(jobroot, jobname, iteration, y, z):
    colpath = make_colpath(iteration, y, z)
    jobpath = os.path.join(jobroot, 'jobs', jobname, colpath)
    return jobpath

def parse_time(timeline):
    match = re.search("Time: (?:\s*(\d+) hours, )?\s*(\d+) minutes[,]? and \s*(\d+) seconds", timeline)
    if match is None:
        return None
    hms = match.groups() # (hours, minutes, seconds); potentially with None
    def toint(s):
        if s is None:
            return 0
        else:
            return int(s)
    hms = [toint(s) for s in hms] # now ints
    seconds = 0
    seconds += hms[0] * 3600 # hours to seconds
    seconds += hms[1] * 60 # minutes to seconds
    seconds += hms[2]
    return seconds
    
def job_status(jobroot, jobname, iteration, y, z, outfile='stdout', stokesfile='Stokesout'):
    jobpath = make_jobpath(jobroot, jobname, iteration, y, z)
    status = None
    if os.path.exists(jobpath):
        status = "PREPARED", None
    
    outfile = os.path.join(jobpath, outfile)
    if os.path.exists(outfile):
        stat = os.stat(outfile)
        tstart = os.path.getctime(outfile)
        telapse = time.time() - tstart
        status = 'STARTED', telapse
        lastlines = [x for x in utils.tail(outfile, 3)]
        if lastlines[0] == ' - Solver finished':
            timeline = lastlines[2]
            trun = parse_time(timeline)
            # check that the stokes output was written
            stokesfile = os.path.join(jobpath, stokesfile)
            if os.path.exists(stokesfile):
                status = 'OK', trun
            else:
                status = 'FAIL', trun
        elif "Controlled abortion" in lastlines[-1]:
            tmod = os.path.getmtime(outfile)
            trun = tmod - tstart
            status = 'FAIL', trun
    return status

def run_status(jobroot, jobname):
    status = OrderedDict()
    jobpath = os.path.join(jobroot, 'jobs', jobname)
    for iterdir in sorted(os.listdir(jobpath)):
        label, iteration = iterdir.split('_')
        iteration = int(iteration)
        status[iteration] = OrderedDict()
        iterpath = os.path.join(jobpath, iterdir)
        for ydir in sorted(os.listdir(iterpath)):
            label, y = ydir.split("_")
            y = int(y)
            ypath = os.path.join(iterpath, ydir)
            for zdir in sorted(os.listdir(ypath)):
                label, z = zdir.split("_")
                z = int(z)
                point = (y, z)
                status[iteration][point] = job_status(jobroot, jobname, iteration, y, z)
    return status

def prepare_job(datapath, jobroot, jobname, iteration, y, z,
                project, email,
                intemp="INPUT.template", subtemp="qsub.template", overwrite=False, **kwargs):
    snap = muram.MuramSnap(datapath, iteration)
    col = snap.column(y, z)
    
    jobpath = make_jobpath(jobroot, jobname, iteration, y, z)
    if os.path.exists(jobpath):
        if overwrite:
            shutil.rmtree(jobpath)
        else:
            raise Exception("job directory " + jobpath + " already exists")
    os.makedirs(jobpath)
    write_col(col, os.path.join(jobpath, 'muram'), **kwargs)
    
    # Prepare INPUT file
    jobpath_rel = os.path.relpath(jobpath, jobroot)
    intemp = os.path.join(jobroot, intemp)
    intemp = open(intemp, 'r').read()
    intemp = intemp.format(jobpath=jobpath_rel)
    inout = os.path.join(jobpath, "INPUT")
    open(inout, 'w').write(intemp)
    
    # Prepare qsub file
    col_id = make_col_id(iteration, y, z)
    subjobname = "muram2hanlert_" + jobname + '_' + col_id
    subtemp = os.path.join(jobroot, subtemp)
    subtemp = open(subtemp, 'r').read()
    subtemp = subtemp.format(jobpath=jobpath_rel, jobname=subjobname, project=project, email=email)
    subout = os.path.join(jobpath, "hanlert.qsub")
    open(subout, 'w').write(subtemp)

    return jobpath

def start_job(jobroot, jobname, iteration, y, z):
    jobpath = make_jobpath(jobroot, jobname, iteration, y, z)
    qsub = os.path.join(jobpath, 'hanlert.qsub')
    command = "qsub " + qsub
    print(command)
    return_code = os.system(command)
    return return_code
