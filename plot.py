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
    stokes = hanlert.read_stokes(os.path.join(jobpath, "Stokes_1_1"))

    # Line centers that were computed from minimum of I
    # TODO: recompute dynamically to handle Doppler shifts
    K = 393.477713
    H = 396.959134
    IRT1 = 850.035829
    IRT2 = 854.443791
    IRT3 = 866.452017
    dL = 0.1

    selHK = (stokes['L'] >= K - dL) & (stokes['L'] <= H + dL)
    selKcore = (stokes['L'] >= (K - dL)) & (stokes['L'] <= (K + dL))
    selHcore = (stokes['L'] >= (H - dL)) & (stokes['L'] <= (H + dL))
    selIRT = (stokes['L'] >= IRT1 - dL) & (stokes['L'] <= IRT3 + dL)
    selIRT1 = (stokes['L'] >= IRT1 - dL) & (stokes['L'] <= IRT1 + dL)
    selIRT2 = (stokes['L'] >= IRT2 - dL) & (stokes['L'] <= IRT2 + dL)
    selIRT3 = (stokes['L'] >= IRT3 - dL) & (stokes['L'] <= IRT3 + dL)

    cmap = mpl.cm.get_cmap('copper')
    for label, sel, center in (('K', selKcore, K), ('H', selHcore, H),
                           ('IRT1', selIRT1, IRT1), ('IRT2', selIRT2, IRT2), ('IRT3', selIRT3, IRT3)):
        ticks = np.linspace(center - dL, center + dL, 5)
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(11, 8.5))
        for i_mu in (1, 2, 3, 4, 5): # TODO: get number of LOS from filesystem
            stokesfile = f"Stokes_{i_mu}_1"
            stokes1 = hanlert.read_stokes(os.path.join(jobpath, stokesfile))
            mu = stokes1['mu']
            mu_str = f"{mu:0.1f}"
            c = cmap(mu)

            ax1.plot(stokes1['L'][sel], stokes1['I'][sel], c=c)
            ax2.plot(stokes1['L'][sel], stokes1['V/I'][sel], c=c, label=f"$\mu =$ {mu_str}")
            ax3.plot(stokes1['L'][sel], stokes1['Q/I'][sel], c=c)
            ax4.plot(stokes1['L'][sel], stokes1['U/I'][sel], c=c)

        ax1.set_ylabel("I")
        ax2.set_ylabel("V/I")
        ax2.legend(loc='upper right')
        ax3.set_ylabel("Q/I")
        ax4.set_ylabel("U/I")
        for ax in (ax1, ax2, ax3, ax4):
            ax.set_xticks(ticks)
            ax.xaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%.2f'))
        fig.tight_layout(rect=[0, 0.03, 1, 0.97])
        fig.suptitle(f"{jobname} iteration={iteration} col=({y}, {z}) Ca II {label}", size=16)
        if save:
            plotfile = f"{col_id}_CaII_{label}.pdf"
            fig.savefig(plotfile, bbox_inches='tight')
        if close:
            plt.close(fig)