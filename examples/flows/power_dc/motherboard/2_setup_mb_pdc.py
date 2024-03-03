# ------------- Introduction -------------
'''
This is the second phase of the DC analysis setup.

This task will perform the following:
- Find and remove shorts between ground and power pins after the merge
- place VRMs on a specified layer
- place sinks on a specified layer
- export sink and vrm .csv paramteres files
  which the user can modify and use in the next phase

After completion of this phase, inspect the new database and move to the next phase.
The user is expected to modify the newly created sink and vrm .csv file
that will be used in the following phase.
'''

# ------------- User defined parameters -------------

# Inputs
# ------
MERGED_DATABASE_NAME = r'C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\db\brd_pkg_OKS.spd'

VRM_LAYER = 'SignalBRD$TOP' # Refers to the merged database
VRM_PWR_NET = 'PVCCIN_CPU0_NORTH'
SINK_LAYER = 'SignalPKG$surface' # Refers to the merged database
SINK_PWR_NET = 'VCCIN_NORTH'
NUM_SINKS = 13
AREA = None # or (xbot, ybot, xtop, ytop); Refers to the merged database

# Outputs
# -------
SINK_SETUP_FILE = r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\db\OKS_sinksetup.csv"
VRM_SETUP_FILE = r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\db\OKS_vrmsetup.csv"

# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks

if __name__ == '__main__':
    brd_pkg = tasks.PdcTask(MERGED_DATABASE_NAME)
    brd_pkg.db.find_pwr_gnd_shorts()
    brd_pkg.place_vrms(VRM_LAYER, VRM_PWR_NET)
    brd_pkg.place_sinks(SINK_LAYER, SINK_PWR_NET, NUM_SINKS, AREA)
    brd_pkg.db.save()

    brd_pkg.export_sink_setup(SINK_SETUP_FILE)
    brd_pkg.export_vrm_setup(VRM_SETUP_FILE)
