# ------------- Introduction -------------
'''
This phase automatically setting the simulation parameters based on user input.
The flow assumes the packages is already processed and cut.

This phase implements the following tasks:
- define special voids
- delete certain layers below the ground layer of the inductor
- Defines all parameters related to the simulation such as
  temperature, frequency related parameters, and computer resources
'''

# ------------- User defined parameters -------------

r"""
# Inputs
# ------
DATABASE_PATH_NAME = r'..\thinkpi_test_db\spr\clarity\spr-mcc_k42410-001_cfc-cfn-io_2020_10_30_22_48_cfc_ios_cfns.spd'

PWR_NET_NAMES = ['VXBR_VCCCFNHCB*','VCCCFNHCB'] # You can also use wildcards
GND_NET_NAMES = 'VSS' # You can also use wildcards

STACKUP_FILE_NAME = r"..\thinkpi_test_db\spr\clarity\spr-mcc_k42410-001_cfc-cfn-io_2020_10_30_22_48_cfc_ios_cfns_stackup.csv"
PADSTACK_FILE_NAME = r"..\thinkpi_test_db\spr\clarity\spr-mcc_k42410-001_cfc-cfn-io_2020_10_30_22_48_cfc_ios_cfns_padstack.csv"
# If material file is not provided user must provide default conductivity
# Material file should be provided by teh FAST ATTD tool based on your technology or your PI lead
MATERIAL_FILE_NAME = None
# If default conductivity is not provided user must provide material file
DEFAULT_CONDUCTIVITY = 4.31e7
CUT_MARGIN = 1e-3 # Use 0 to avoid cutting
PROCESSED_DATABASE_PATH_NAME = r"spr-mcc_k42410-001_cfc-cfn-io_2020_10_30_22_48_cfc_ios_cfns_thinkPI_process.spd"
DELETE_BELOW_LAYER = 'Signal$2b'

SIMULATION_TEMPERATURE = 100
SOL_FREQ = 1e9
FMIN = 0
FMAX = 1e9
MAGNETIC = True # Indicates if the inductor is magnetic or ACI
SW_FREQ = 90e6 # Switching FIVR frequency

# First order is recommended by the BKM as it provides better accuracy
# with minimal simulation time penalty
ORDER = 1 
VOID_SIZE = 5e-6 # If EMIB is included in the package use 1e-6 m otherwise use 5e-6 m

# Do not set the number to more than the number of cores a server has
# Do not use all the resources of a shared server for one simulation
# For large designs (ex. >10x10mm, >100 ports),
# it is recommended to use 32 cores or more (if the server permits)
NUM_CORES = 2

# Outputs
# -------
TCL_FILE_NAME = r"clarity_preprocess_test.tcl"
"""

# Inputs
# ------
DATABASE_PATH_NAME = r'..\thinkpi_test_db\spr\clarity\spr-mcc_k42410-001_cfc-cfn-io_2020_10_30_22_48_cfc_ios_cfns.spd'

DELETE_BELOW_LAYER = 'Signal$2b'

SIMULATION_TEMPERATURE = 110
SOL_FREQ = 1e9
FMIN = 0
FMAX = 1e9
MAGNETIC = True # Indicates if the inductor is magnetic or ACI
SW_FREQ = 90e6 # Switching FIVR frequency

# Zero order is recommended by the BKM as it provides better accuracy
# with minimal simulation time penalty
ORDER = 0
VOID_SIZE = 5e-6 # If EMIB is included in the package use 1e-6 m otherwise use 5e-6 m

# Outputs
# -------
TCL_FILE_NAME = r"clarity_preprocess_test.tcl"

# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks

if __name__ == '__main__':
    pkg = tasks.ClarityTask(DATABASE_PATH_NAME)

    pkg.setup_clarity_sim1(delete_below_layer=DELETE_BELOW_LAYER,
                           sim_temp=SIMULATION_TEMPERATURE,
                            sol_freq=SOL_FREQ, fmin=FMIN, fmax=FMAX,
                            magnetic=MAGNETIC, sw_freq=SW_FREQ,
                            order=ORDER, void_size=VOID_SIZE)
    pkg.create_tcl(('Clarity 3D Layout', '3DFEMExtraction'),
                   TCL_FILE_NAME)
    pkg.run_tcl(TCL_FILE_NAME, pkg.exec_paths['sigrity'][0])


    