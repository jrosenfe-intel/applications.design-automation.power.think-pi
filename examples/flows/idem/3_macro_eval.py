# ------------- Introduction -------------
'''
This phase can be run while the previous phase is performing the optimization.
In this phase the five best matches are graphically plotted and compared to the
original S-parameters in the form of a terminated PDN impednace profile.
'''

# ------------- User defined parameters -------------

# Inputs
# ------
SPARAM_PATH_NAME = r"D:\jrosenfe\ThinkPI\idem\OKS1_DNO5_bga9324_ww22_ANAcaps_cut_ports_2nd_071523_181825_32744_DCfitted.s47p"

MAX_DATA_FREQ =10e3 # Hz

# ------------- Don't modify anything below this line -------------

from thinkpi.flows import tasks

if __name__ == '__main__':
    results = tasks.IdemEvalResults(SPARAM_PATH_NAME, MAX_DATA_FREQ)
    results.refresh()
    
    
    