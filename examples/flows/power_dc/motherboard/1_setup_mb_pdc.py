# ------------- Introduction -------------
'''
This is the first phase of the DC analysis setup.

This task will perform the following:
- connect two databases with a given resistance per pin

After completion of this phase, inspect the new database and move to the next phase.
In the second phase, shorts between ground and power pins of the connector are found and removed,
as well as sinks and VRMs are placed.
'''

# ------------- User defined parameters -------------

# Inputs
# ------
TOP_DB_PATH_NAME = r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\db\dmr-ap_ppf_12ch_vccin_pdslice_ccb-io_north_0050422.spd"
BOTTOM_DB_PATH_NAME = r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\db\OKS_12CH_PI_V1_ww19.spd"
PIN_RESISTANCE = 0.1e-3 # Ohm
PIN_INDUCTANCE = None # Henry

# Outputs
# -------
MERGED_DATABASE_NAME = r'C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\db\brd_pkg_OKS.spd'
TCL_FILE_NAME = 'OKS_brd_pkg_merged.tcl'

# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks

if __name__ == '__main__':
    brd = tasks.PdcTask(BOTTOM_DB_PATH_NAME)
    pkg = tasks.PdcTask(TOP_DB_PATH_NAME)

    brd.merge(pkg, PIN_RESISTANCE, MERGED_DATABASE_NAME)
    brd.create_tcl(('PowerDC', 'IRDropAnalysis'),
                   TCL_FILE_NAME)
    
    brd.run_tcl(TCL_FILE_NAME, brd.exec_paths['sigrity'][0])

    if PIN_INDUCTANCE is not None:
        layout = tasks.PdcTask(MERGED_DATABASE_NAME)
        layout.connector_res_ind(pin_res=None,
                             pin_ind=PIN_INDUCTANCE)
        layout.db.save()
