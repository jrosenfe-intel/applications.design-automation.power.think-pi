# ------------- Introduction -------------
'''
This is also an optional step. In this phase, sink map .csv file (from previous phase)
and simulation data from .xml file are used to create heatmaps for the
sinks' actual, minimum, and maximum average voltages.
'''

# ------------- User defined parameters -------------

# Inputs
# ------
XML_SIM_RESULTS = r'..\thinkpi_test_db\DMR\dmr_ap_ucc1_pwr_vccin_uciea_north_south_23ww42_odb_pdc_ready_SimulationResult.xml'
SINK_MAP_FILE = r'..\thinkpi_test_db\DMR\sink_map.csv'

# Outputs
# -------
HEATMAP_REPORT = r'..\thinkpi_test_db\DMR\sink_heatmaps.xlsx'

# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks
from thinkpi.operations import speed as spd
from thinkpi.waveforms import measurements as msr
import thinkpi.operations.loader as ld

pkg_ind = tasks.PdcTask()

pkg_ind.sink_heatmaps(XML_SIM_RESULTS,
                      SINK_MAP_FILE,
                      HEATMAP_REPORT
)
