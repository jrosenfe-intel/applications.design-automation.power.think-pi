# ------------- Introduction -------------
'''
This is the third phase of the DC analysis setup.
The user is expected to modify the sink and vrm .csv file
that will be used in this phase.

This task will perform the following:
- import sink and vrm parameters after user modifications
- enable bypassing PowerDC confirmation
- enable adding nodes to pads
- delete extra smb layer of the package after the board and package merge
- set simulation temperature

After completion of this phase inspect the modified database and run simulation.
After completion of the simulation, move to the next phase where results are aggregated.
'''

# ------------- User defined parameters -------------
r'''
MERGED_DATABASE_NAME = r'C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\db\brd_pkg_OKS.spd'

SINK_SETUP_FILE = r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\db\OKS_sinksetup.xlsx"
VRM_SETUP_FILE = r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\db\OKS_vrmsetup.xlsx"

SIM_TEMPERATURE = 100

TCL_FILE_NAME = 'OKS_pdc_setup.tcl'
'''

# Inputs
# ------
MERGED_DATABASE_NAME = r'..\thinkpi_test_db\spr\brd_interposer_pkg_SPR.spd'
SINK_SETUP_FILE = r"..\thinkpi_test_db\spr\SPR_sinksetup.csv"
VRM_SETUP_FILE = r"..\thinkpi_test_db\spr\SPR_vrmsetup.csv"
SIM_TEMPERATURE = 90

# Outputs
# -------
TCL_FILE_NAME = 'SPR_pdc_interposer_setup.tcl'

# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks
from thinkpi.config import thinkpi_conf as cfg
from thinkpi.operations import speed as spd

if __name__ == '__main__':
    db = spd.Database(MERGED_DATABASE_NAME)
    db.load_flags['plots'] = False
    db.load_data()

    brd_pkg = tasks.PdcTask(db)
    brd_pkg.import_sink_setup(SINK_SETUP_FILE)
    brd_pkg.import_vrm_setup(VRM_SETUP_FILE)
    brd_pkg.db.save()
    
    brd_pkg.pdc_setup(SIM_TEMPERATURE)
    brd_pkg.create_tcl(('PowerDC', 'IRDropAnalysis'),
                       TCL_FILE_NAME)
    brd_pkg.run_tcl(TCL_FILE_NAME, brd_pkg.exec_paths['sigrity'][0])
