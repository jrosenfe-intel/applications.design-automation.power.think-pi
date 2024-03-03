# ------------- Introduction -------------
'''
Automatically preprocess a package or board database,
as well as setups layout for PowerSi extracttion.
Note that if the user desires to setup stackup or/and padstack
they must first export the corresponding .csv files using
the 1_stackup_export.py and 2_padstack_export.py flow, respectively.

This preprocessing flow implements the following tasks:
- import material file (if provided)
- disable all nets
- Net selection and classification
- color nets
- cut out region of interest (if provided)
- convert traces to shapes
- perform shape processing
- convert pads to shapes
- split nets
- setup stackup
- setup padstack
- disable all components
- define special voids
- assign default via conductivity (if provided)
- general check of shorts in the layout
'''

# ------------- User defined parameters -------------

r'''
# Inputs
# ------
DATABASE_PATH_NAME = r"D:\jrosenfe\ThinkPI\thinkpi_test_db\CWF\CWF_SP_A12345_MIN_2023_05_30.spd"

PWR_NET_NAMES = ['VCCD_HV0', 'VCCD_HV1', 'VCCFA_EHV', 'VCCFA_EHV_FIVRA', 'VCCINF', 'VCCVNN'] # You can also use wildcards
GND_NET_NAMES = 'VSS' # You can also use wildcards

# To avoid setup of a stackup provide None
STACKUP_FILE_NAME = r"D:\jrosenfe\ThinkPI\thinkpi_test_db\CWF\stackup_CWF_SP.csv"
# To avoid setup of a padstack provide None
PADSTACK_FILE_NAME = r"D:\jrosenfe\ThinkPI\thinkpi_test_db\CWF\padstack_CWF_SP.csv"
# If material file is not provided user must provide default conductivity
# Material file should be provided by ATTD based on your technology or your PI lead
MATERIAL_FILE_NAME = r"D:\jrosenfe\ThinkPI\thinkpi_test_db\CWF\ATTD_Package_Material_Library_PowerSI1276_Server_Rev_23_15_2.txt"
# If default conductivity is not provided user must provide material file
DEFAULT_CONDUCTIVITY = None
CUT_MARGIN = 0 # In meters. Use 0 to avoid cutting.
PROCESSED_DATABASE_PATH_NAME = r"D:\jrosenfe\ThinkPI\thinkpi_test_db\CWF\CWF_SP_A12345_MIN_2023_05_30_preproc.spd"

SIMULATION_TEMPERATURE = 90
START_FREQUENCY = 0
END_FREQUENCY = 2e9

# Outputs
# -------
TCL_FILE_NAME = 'CWF_SP_preprocess_db.tcl'
'''

r'''

# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\DCC\M84472-001.spd"

PWR_NET_NAMES = ['PVCCFA_EHV_CPU0'] # You can also use wildcards
GND_NET_NAMES = 'GND' # You can also use wildcards

# To avoid setup of a stackup provide None
STACKUP_FILE_NAME = r"..\thinkpi_test_db\DCC\stackup.csv"
# To avoid setup of a padstack provide None
PADSTACK_FILE_NAME = r"..\thinkpi_test_db\DCC\padstack.csv"
# If material file is not provided user must provide default conductivity
# Material file should be provided by ATTD based on your technology or your PI lead
MATERIAL_FILE_NAME = None
# If default conductivity is not provided user must provide material file
DEFAULT_CONDUCTIVITY = None
CUT_MARGIN = 0 # In meters. Use 0 to avoid cutting.
PROCESSED_DATABASE_PATH_NAME = r"..\thinkpi_test_db\DCC\M84472-001_PVCCFA_EHV_CPU0_proc.spd"

SIMULATION_TEMPERATURE = 90
START_FREQUENCY = 0
END_FREQUENCY = 2e9

# Outputs
# -------
TCL_FILE_NAME = 'preprocess_db.tcl'
'''

r'''
# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\GNR\gnr_hcc_fullstack_pwr_100_2023_08_25_16_26.spd"

PWR_NET_NAMES = ['VXBR*', 'VCC*IODIE00', 'VCC*IODIE04'] # You can also use wildcards
GND_NET_NAMES = 'VSS' # You can also use wildcards

# To avoid setup of a stackup provide None
STACKUP_FILE_NAME = r"..\thinkpi_test_db\GNR\gnr_hcc_fullstack_pwr_100_2023_08_25_16_26_stackup.csv"
# To avoid setup of a padstack provide None
PADSTACK_FILE_NAME = r"..\thinkpi_test_db\GNR\gnr_hcc_fullstack_pwr_100_2023_08_25_16_26_padstack.csv"
# If material file is not provided user must provide default conductivity
# Material file should be provided by ATTD based on your technology or your PI lead
MATERIAL_FILE_NAME = None
# If default conductivity is not provided user must provide material file
DEFAULT_CONDUCTIVITY = 4.31e7
CUT_MARGIN = 0 # In meters. Use 0 to avoid cutting.
DELETE_UNUSED_NETS = False
PROCESSED_DATABASE_PATH_NAME = r"..\thinkpi_test_db\GNR\gnr_hcc_fullstack_pwr_100_2023_08_25_16_26_processed.spd"

SIMULATION_TEMPERATURE = 110
START_FREQUENCY = 0
END_FREQUENCY = 1e9

# Outputs
# -------
TCL_FILE_NAME = 'GNR_SP_HCC_FIVR_preprocess_db.tcl'
'''

