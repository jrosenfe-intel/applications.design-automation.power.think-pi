# ------------- Introduction -------------
'''
In this phase all the required VRMs, sinks, and LDOs, are placed.
Additionally, the corresponding .csv setup files for each group is created.
The user is expected to fill in the required information in these files
to be used in the next phase.
'''

# ------------- User defined parameters -------------

# Inputs
# ------
MERGED_DATABASE_NAME = r"..\thinkpi_test_db\GNR\ignr_hcc_int_fdr_patch_dfx_2023_11_29_16_44_board_merged.spd"
INPUT_RAILS = ['VCCIN', 'VCCFA_EHV_FIVRA']

NETS_TO_MERGE = 'VXBR*'
VRM_PWR_RAILS = ['PVCCIN_CPU0', 'PVCCINFAON_CPU0',
                 'PVCCFA_EHV_FIVRA_CPU0_1', 'PVCCFA_EHV_CPU0',
                 'PVCCD1_HV_CPU0', 'PVCCD0_HV_CPU0', 'PVNN_MAIN_CPU0_1']

VRM_LAYER = 'SignalBRD$TOP'
SINK_LAYER = 'SignalPKGPKG$surface_outer'

SINK_PWR_RAILS = ['VCCVNN', 'VCCIO_*', 'VCCINF', 'VCCHDC_*',
                  'VCCFA_EHV', 'VCCD_HV*',
                  'VCCDDRD*', 'VCCDDRA*', 'VCCCORE*', 'VCCCFN*',
                  'VCCCFC_*']

CAP_FINDER = 'PKGPKGC*'

# Outputs
# -------
SINK_SETUP_FILE = r'..\thinkpi_test_db\GNR\GNR_sink_setup.csv'
VRM_SETUP_FILE = r'..\thinkpi_test_db\GNR\GNR_vrm_setup.csv'
LDO_SETUP_FILE = r'..\thinkpi_test_db\GNR\GNR_ldo_setup.csv'
TCL_FILE_NAME = r'..\thinkpi_test_db\GNR\GNR_brd_pkg_merged.tcl'

# ------------- Don't modify anything below this line -------------
from pathlib import Path
from thinkpi.flows import tasks
from thinkpi.operations import speed as spd

if __name__ == '__main__':
    db = spd.Database(MERGED_DATABASE_NAME)
    db.load_flags['plots'] = False
    db.load_data()
    brd_pkg = tasks.SocketElectroThermalTask(db)
    
    brd_pkg.db.find_pwr_gnd_shorts()
    brd_pkg.place_vrms(VRM_LAYER, VRM_PWR_RAILS)
    brd_pkg.place_sinks(SINK_LAYER, SINK_PWR_RAILS, 1, CAP_FINDER)
    brd_pkg.export_sink_setup(SINK_SETUP_FILE)
    brd_pkg.export_vrm_setup(VRM_SETUP_FILE)
    brd_pkg.db.save()
    
    ldo_nodes = brd_pkg.place_ldo_circuits(INPUT_RAILS, NETS_TO_MERGE)
    TCL_FILE_NAME_ph1 = TCL_FILE_NAME.replace(Path(TCL_FILE_NAME).suffix,
                                              f'_phase2_1{Path(TCL_FILE_NAME).suffix}')
    brd_pkg.create_tcl(('Celsius Layout', 'E/TCoSimulation'),
                    TCL_FILE_NAME_ph1)
    brd_pkg.run_tcl(TCL_FILE_NAME_ph1, brd_pkg.exec_paths['sigrity'][0])

    db.load_data()
    brd_pkg = tasks.SocketElectroThermalTask(db)
    brd_pkg.place_ldos(*ldo_nodes)
    TCL_FILE_NAME_ph2 = TCL_FILE_NAME.replace(Path(TCL_FILE_NAME).suffix,
                                              f'_phase2_2{Path(TCL_FILE_NAME).suffix}')
    brd_pkg.create_tcl(('Celsius Layout', 'E/TCoSimulation'),
                    TCL_FILE_NAME_ph2)
    brd_pkg.run_tcl(TCL_FILE_NAME_ph2, brd_pkg.exec_paths['sigrity'][0])
    
    db.load_data()
    ldo_db = tasks.SocketElectroThermalTask(db)
    ldo_db.export_ldo_setup(LDO_SETUP_FILE)

