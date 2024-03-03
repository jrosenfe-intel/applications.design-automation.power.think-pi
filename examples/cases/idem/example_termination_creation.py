# ------------- Introduction -------------
'''
Create a termination file for a PowerSI .snp file.
This termination file is used to create an basic Hspice deck for impedance profile
analysis.
'''
# ------------- User defined parameters -------------
import sys
#Path to Think PI version
sys.path.append(r'./think-pi-dev_pr_127/applications.design-automation.power.think-pi-dev') 

#Input s-parameters file path
sparam_fpath='OKS1_NFF1S_DNOX_PWRsims_ww03_processed_all_ports_clip_012623_173538_30544_DCfitted.s29p'
#Output termination file path
termination_fpath='termination.csv'


# ------------- Don't modify anything below this line -------------
from thinkpi.tools.hspice_deck import PSITerminationFile

#Create the Termination file
term_file=PSITerminationFile()
term_file.create_termination(sparam_fpath,termination_fpath)