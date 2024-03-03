# ------------- Introduction -------------
'''
Exports current database stackup in the form of .csv files.
Based on provided parameters, fields will be populated with the corresponding values.
The task will export the prefilled stackup and padstack of the database.
The user can modify the parameters in these files and use them in other flows.

If a parameter is set to None the existing value in the loaded .spd file is used.
Alternatively, if a parameter is set to '', the new padstack value will be set to blank.
'''

# ------------- User defined parameters -------------

r'''
# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\OKS\dmr-ap_ppf_12ch_vccin_pdslice_ccb-io_north_0050422.spd"

UNIT = 'um' # Only use one of the following units: nm, um, mm, cm, m, mil, inch

# If None is used, the parameters in the original spd file are used
# If '' is used, the specific parameter will be blank
DIELECT_THICKNESS = None
METAL_THICKNESS = None
CORE_THICKNESS = None
CONDUCT_STACKUP = None
DIELEC_MATERIAL = None
METAL_MATERIAL = None
CORE_MATERIAL = None
FILLIN_DIELEC_MATERIAL = None
ER = 2.1
LOSS_TANGENT = 0.1

# Outputs
# -------
STACKUP_FILE_NAME = r"..\thinkpi_test_db\OKS\dmr-ap_ppf_12ch_vccin_pdslice_ccb-io_north_0050422_stackup.csv"
'''

# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\CWF\cwf_ap_point_cfc_23ww37p1_patch.spd"

UNIT = 'um' # Only use one of the following units: nm, um, mm, cm, m, mil, inch

# If None is used, the parameters in the original spd file are used
# If '' is used, the specific parameter will be blank
DIELECT_THICKNESS = None
METAL_THICKNESS = None
CORE_THICKNESS = None
CONDUCT_STACKUP = None
DIELEC_MATERIAL = 'GY18E_90C/Dry(Rev4)'
METAL_MATERIAL = 'PackageCopper'
CORE_MATERIAL = 'R1515V_700um_90C/Dry(Rev2)'
FILLIN_DIELEC_MATERIAL = 'GY18E_90C/Dry(Rev4)'
ER = None
LOSS_TANGENT = None

# Outputs
# -------
STACKUP_FILE_NAME = r"..\thinkpi_test_db\CWF\cwf_ap_point_cfc_23ww37p1_patch_stackup.csv"
# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks

if __name__ == '__main__':
    db = tasks.PsiTask(DATABASE_PATH_NAME)

    db.auto_setup_stackup(fname=STACKUP_FILE_NAME, dielec_thickness=DIELECT_THICKNESS,
                            metal_thickness=METAL_THICKNESS, core_thickness=CORE_THICKNESS,
                            conduct=CONDUCT_STACKUP, dielec_material=DIELEC_MATERIAL,
                            metal_material=METAL_MATERIAL, core_material=CORE_MATERIAL,
                            fillin_dielec_material=FILLIN_DIELEC_MATERIAL,
                            er=ER, loss_tangent=LOSS_TANGENT,
                            unit=UNIT)
    