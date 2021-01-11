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
              min_height=-100.0, tau1_ix=None, max_tau=20., N_ixs=None, N_ixs_ref='top', sample=1, **kwargs):
    """Write MURaM column as HanleRT input files

    Two files are written to the given filepath: muram.atmos and muram.field, containing 
    the atmosphere and magnetic field parameters, respectively.

    Inputs:
     - col (MuramColumn)  : column to write
     - filepath (str)     : destination directory
     - vmicro (ndarray)   : optional microturbulent velocity array
     - zerovel (bool)     : if True, velocities from col are ignored
     - density_type (str) : the type of data specifying density/pressure
     - tau_scale (bool)   : if True, a tau depth scale is used instead of height
     - min_height (float) : the lowest height taken from col
     - tau1_ix (int)      : the index which should be considered tau=1 or height=0
     - max_tau (int)      : the maximum optical depth taken from col (when tau_scale is True)
     - N_ixs (int)        : the number of indexes to take from the column.  The default (None) is to take all 
                            indexes above min_height or max_tau.
     - N_ixs_ref (str)    : Reference point for taking N_ixs.  Either 'top' (default), to take from the top of
                            the domain, 'min' to take from above the specified min_height or max_tau, or 'tau1' 
                            to take from above the tau1_ix (tau=1/height=0 point).  'top' and 'tau1'
                            causes min_height/max_tau to be ignored.
     - sample (int)       : the sampling interval for col.  Default is 1 (every element)
     - **kwargs           : remaining keyword args are passed to hanlert.io.write_atmos

    Returns:
     - None
    """
    
    # Atmosphere
    #
    # Select only heights above the defined minimum
    if tau1_ix is None:
        tau1_ix = (np.abs(col.tau - 1.0)).argmin()
    if not tau_scale:
        height = (col.X - col.X[tau1_ix]) / 1e5 # km
        sel = height >= min_height
    else:
        height = col.tau
        sel = height <= max_tau
    min_height_ix = np.where(sel)[0][0] # smallest height / biggest tau

    # Optionally select a fixed number of grid points
    if N_ixs is not None:
        sel = np.zeros(height.size, dtype='bool')
        if N_ixs_ref == 'top':
            # Overrides min_height/max_tau settings
            if N_ixs > height.size:
                raise Exception(f"Requested to take N_ixs={N_ixs} from below the last index, " + 
                                f"but only {height.size} indexes exist")
            sel[-N_ixs:] = True
        elif N_ixs_ref == 'min':
            top_ix = min_height_ix + N_ixs
            if top_ix > (height.size - 1):
                N_above = (height.size - 1) - min_height_ix
                raise Exception(f"Requested to take N_ixs={N_ixs} from above the specified minimum, " + 
                                f"but only {N_above} indexes exist above that point")
            sel[min_height_ix:top_ix] = True
        elif N_ixs_ref == 'tau1':
            top_ix = tau1_ix + N_ixs
            if top_ix > (height.size - 1):
                N_above = (height.size - 1) - tau1_ix
                raise Exception(f"Requested to take N_ixs={N_ixs} from above tau=1, " + 
                                f"but only {N_above} indexes exist above that point")
            sel[tau1_ix:top_ix] = True
        else:
            raise Exception("N_ixs_ref must be either 'top' or 'tau1'")
        
    # Optionally select only every nth sample
    # Careful to keep the deepest sample from selection above
    sel2 = np.zeros_like(height, dtype='bool') # All False
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
    B = np.sqrt(col.Bx**2 + col.By**2 + col.Bz**2)
    Binc = np.degrees(np.arccos(col.Bx/B)) # deg; range [0, 180]
    Bazi = np.degrees(np.arctan2(col.By, col.Bz)) # deg; range [-180, +180]
    Bazi[ Bazi < 0 ] += 360. # deg; range [0, 360]
    B = B * np.sqrt(4 * np.pi) # convert to Gauss.  TODO XXX remove when fixed in muram.py
    hanlert.io.write_Bfield(filepath, B[sel], Binc[sel], Bazi[sel])

def shortest_column(datapath, iteration, min_height=0):
    """Returns the lowest number of indexes above (and including) the min_height sample"""
    snap = muram.MuramSnap(datapath, iteration)
    tau1_ix = (np.abs(snap.tau - 1.0)).argmin(axis=0)
    max_ix = np.max(tau1_ix) + int(np.ceil(min_height * 1e5 / snap.dX[0]))
    N_shortest = snap.shape[0] - max_ix
    return N_shortest

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
        lastlines = [x for x in utils.tail(outfile, 4)] # TODO BUG: PBS, mpirun might add lines
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

def start_jobpath(jobpath):
    qsub = os.path.join(jobpath, 'hanlert.qsub')
    command = "qsub " + qsub
    print(command)
    return_code = os.system(command)
    return return_code

def start_job(jobroot, jobname, iteration, y, z):
    jobpath = make_jobpath(jobroot, jobname, iteration, y, z)
    return start_jobpath(jobpath)

def prepare_uniformB_jobs(jobroot, jobname, B, project, email,
                intemp="INPUT.template", subtemp="qsub.template", overwrite=False, **kwargs):
    """Prepare a sereis of jobs imposing a uniform magnetic field"""

    
    if B.shape[1] != 3:
        raise Exception("Bfile should be numpy array of [Bmag, Binc, Bazi], shape (n, 3)")
    N = B.shape[0]

    # Ensure clean directory tree at the jobname level
    jobnamepath = os.path.join(jobroot, 'jobs', jobname)
    if os.path.exists(jobnamepath):
        if overwrite:
            shutil.rmtree(jobnamepath)
        else:
            raise Exception("job directory " + jobnamepath + " already exists")
    os.makedirs(jobnamepath)

    # Save magnetic field data to jobnamepath
    Bfile = os.path.join(jobnamepath, 'uniformB.npy')
    np.save(Bfile, B)

    jobpath_list = []
    for ix in range(N):
        Bname = f"B_{ix:04d}"
        Bmag = B[ix, 0]
        Binc = B[ix, 1]
        Bazi = B[ix, 2]

        jobpath = os.path.join(jobnamepath, Bname)
        os.makedirs(jobpath)

        # Write field file
        hanlert.io.write_Bfield(os.path.join(jobpath, 'B'), Bmag, Binc, Bazi)
        
        # Prepare INPUT file
        jobpath_rel = os.path.relpath(jobpath, jobroot)
        intemppath = os.path.join(jobroot, intemp)
        intempstr = open(intemppath, 'r').read()
        intempstr = intempstr.format(jobpath=jobpath_rel)
        inout = os.path.join(jobpath, "INPUT")
        open(inout, 'w').write(intempstr)
    
        # Prepare qsub file
        subjobname = jobname + '_' + Bname
        subtemppath = os.path.join(jobroot, subtemp)
        subtempstr = open(subtemp, 'r').read()
        subtempstr = subtempstr.format(jobpath=jobpath_rel, jobname=subjobname, project=project, email=email)
        subout = os.path.join(jobpath, "hanlert.qsub")
        open(subout, 'w').write(subtempstr)
        jobpath_list.append(jobpath)
    return jobpath_list
