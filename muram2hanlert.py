import os
import os.path
import muram
import hanlert
import utils

def write_col(col, filepath, vmicro=None, density_type='rho', tau_scale=False, 
              min_height=-100.0, tau1_ix=None, max_tau=20., sample=1, **kwargs):
    
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
    
    # XXX setting vmacro = zeros for now
    # XXX vmicro probably set to zero
    zeros = np.zeros_like(col.x)
    if vmicro is None:
        vmicro = zeros
    
    hanlert.write_atmos(filepath, height[sel], col.T[sel], density[sel], zeros[sel], vmicro[sel],
                density_type=density_type, tau_scale=tau_scale, **kwargs)
    
    # Magnetic field
    #
    # Convert from cartesian to inclination/azimuth representation
    B = np.sqrt(col.Bx**2 + col.By**2 + col.Bz**2) * np.sqrt(4 * np.pi) # TODO XXX remove when fixed in muram.py
    Binc = np.degrees(np.arccos(col.Bx/B)) # deg; range [0, 180]
    Bazi = np.degrees(np.arctan2(col.By, col.Bz)) # deg; range [-180, +180]
    Bazi[ Bazi < 0 ] += 360. # deg; range [0, 360]
    hanlert.write_Bfield(filepath, B[sel], Binc[sel], Bazi[sel])

def make_colpath(iteration, y, z):
    colpath = f"iter_{iteration:05d}/YZ_{y:04d}_{z:04d}"
    return colpath
    
def make_jobpath(jobroot, iteration, y, z):
    colpath = make_colpath(iteration, y, z)
    jobpath = os.path.join(jobroot, colpath)
    return jobpath

def job_status(jobroot, iteration, y, z, outfile='stdout'):
    jobpath = make_jobpath(jobroot, iteration, y, z)
    status = None
    if os.path.exists(jobpath):
        status = "prepared"
    
    outfile = os.path.join(jobpath, outfile)
    if os.path.exists(outfile):
        status = 'started'
        lastlines = [x for x in utils.tail(outfile, 3)]
        if lastlines[0] == ' - Solver finished':
            status = 'done'
    return status

def prepare_job(datapath, jobroot, iteration, y, z,
                project, email,
                intemp="INPUT.template", subtemp="qsub.template", overwrite=False, **kwargs):
    snap = muram.MuramSnap(datapath, iteration)
    col = snap.column(y, z)
    
    colpath = make_colpath(iteration, y, z)
    jobpath = make_jobpath(jobroot, iteration, y, z)
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
    jobname = "hanlert_muramcol_" + colpath.replace("/", "_")
    subtemp = os.path.join(jobroot, subtemp)
    subtemp = open(subtemp, 'r').read()
    subtemp = subtemp.format(jobpath=jobpath_rel, jobname=jobname, project=project, email=email)
    subout = os.path.join(jobpath, "hanlert.qsub")
    open(subout, 'w').write(subtemp)

    return jobpath

def start_job(jobroot, iteration, y, z):
    jobpath = make_jobpath(jobroot, iteration, y, z)
    qsub = os.path.join(jobpath, 'hanlert.qsub')
    command = "qsub " + qsub
    print(command)
    return_code = os.system(command)
    return return_code
