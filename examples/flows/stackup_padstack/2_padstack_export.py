# ------------- Introduction -------------
'''
Exports current database padstack in the form of .csv files.
Based on provided parameters, fields will be populated with the corresponding values.
The task will export the prefilled stackup and padstack of the database.
The user can modify the parameters in these files and use them in other flows.

If a parameter is set to None the existing value in the loaded .spd file is used.
Alternatively, if a parameter is set to '', the new padstack value will be set to blank.
'''

r'''
# ------------- User defined parameters -------------

# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\OKS\debug\Daniel\baseline_OKS1_NFF1S_DNOX_PWRsims_ww03_processed_all_ports_clip_fix.spd"

UNIT = 'mil' # Only use one of the following units: nm, um, mm, cm, m, mil, inch

# Padstack parameters - Only use the ones you need
DB_TYPE = 'brd' #'board' # or 'brd' or 'package' or 'pkg' only
PLATING = 1 # 2.54e-5 m (1 mil) for a board and 18e-6 m for a package
CONDUCT_PADSTACK = 3.4e7 # 3.4e7 S/m for a board and 4.31e7 S/m for a package
MATERIAL = ''
INNERFILL_MATERIAL = None # Typically used for FIVR indcutor power and ground PTHs
OUTER_THICKNESS = None # Typically used for FIVR magnetic inductor power PTHs
OUTER_COATING_MATERIAL = None # Typically used for FIVR magnetic inductor power PTHs

# Outputs
# -------
PADSTACK_FILE_NAME = r"..\thinkpi_test_db\OKS\debug\Daniel\baseline_brd_22L_padstack.csv"
'''

# ------------- User defined parameters -------------

r'''
# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\GNR\oblong_debug\M6186203_cut.spd"

UNIT = 'mil' # Only use one of the following units: nm, um, mm, cm, m, mil, inch

# Padstack parameters - Only use the ones you need
DB_TYPE = 'brd' #'board' # or 'brd' or 'package' or 'pkg' only
PLATING = 1 # 2.54e-5 m (1 mil) for a board and 18e-6 m for a package
CONDUCT_PADSTACK = 3.4e7 # 3.4e7 S/m for a board and 4.31e7 S/m for a package
MATERIAL = ''
INNERFILL_MATERIAL = None # Typically used for FIVR indcutor power and ground PTHs
OUTER_THICKNESS = None # Typically used for FIVR magnetic inductor power PTHs
OUTER_COATING_MATERIAL = None # Typically used for FIVR magnetic inductor power PTHs

# Outputs
# -------
PADSTACK_FILE_NAME = r"..\thinkpi_test_db\GNR\oblong_debug\M6186203_padstack.csv"
'''

"""

# ------------- User defined parameters -------------

# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\SRF\srf_ap_zcc_res_ext_2023_01_19_08_49_proc_vload_t_sense_23ww4p2.spd"

UNIT = 'm' # Only use one of the following units: nm, um, mm, cm, m, mil, inch

# Padstack parameters - Only use the ones you need
DB_TYPE = 'pkg' #'board' # or 'brd' or 'package' or 'pkg' only
PLATING = 2.54e-5 # 2.54e-5 m (1 mil) for a board and 18e-6 m for a package
CONDUCT_PADSTACK = 4.31e7 # 3.4e7 S/m for a board and 4.31e7 S/m for a package
MATERIAL = ''
INNERFILL_MATERIAL = None # Typically used for FIVR indcutor power and ground PTHs
OUTER_THICKNESS = None # Typically used for FIVR magnetic inductor power PTHs
OUTER_COATING_MATERIAL = None # Typically used for FIVR magnetic inductor power PTHs

# Outputs
# -------
PADSTACK_FILE_NAME = r"..\thinkpi_test_db\SRF\paddystacky_doe_padstack.csv"

"""

'''
# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\GNR\M6186203.spd"

UNIT = 'mil' # Only use one of the following units: nm, um, mm, cm, m, mil, inch

# Padstack parameters - Only use the ones you need
DB_TYPE = 'brd' #'board' or 'brd' or 'package' or 'pkg' only
PLATING = 1 # 2.54e-5 m (1 mil) for a board and 18e-6 m for a package
CONDUCT_PADSTACK = 3.4e7 # 3.4e7 S/m for a board and 4.31e7 S/m for a package
MATERIAL = ''
INNERFILL_MATERIAL = '' # Typically used for FIVR indcutor power and ground PTHs
OUTER_THICKNESS = None # Typically used for FIVR magnetic inductor power PTHs
OUTER_COATING_MATERIAL = '' # Typically used for FIVR magnetic inductor power PTHs

# Outputs
# -------
PADSTACK_FILE_NAME = r"..\thinkpi_test_db\GNR\M6186203_padstack.csv"
'''

# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\GNR\gnr_hcc_fullstack_pwr_100_2023_08_25_16_26.spd"

UNIT = 'um' # Only use one of the following units: nm, um, mm, cm, m, mil, inch

# Padstack parameters - Only use the ones you need
DB_TYPE = 'pkg' # 'board' or 'brd' or 'package' or 'pkg' only
BRD_PLATING = 18 # Can be None. 2.54e-5 m (1 mil) for a board and 18e-6 m for a package
PKG_GND_PLATING = 18 # Can be None
PKG_PWR_PLATING = 25 # Can be None
CONDUCT_PADSTACK = 4.31e7 # 3.4e7 S/m for a board and 4.31e7 S/m for a package
MATERIAL = ''
INNERFILL_MATERIAL = None # Typically used for FIVR indcutor power and ground PTHs
OUTER_THICKNESS = None # Typically used for FIVR magnetic inductor power PTHs
OUTER_COATING_MATERIAL = None # Typically used for FIVR magnetic inductor power PTHs

# Outputs
# -------
PADSTACK_FILE_NAME = r"..\thinkpi_test_db\GNR\gnr_hcc_fullstack_pwr_100_2023_08_25_16_26_padstack.csv"

# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks

if __name__ == '__main__':
    db = tasks.PsiTask(DATABASE_PATH_NAME)
    db.auto_setup_padstack(fname=PADSTACK_FILE_NAME, db_type=DB_TYPE,
                            brd_plating=BRD_PLATING,
                            pkg_gnd_plating=PKG_GND_PLATING,
                            pkg_pwr_plating=PKG_PWR_PLATING,
                            conduct=CONDUCT_PADSTACK, material=MATERIAL,
                            innerfill_material=INNERFILL_MATERIAL,
                            outer_thickness=OUTER_THICKNESS,
                            outer_coating_material=OUTER_COATING_MATERIAL,
                            unit=UNIT)
