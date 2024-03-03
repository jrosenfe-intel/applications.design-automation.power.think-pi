# ------------- Introduction -------------
'''
In this phase, electro-thermal setup is performed.
Additionally, The user must update the VRM, sink, and LDO information in the csv files
created in the previous phase.
Once this is done, this phase will update that information in the specified database.

In summary, user must inspect and modify the following files before running this phase:
- SINK_SETUP_FILE
- VRM_SETUP_FILE
- LDO_SETUP_FILE
'''

# ------------- User defined parameters -------------

# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\GNR\ignr_hcc_int_fdr_patch_dfx_2023_11_29_16_44_board_merged.spd"

SINK_SETUP_FILE = r'..\thinkpi_test_db\GNR\GNR_sink_setup.csv'
VRM_SETUP_FILE = r'..\thinkpi_test_db\GNR\GNR_vrm_setup.csv'
LDO_SETUP_FILE = r'..\thinkpi_test_db\GNR\GNR_ldo_setup.csv'

AMBIENT_TEMP = 38 # In Celsius degrees
TOTAL_NUM_COMPUTE_AND_IO_DIES = 3

IHS_LENGTH = 104.5e-3 # In meters. This value should come form the mechanical drawing.
IHS_WIDTH = 70.5e-3 # In meters. This value should come form the mechanical drawing.
IHS_THICKNESS = 3e-3 # In meters. This value should come form the mechanical drawing.

HEATSINK_LENGTH = 127e-3 # In meters. This value should come form the mechanical drawing.
HEATSINK_WIDTH = 100e-3 # In meters. This value should come form the mechanical drawing.
HEATSINK_THICKNESS = 2.5e-3 # In meters. This value should come form the mechanical drawing.
HEATSINK_ADHESIVE_THICKNESS = 0.1e-3 # In meters. This value should come form the mechanical drawing.
HEATSINK_HTC = 2000 # In W/(m^2*C). Heatshink heat trasnfer coefficient.

TIM1_THICKNESS = 0.356e-3 # In meters. This value should come form the mechanical drawing.
VRM_VCCIN_LAYER = 'SignalBRD$TOP'
BRD_VCCIN_RAIL = 'PVCCIN_CPU0'

COMPUTE_POWER = 250 # In Watt per die
IO_POWER = 25 # In Watt per die

IC_THICKNESS = 0.5e-3 # In meters. This value should come form the mechanical drawing.
IC_TEMPERATURE = 105 # In Celsius degrees

PKG_GND_PLATING = 18e-6 # In meters
PKG_PWR_PLATING = 18e-6 # In meters

# Outputs
# -------
STACKUP_FILE_NAME = r'..\thinkpi_test_db\GNR\socket_et_stackup.csv'
PADSTACK_FILE_NAME = r'..\thinkpi_test_db\GNR\socket_et_padstack.csv'
DATABASE_PROCESSED = r"..\thinkpi_test_db\GNR\ignr_hcc_int_fdr_patch_dfx_2023_11_29_16_44_board_merged_ET.spd"
TCL_FILE_NAME = r'..\thinkpi_test_db\GNR\socket_et.tcl'

# ------------- Don't modify anything below this line -------------
from pathlib import Path
from thinkpi.flows import tasks
from thinkpi.config import thinkpi_conf as cfg
from thinkpi.operations import speed as spd

if __name__ == '__main__':
    db = spd.Database(DATABASE_PATH_NAME)
    db.load_flags['plots'] = False
    db.load_data()

    skt1 = tasks.SocketElectroThermalTask(db)
    r'''
    skt1.setup_stackup_padstack(stackup_fname=STACKUP_FILE_NAME,
                                padstack_fname=PADSTACK_FILE_NAME,
                                pkg_gnd_plating=PKG_GND_PLATING,
                                pkg_pwr_plating=PKG_PWR_PLATING)
    '''
    skt1.et_socket_setup_phase1(db_fname=DATABASE_PROCESSED,
                                num_dies=TOTAL_NUM_COMPUTE_AND_IO_DIES,
                               ihs_length=IHS_LENGTH,
                               ihs_width=IHS_WIDTH,
                               ihs_thickness=IHS_THICKNESS,
                               hs_length=HEATSINK_LENGTH,
                               hs_width=HEATSINK_WIDTH,
                               hs_thickness=HEATSINK_THICKNESS,
                               tim1_thickness=TIM1_THICKNESS,
                               power_mosfets_plane=VRM_VCCIN_LAYER,
                               power_mosfets_rail=BRD_VCCIN_RAIL,
                               compute_power=COMPUTE_POWER,
                               io_power=IO_POWER,
                               heatsink_htc=HEATSINK_HTC,
                               hs_adhesive_thickness=HEATSINK_ADHESIVE_THICKNESS,
                               temp=AMBIENT_TEMP)

    TCL_FILE_NAME_ph1 = f'{str(Path(TCL_FILE_NAME).stem)}_phase3_1.tcl'
    skt1.create_tcl(('Celsius Layout', 'E/TCoSimulation'),
                    TCL_FILE_NAME_ph1)
    skt1.run_tcl(TCL_FILE_NAME_ph1, skt1.exec_paths['sigrity'][0])

    db.load_data()
    skt2 = tasks.SocketElectroThermalTask(db)
    skt2.et_socket_setup_phase2(node_coords=skt1.power_ic_coords,
                                comp_thickness=IC_THICKNESS,
                                temp=IC_TEMPERATURE)
    TCL_FILE_NAME_ph2 = f'{str(Path(TCL_FILE_NAME).stem)}_phase3_2.tcl'
    skt2.create_tcl(('Celsius Layout', 'E/TCoSimulation'),
                    TCL_FILE_NAME_ph2)
    skt2.run_tcl(TCL_FILE_NAME_ph2, skt2.exec_paths['sigrity'][0])

    db.load_data()
    skt2.import_sink_setup(SINK_SETUP_FILE)
    skt2.import_vrm_setup(VRM_SETUP_FILE)
    skt2.import_ldo_setup(LDO_SETUP_FILE)
    skt2.db.save()

    
    
    
    