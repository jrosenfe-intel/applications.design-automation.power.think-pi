# ------------- Introduction -------------
'''
This is the first phase of the socket electro-thermal analysis setup.
This flow assumes board and package layouts are preprocessed.

This task will perform the following:
- connect package and board layouts given resistance per pin

After completion of this phase, inspect the new database and move to the next phase.
'''

# ------------- User defined parameters -------------

# Inputs
# ------
TOP_DB_PATH_NAME = r"..\thinkpi_test_db\OKS\skt_electro_thermal\dmr_ap_ucc1_pwr_vccin_uciea_ring_23ww42_odb_proc.spd"
BOTTOM_DB_PATH_NAME = r"..\thinkpi_test_db\OKS\skt_electro_thermal\JC2_DNO_100923_0v56B_master_proc_no_p2s.spd"
PIN_RESISTANCE = 30e-3 # Ohm

# Outputs
# -------
TCL_FILE_NAME = 'OKS_brd_pkg_merged.tcl'
MERGED_DATABASE_NAME = r'..\thinkpi_test_db\OKS\skt_electro_thermal\dmr_ap_ucc1_JC2_DNO_100923_0v56B.spd'

# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks
from thinkpi.config import thinkpi_conf as cfg

if __name__ == '__main__':
    brd = tasks.PdcTask(BOTTOM_DB_PATH_NAME)
    pkg = tasks.PdcTask(TOP_DB_PATH_NAME)

    brd.merge(pkg, PIN_RESISTANCE, MERGED_DATABASE_NAME)
    brd.create_tcl(('Celsius Layout', 'E/TCoSimulation'),
                   TCL_FILE_NAME)
    brd.run_tcl(TCL_FILE_NAME, brd.exec_paths['sigrity'][0])
    
    
    