r'''
# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\OKS\et\dmr_ap_ucc1_pwr_vccin_uciea_ring_23ww42_odb.spd"
PROCESSED_DATABASE_PATH_NAME = r"..\thinkpi_test_db\OKS\et\dmr_ap_ucc1_pwr_vccin_uciea_north_south_23ww42_odb_pdc_proc.spd"

PWR_NET_NAMES = ['VCCUCIEA_SE', 'VCCUCIEA_SW',
                 'VXBR_UCIEA_SE*', 'VXBR_UCIEA_SW*'] # You can also use wildcards
GND_NET_NAMES = 'VSS' # You can also use wildcards

# To avoid setup of a stackup provide None
STACKUP_FILE_NAME = None
# To avoid setup of a padstack provide None
PADSTACK_FILE_NAME = None
# If material file is not provided user must provide default conductivity
# Material file should be provided by ATTD based on your technology or your PI lead
MATERIAL_FILE_NAME = None
# If default conductivity is not provided user must provide material file
DEFAULT_CONDUCTIVITY = 4.31e7
CUT_MARGIN = 1e-3 # In meters. Use 0 to avoid cutting.
DELETE_UNUSED_NETS = True

# Outputs
# -------
TCL_FILE_NAME = 'preprocess.tcl'
'''

r'''
DATABASE_PATH_NAME = r"..\thinkpi_test_db\FHF\M87461-001_GNR_WS_ERB_FAB1_REV0P65_WW46P2_A10.spd"
PROCESSED_DATABASE_PATH_NAME = r"..\thinkpi_test_db\FHF\M87461-001_GNR_WS_ERB_FAB1_REV0P65_WW46P2_A10_INF.spd"

#PWR_NET_NAMES = ['?VCCIN_CPU0', '?VCCFA_EHV_CPU0', '?VCCFA_EHV_FIVRA_CPU0', '?VCCINFAON_CPU0', '?VCCD?_HV_CPU0', '?VNN_MAIN_CPU0']
PWR_NET_NAMES = ['?VCCINF']
#+VCCD0_HV
GND_NET_NAMES = 'GND' # You can also use wildcards

# To avoid setup of a stackup provide None
STACKUP_FILE_NAME = r"..\thinkpi_test_db\FHF\M87461-001_GNR_WS_ERB_FAB1_REV0P453_WW28P3_A5_stackup.csv"
# To avoid setup of a padstack provide None
PADSTACK_FILE_NAME = None
# If material file is not provided user must provide default conductivity
# Material file should be provided by ATTD based on your technology or your PI lead
MATERIAL_FILE_NAME = None
# If default conductivity is not provided user must provide material file
DEFAULT_CONDUCTIVITY = 3.4e7

# Margin to leave around nets of interest in METERS.
# when cut is performed. If 0 is provided no cut is performed.
CUT_MARGIN = 3e-3 # In Meters

DELETE_UNUSED_NETS = True


# Outputs
# -------
TCL_FILE_NAME = 'preprocess.tcl'

'''

DATABASE_PATH_NAME = r"..\thinkpi_test_db\DMR\dmr_ap_ucc1_pwr_vccin_uciea_ring_23ww42_odb.spd"
PROCESSED_DATABASE_PATH_NAME =r"..\thinkpi_test_db\DMR\dmr_ap_ucc1_pwr_vccin_uciea_ring_23ww42_odb_proc.spd"

PWR_NET_NAMES = ['VCCUCIEA_SE','VXBR_UCIEA_SE*'] # You can also use wildcards
GND_NET_NAMES = 'VSS' # You can also use wildcards

# To avoid setup of a stackup provide None
STACKUP_FILE_NAME = r'..\thinkpi_test_db\DMR\dmr_ucei_stackup.csv'
# To avoid setup of a padstack provide None
PADSTACK_FILE_NAME = r"..\thinkpi_test_db\DMR\dmr_ucei_padstack.csv"
# If material file is not provided user must provide default conductivity
# Material file should be provided by ATTD based on your technology or your PI lead
MATERIAL_FILE_NAME = r'..\thinkpi_test_db\DMR\ATTD_Package_Material_Library_PowerSI_Rev_23_40_0.txt'
# If default conductivity is not provided user must provide material file
DEFAULT_CONDUCTIVITY = None

# Margin to leave around nets of interest in METERS.
# when cut is performed. If 0 is provided no cut is performed.
CUT_MARGIN = 0 # In Meters

DELETE_UNUSED_NETS = False


# Outputs
# -------
TCL_FILE_NAME =r'dmr_ucie_preprocess.tcl'


# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks
from thinkpi.operations import speed as spd

if __name__ == '__main__':
    db = spd.Database(DATABASE_PATH_NAME)
    db.load_flags['plots'] = False
    db.load_data()
    db.delete_overlap_vias()
    db = tasks.TasksBase(db)
    db.select_nets(PWR_NET_NAMES, GND_NET_NAMES)
    db.preprocess(STACKUP_FILE_NAME, PADSTACK_FILE_NAME, MATERIAL_FILE_NAME,
                    DEFAULT_CONDUCTIVITY, CUT_MARGIN, PROCESSED_DATABASE_PATH_NAME,
                    DELETE_UNUSED_NETS)
    
    db.create_tcl(('PowerSI', 'extraction'), TCL_FILE_NAME)
    db.run_tcl(TCL_FILE_NAME, db.exec_paths['sigrity'][0])

   

    

    

    