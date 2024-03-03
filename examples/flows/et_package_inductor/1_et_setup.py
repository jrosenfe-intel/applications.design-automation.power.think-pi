# ------------- Introduction -------------
r'''
In this phase, all the required setup steps are performed
to run electo-thermal package inductor simulation.
Note that this flow assumes the database to be preproccesed and cut but
without the vxbr* nets merged to the output plane.
In order to modify any of the material properties, user must
modify the thinkpi_conf.py file located at: ~\thinkpi\config\thinkpi_conf.py

The following tasks are executed:
- Select the switching phase nodes and output plane rail names
- Perform electro-thermal simulation setup
- Place sinks and VRMs
- Setup stackup and padstack
- Export sinks and VRM information for the user to update and use in the next phase
- Merge switching nets
'''

# ------------- User defined parameters -------------

r'''
# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\SRF\srf_ap_zcc_res_ext_2023_01_19_08_49_proc_vload_t_sense_23ww4p2.spd"
PROCESSED_DATABASE_NAME = None # If None the original databse will be overwritten

PWR_NET_NAMES = ['VXBR_CFC_E_PH0_CDIE09', 'VXBR_CFC_E_PH1_CDIE09',
                 'VXBR_CFC_E_PH2_CDIE09', 'VXBR_CFC_E_PH3_CDIE09', 'VCCCFC_E_CDIE09'] # You can also use wildcards
GND_NET_NAMES = 'VSS' # You can also use wildcards

AMBIENT_TEMPERATURE = 105 # This is the default value

NUM_SINKS=5
SINK_AREA = None # None is the default value
INDUCTOR_RAIL_UNDER_ANALYSIS = 'VCCCFC_E_CDIE09'
INDUCTOR_TRACES_LAYER = 'Signal$1bco' # 'Signal$1bco' is the default value
DIE_CIRCUIT_NAME = 'ddie' # 'ddie' is the default value
DIE_THICKNESS = 0.75e-3 # This is the default value
PCB_BOTTOM_TEMPERATURE = 105 # 105 is the default value

# If simulation is taking too long increase this value
MAXIMUM_MESH_EDGE = 0.06e-3 # 0.06e-3 is the default value.

SINK_SETUP_FILE = r"..\thinkpi_test_db\SRF\output_et_sink.csv"
VRM_SETUP_FILE = r"..\thinkpi_test_db\SRF\output_et_vrm.csv"

# For the following parameres, if None is provided, the value in the .spd file is used
DIELECTRIC_THICKNESS = 0.025e-3
METAL_THICKNESS = 0.035e-3
CORE_THICKNESS = 0.74e-3
MAGNETIC = True # Indicating if the package inductor is magnetic or ACI

NETS_TO_MERGE = ['VXBR_CFC_E_PH0_CDIE09', 'VXBR_CFC_E_PH1_CDIE09',
                 'VXBR_CFC_E_PH2_CDIE09', 'VXBR_CFC_E_PH3_CDIE09']

# Outputs
# -------
STACKUP_FILE = r"..\thinkpi_test_db\SRF\whateverIwant_doe_stackup.csv"
PADSTACK_FILE = r"..\thinkpi_test_db\SRF\paddystacky_doe_padstack.csv"
TCL_FILE_NAME = r"et_phase1.tcl"
'''

# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\DMR\dmr_ap_ucc1_fivr_fixdig_pdc_v2.spd"
# Assign None to overwrite the original file
NEW_DATABASE_NAME = r'..\thinkpi_test_db\DMR\dmr_ap_ucc1_fivr_fixdig_et.spd'

# You can also use wildcards
# Include in this list vxbr* nets as well
PWR_NET_NAMES = ['VCCFIXDIG_W_2', 'VXBR_FIXDIG_W_P0*']
GND_NET_NAMES = 'VSS_1' # You can also use wildcards

AMBIENT_TEMPERATURE = 105 # This is the default value
DEFAULT_VIA_CONDUCT = 4.3e7 # S/m for package

NUM_SINKS = 0 # Specify 0 to place no sinks
SINK_AREA = None # None is the default value
PLACE_VRMS = True # Specify False to place no VRMs
MERGE_VXBR = False

INDUCTOR_RAIL_UNDER_ANALYSIS = 'VCCFIXDIG_W_2'
INDUCTOR_TRACES_LAYER = 'Signal$1bco' # 'Signal$1bco' is the default value
DIE_CIRCUIT_NAME = 'ddie' # 'ddie' is the default value
DIE_THICKNESS = 0.75e-3 # This is the default value
PCB_BOTTOM_TEMPERATURE = 105 # 105 is the default value

# If simulation is taking too long increase this value
MAXIMUM_MESH_EDGE = None # If None will be automatically calculated

# For the following parameters
# If None is provided, the value in the .spd file is used
DIELECTRIC_THICKNESS = None
METAL_THICKNESS = None
CORE_THICKNESS = None
C4_DIAMETER = 70e-6 # In Meters. This is the default value.
MAGNETIC = True # Indicating if the package inductor is magnetic or ACI

