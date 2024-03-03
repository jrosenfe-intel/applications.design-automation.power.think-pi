# ------------- Introduction -------------
'''
This flow is dedicated to FIVR package inductor(s) power DC analysis.
The starting point of this flow is with a preprocessed databse.

In this phase the following tasks will be performed:
- place sinks on the surface layer
- place VRMs on the VXBR* nets on the surface layer
- export sink and vrm .csv paramteres files
  which the user can modify and use in the next phase
- enable bypassing PowerDC confirmation
- enable adding nodes to pads
- set simulation temperature

After completion of this phase, inspect the new generated .csv files
and update them as needeed. These files will be used in the next phase.
'''

# ------------- User defined parameters -------------

r'''
# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\SRF\fivr_dc\srf_ap_zcc_res_ext_2023_01_19_08_49_proc_vload_t_sense_23ww4p2.spd"

# You can also use wildcards
PWR_NET_NAMES = ['VXBR_CFC_E_*_CDIE09', 'VCCCFC_E_CDIE09'] # You can also use wildcards
GND_NET_NAMES = 'VSS'

NUM_SINKS=5
SINK_AREA = None # or (xbot, ybot, xtop, ytop); None is the default value

# You can also use wildcards
VRM_NETS = ['VXBR_CFC_E_*_CDIE09']

SIM_TEMPERATURE = 90

# Outputs
# -------
SINK_SETUP_FILE = r"..\thinkpi_test_db\SRF\fivr_dc\SRF_sinksetup.csv"
VRM_SETUP_FILE = r"..\thinkpi_test_db\SRF\fivr_dc\SRF_vrmsetup.csv"
TCL_FILE_NAME = r"..\thinkpi_test_db\SRF\fivr_dc\SRF_FIVR_setup.tcl"
'''

# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\GNR\gnr_hcc_fullstack_pwr_100_2023_08_25_16_26_processed.spd"

# You can also use wildcards
PWR_NET_NAMES = ['VXBR*IODIE00', 'VXBR*IODIE04', 'VCC*IODIE00', 'VCC*IODIE04'] # You can also use wildcards
GND_NET_NAMES = 'VSS_1'

NUM_SINKS=1
SINK_AREA = None # or (xbot, ybot, xtop, ytop); None is the default value

SIM_TEMPERATURE = 110

# Outputs
# -------
SINK_SETUP_FILE = r"..\thinkpi_test_db\GNR\gnr_hcc_iodie_sinksetup.csv"
VRM_SETUP_FILE = r"..\thinkpi_test_db\GNR\gnr_hcc_iodie_vrmsetup.csv"
TCL_FILE_NAME = r"..\thinkpi_test_db\GNR\gnr_hcc_iodie_sinksetup_setup.tcl"

# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks
from thinkpi.operations import speed as spd

if __name__ == '__main__':
    db = spd.Database(DATABASE_PATH_NAME)
    db.load_flags['plots'] = False
    db.load_data()

    pkg_ind = tasks.PackageInductorElectroThermalTask(db)
    pkg_ind.select_nets(PWR_NET_NAMES, GND_NET_NAMES)
    pkg_ind.place_sinks(num_sinks=NUM_SINKS, area=SINK_AREA,
                        use_top_layer=True)
    pkg_ind.place_vrms()
    pkg_ind.export_sink_setup(fname=SINK_SETUP_FILE)
    pkg_ind.export_vrm_setup(fname=VRM_SETUP_FILE)
    pkg_ind.db.save()
    
    pkg_ind = tasks.PdcTask(db)
    pkg_ind.pdc_setup(SIM_TEMPERATURE, shape_process=False)
    pkg_ind.create_tcl(('PowerDC', 'IRDropAnalysis'),
                       TCL_FILE_NAME)
    pkg_ind.run_tcl(TCL_FILE_NAME, pkg_ind.exec_paths['sigrity'][0])
    