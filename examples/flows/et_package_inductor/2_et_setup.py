# ------------- Introduction -------------
'''
The user must update the VRM and sink information in the templates created in the previous phase.
Once this is done, this phase will update it in the specified database.

In summary, the user must inspect and modify the following files before running this phase:
- SINK_SETUP_FILE
- VRM_SETUP_FILE
'''

# ------------- User defined parameters -------------

# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\thermal\gnr_x1_master_m63954-001_03_22_2022_et.spd"
SINK_SETUP_FILE = r"..\thinkpi_test_db\thermal\et_sink.csv"
VRM_SETUP_FILE = r"..\thinkpi_test_db\thermal\et_vrm.csv"

# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks

if __name__ == '__main__':
    pkg_ind = tasks.PackageInductorElectroThermalTask(DATABASE_PATH_NAME)
    pkg_ind.import_sink_setup(SINK_SETUP_FILE)
    pkg_ind.import_vrm_setup(VRM_SETUP_FILE)
    pkg_ind.db.save()
    
    
    