# Must provide a value.
# For CoaMil 1.0 use 100e-6, and for CoaxMil 2.0 use 150e-6
OUTER_COATING_THICKNESS = 150e-6

PKG_GND_PLATING = 18e-6 # In meters
PKG_PWR_PLATING = 25e-6 # In meters. For Coax 1.0 use 18e-6.

# Outputs
# -------
STACKUP_FILE = r"..\thinkpi_test_db\DMR\dmr_ap_fixdig_ET_stackup.csv"
PADSTACK_FILE = r"..\thinkpi_test_db\DMR\dmr_ap_fixdig_ET_padstack.csv"
SINK_SETUP_FILE = r"..\thinkpi_test_db\DMR\dmr_ap_fixdig_et_sink.csv"
VRM_SETUP_FILE = r"..\thinkpi_test_db\DMR\dmr_ap_fixdig_et_vrm.csv"
TCL_FILE_NAME = r"..\thinkpi_test_db\DMR\dmr_ap_fixdig_et_phase1.tcl"


# ------------- Don't modify anything below this line -------------
from pathlib import Path
from thinkpi.flows import tasks

if __name__ == '__main__':
    TCL_FNAME = TCL_FILE_NAME.replace(Path(TCL_FILE_NAME).suffix, '_1.tcl')
    pkg_ind = tasks.PackageInductorElectroThermalTask(DATABASE_PATH_NAME)


    pkg_ind.select_nets(PWR_NET_NAMES, GND_NET_NAMES)
    pkg_ind.et_setup_phase1(db_fname=NEW_DATABASE_NAME,
                            temp=AMBIENT_TEMPERATURE,
                            default_conduct=DEFAULT_VIA_CONDUCT)
    pkg_ind.create_tcl(('Celsius Layout', 'E/TCoSimulation'),
                       TCL_FNAME)
    pkg_ind.run_tcl(TCL_FNAME, pkg_ind.exec_paths['sigrity'][0])

    if NEW_DATABASE_NAME is None:
        pkg_ind = tasks.PackageInductorElectroThermalTask(DATABASE_PATH_NAME)
    else:
        pkg_ind = tasks.PackageInductorElectroThermalTask(NEW_DATABASE_NAME)

    pkg_ind.select_nets(PWR_NET_NAMES, GND_NET_NAMES)
    if NUM_SINKS > 0:
        pkg_ind.place_sinks(num_sinks=NUM_SINKS, area=SINK_AREA)
    if PLACE_VRMS:
        pkg_ind.place_vrms()
    pkg_ind.db.save()
    pkg_ind.et_setup_phase2(ind_rail=INDUCTOR_RAIL_UNDER_ANALYSIS,
                            ind_layer=INDUCTOR_TRACES_LAYER,
                            die_name=DIE_CIRCUIT_NAME,
                            die_thickness=DIE_THICKNESS,
                            PCB_bot_temp=PCB_BOTTOM_TEMPERATURE,
                            mesh_edge=MAXIMUM_MESH_EDGE)
    
    pkg_ind.setup_stackup_padstack(stackup_fname=STACKUP_FILE,
                                    padstack_fname=PADSTACK_FILE,
                                    pkg_gnd_plating=PKG_GND_PLATING,
                                    pkg_pwr_plating=PKG_PWR_PLATING,
                                    dielec_thickness=DIELECTRIC_THICKNESS,
                                    metal_thickness=METAL_THICKNESS,
                                    core_thickness=CORE_THICKNESS,
                                    outer_thickness=OUTER_COATING_THICKNESS,
                                    c4_diameter=C4_DIAMETER,
                                    magnetic=MAGNETIC)
    TCL_FNAME = TCL_FILE_NAME.replace(Path(TCL_FILE_NAME).suffix, '_2.tcl')
    pkg_ind.create_tcl(('Celsius Layout', 'E/TCoSimulation'),
                       TCL_FNAME)
    pkg_ind.run_tcl(TCL_FNAME, pkg_ind.exec_paths['sigrity'][0])

    if NEW_DATABASE_NAME is None:
        pkg_ind = tasks.PackageInductorElectroThermalTask(DATABASE_PATH_NAME)
    else:
        pkg_ind = tasks.PackageInductorElectroThermalTask(NEW_DATABASE_NAME)
    pkg_ind.select_nets(PWR_NET_NAMES, GND_NET_NAMES)

    if MERGE_VXBR:
        pkg_ind.db.merge_nets(nets_to_merge=[net for net in pkg_ind.pwr_nets if 'vxbr' in net.lower()])
    if NUM_SINKS > 0:
        pkg_ind.export_sink_setup(fname=SINK_SETUP_FILE)
    if PLACE_VRMS:
        pkg_ind.export_vrm_setup(fname=VRM_SETUP_FILE)
