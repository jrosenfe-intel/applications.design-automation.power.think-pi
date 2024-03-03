# ThinkPI latest code paths
# -------------------------
SOURCE_CORE = r'\\amr\ec\proj\pandi\EPS1\EPS_Training\5_Advanced_Trainings\59_ThinkPI\1_ThinkPi_Repo\core_latest'
SOURCE_BACKEND = r'\\amr\ec\proj\pandi\EPS1\EPS_Training\5_Advanced_Trainings\59_ThinkPI\1_ThinkPi_Repo\app_latest\backend'
DEST_CORE = r'C:\thinkpi\core_latest'
DEST_BACKEND = r'C:\thinkpi\app\backend'
BACKEND_PORT = 8000


# User environment varibales
# --------------------------
# OMP_NUM_THREADS: Avoiding memory leakage when sklearn is used for the kmean algorithm
# PDC_SUPPORT_LARGE_POWRLOSS_CONVERT_RATE: Enabling more than 100% LDO efficiency in PDC for the socket electro-magnetic analysis
ENVIRON_VARS = {'OMP_NUM_THREADS': '1',
                'PDC_SUPPORT_LARGE_POWRLOSS_CONVERT_RATE': '1'}

# Tools paths
# -----------
SIMPLIS_EXEC = r'C:\Program Files\SIMetrix900\bin64\SIMetrix.exe'
SIGRITY_EXEC = r'C:\Cadence\Sigrity2021.1\tools\bin\powersi.exe'
HSPICE_EXEC = r'C:\Synopsys\Hspice_P-2019.06-SP2-3\WIN64'
IDEM_EXEC = r'C:\Program Files (x86)\CST Studio Suite 2021\AMD64'

# Simplis scripts
# ---------------
SIMPLIS_PARSER = 'simplis_parse_power_distribution_netlist_1.sxscr'
SIMPLIS_SYMBOL = 'simplis_create_pdn_symbol_1.sxscr'

# ATTD component browser API links
# --------------------------------
ECC_URL = r'https://ecc.intel.com/eccapi' # This is the API address, note it will change someday to something like ecc.intel.com/blah/blah
AUTHORITY_URL = r'https://login.microsoftonline.com/46c98d88-e344-4ed4-8496-4ed7712e255d' # This is where we get the tokens and includes Intel's tenant ID
SCOPE = r'api://afe78f57-3ebe-4f96-b1b2-e7806c93fc23/ecccb.read' # This is the component browser api scope - we are not using this for access today but a scope is needed
COMP_BROWSER_API_CLIENT_ID = 'afe78f57-3ebe-4f96-b1b2-e7806c93fc23' # This is the ATTD Component Browser API application (client) ID in Azure

# Material files
# --------------
ET_MATERIAL_FILE = r"pkg_thermal_materials_WW25'23.txt" # r"pkg_thermal_materials_WW5'22.txt"
ET_LGA_MATERIAL_FILE = r"lga_thermal_materials_WW5'22.txt"

# eTPS thermal parameters
# -----------------------
ETPS_PLANE_DENSITY = 800 # A/mm^2
ETPS_MAX_PLANE_DENSITY = 3000 # A/mm^2
ETPS_IAVG = {49: 850, 55: 1100, 60: 1300,
            75: 2000, 120: 5100, 150: 6000,
            180: 7300, 250: 10000}
ETPS_TEMP_SCALE = {80: 15, 85: 10, 90: 7, 95: 5,
                    100: 3.5, 105: 2.6, 110: 1.9,
                    115: 1.4, 120: 1, 125: 0.74,
                    130: 0.56}
ETPS_YEARS_SCALE = {1: 4.37, 2: 2.6, 3: 1.9, 4: 1.5, 5: 1.3, 6: 1.1,
                    7: 1, 8: 0.9, 9: 0.82, 10: 0.76, 11: 0.71,
                    12: 0.66, 13: 0.62, 14: 0.59, 15: 0.56}

# Electro-thermal parameters
# --------------------------
DIELECT_MATERIAL = 'Dielectric_BU' # Name depends on the ET_MATERIAL_FILE
METAL_MATERIAL = 'Copper_PKG_Mean' # Name depends on the ET_MATERIAL_FILE
CORE_MATERIAL = 'Dielectric_C' # Name depends on the ET_MATERIAL_FILE
FILLIN_DIELEC_MATERIAL = 'Dielectric_BU' # Name depends on the ET_MATERIAL_FILE
SOCKET_CAVITY_MATERIAL = 'Cavity' # Name depends on the ET_LGA_MATERIAL_FILE
SOCKET_PIN_MATERIAL = 'Pin_SKT'
SOCKET_PIN_DIAMETER = 0.18e-3 # In meters
BOARD_DIELEC_MATERIAL = 'FR-4' # Name depends on the ET_LGA_MATERIAL_FILE
BOARD_METAL_MATERIAL = 'Copper_EDA_BRD' # Name depends on the ET_LGA_MATERIAL_FILE
SOCKET_LAYER_THICKNESS = 2.7e-3
BUMP_THICKNESS = 0.045e-3 # Confirm with the package process technology, PDWG
DIE_THICKNESS = 0.7e-3
CAP_THICKNESS = 3e-3
PLATING = 18e-6 # In meters
PKG_GND_PLATING = 18e-6  # In meters
PKG_PWR_PLATING = 25e-6 # In meters
INNERFILL_MATERIAL = 'Epoxy_BT' # For magnetic PTHs. Name depends on the ET_MATERIAL_FILE
OUTER_THICKNESS = 150e-6 # For magnetic PTHs
OUTER_COATING_MATERIAL = 'AMP2' # For magnetic PTHs
C4_MATERIAL = 'C4_Bump_Solder_Copper' # Name depends on the ET_MATERIAL_FILE
C4_DIAMETER = 77e-6 # Confirm with eTPS document
TIM1_MATERIAL = 'TIM_1' # Name depends on the ET_LGA_MATERIAL_FILE
TIM1_IO_MATERIAL = 'TIM1IO' # Name depends on the ET_LGA_MATERIAL_FILE
TIM1_COMPUTE_MATERIAL = 'TIM1C' # Name depends on the ET_LGA_MATERIAL_FILE
DIE_MATERIAL = 'Silicon' # Name depends on the ET_LGA_MATERIAL_FILE
ADHESIVE_MATERIAL = 'Thermal_Plastic' # Name depends on the ET_LGA_MATERIAL_FILE
ADHESIVE_THICKNESS = 0.15e-3
HS_ADHESIVE_MATERIAL = 'TIM_2'
IC_MATERIAL = 'MoldingCompound' # Name depends on the ET_LGA_MATERIAL_FILE
IC_THICKNESS = 0.5e-3 # In meters
IC_TEMPERATURE = 105 # in ⁰C
