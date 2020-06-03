import numpy as np
from matplotlib import pyplot as plt
import matplotlib as mpl
import os
import hanlert
from . import jobs

def plot_atmos(col, min_height=-100., close=False, save=False):
    iteration = col.iteration
    tau1_ix = (np.abs(col.tau - 1.0)).argmin()
    height = (col.X - col.X[tau1_ix]) / 1e5 # km
    sel = height >= min_height
        
    fig, ((ax1, ax4, ax7), (ax2, ax5, ax8), (ax3, ax6, ax9)) = plt.subplots(3, 3, figsize=(11, 8.5))
    
    ax1.plot(height[sel], col.T[sel], 'k.-')
    ax1.set_ylabel('Temperature [K]')
    ax2.plot(height[sel], col.rho[sel], 'k.-')
    ax2.set_ylabel('Density [g/cm^3]')
    ax3.plot(height[sel], col.P[sel], 'k.-')
    ax3.set_ylabel('Pressure [dyn/cm^2]')

    ax4.plot(height[sel], col.vx[sel], 'k.-')
    ax4.set_ylabel('vx [cm/s]')
    ax5.plot(height[sel], col.vy[sel], 'k.-')
    ax5.set_ylabel('vy [cm/s]')
    ax6.plot(height[sel], col.vz[sel], 'k.-')
    ax6.set_ylabel('vz [cm/s]')

    sqrt4pi = np.sqrt(4 * np.pi)
    ax7.plot(height[sel], col.Bx[sel] * sqrt4pi, 'k.-')
    ax7.set_ylabel('Bx [G]')
    ax8.plot(height[sel], col.By[sel] * sqrt4pi, 'k.-')
    ax8.set_ylabel('By [G]')
    ax9.plot(height[sel], col.Bz[sel] * sqrt4pi, 'k.-')
    ax9.set_ylabel('Bz [G]')
    fig.suptitle(f"iteration={iteration} col=({col.y}, {col.z})")
    fig.tight_layout(rect=[0, 0.03, 1, 0.98])
    if save:
        fig.savefig(f'mean_atmos_{col.iteration:5d}.png')
    if close:
        plt.close(fig)
        
def plot_col(snap, y, z):
    col = snap.column(y, z)
    plot_atmos(col)

def plot_random_col(snap):
    y = np.random.randint(0, snap.T.shape[1])
    z = np.random.randint(0, snap.T.shape[2])
    plot_col(snap, y, z)

def plot_CaII(jobroot, jobname, iteration, y, z, save=False, close=False):
    
    # mpl.rcParams.update({'font.size':12})
    jobpath = jobs.make_jobpath(jobroot, jobname, iteration, y, z)
    col_id = jobs.make_col_id(iteration, y, z)
    title = f"{jobname} iteration={iteration} col=({y}, {z}) Ca II {label}"
    if save:
        plotfile = f"{col_id}_CaII_{label}.pdf"
        save = plotfile
    hanlert.plot_CaII(jobpath, title=title, save=save, close=close, **kwargs)
