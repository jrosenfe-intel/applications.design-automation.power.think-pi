# ------------- Introduction -------------
'''
This phase creates a termination file template for a touchstone .snp file.
This termination file is used to automatically create an
impedance profile Hspice deck in the next optimization phase.
The user can update this termination file to represenet a more accurate termination scenario.
'''

# ------------- User defined parameters -------------

# Inputs
# ------
SPARAM_PATH_NAME = r"E:\Users\jrosenfe\ThinkPI\data\idem_optimizer\sparams\OKS1_NFF1S_DNOX_PWRsims_ww03_processed_all_ports_clip_012623_173538_30544_DCfitted.s29p"
# SPARAM_PATH_NAME = r'E:\Users\jrosenfe\ThinkPI\data\idem_optimizer\sparams\BPS_FAB2_020619_A_proce_A_050819_171415_5252_DCfitted.s46p'

# Outputs
# -------
TERMINATION_FILE_NAME = r"E:\Users\jrosenfe\ThinkPI\data\idem_optimizer\termination.csv"

# ------------- Don't modify anything below this line -------------
from thinkpi.tools.hspice_deck import PSITerminationFile

term_file = PSITerminationFile()
term_file.create_termination(SPARAM_PATH_NAME,
                            TERMINATION_FILE_NAME)