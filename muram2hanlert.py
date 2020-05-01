import os
import os.path
import muram

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
        lastlines = [x for x in tail(outfile, 3)]
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
