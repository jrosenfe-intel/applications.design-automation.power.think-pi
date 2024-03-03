# ------------- Introduction -------------
'''
PowerSi (2.5D) setup extraction
'''

# ------------- User defined parameters -------------

# Inputs
# ------
DATABASE_PATH_NAME = r"D:\jrosenfe\ThinkPI\thinkpi_test_db\CWF\CWF_SP_A12345_MIN_2023_05_30.spd"

SIMULATION_TEMPERATURE = 110
START_FREQUENCY = 0
END_FREQUENCY = 1e9


# Outputs
# -------
TCL_FILE_NAME = 'psi_setup.tcl'

# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks
from thinkpi.operations import speed as spd

if __name__ == '__main__':
    db = spd.Database(DATABASE_PATH_NAME)
    db.load_flags['plots'] = False
    db.load_data()

    db.setup_psi_sim(SIMULATION_TEMPERATURE, START_FREQUENCY, END_FREQUENCY)
    db.create_tcl(('PowerSI', 'extraction'), TCL_FILE_NAME)
    db.run_tcl(TCL_FILE_NAME, db.exec_paths['sigrity'][0])
    #db.save_layout_views()
    #db.crop_layout_views()