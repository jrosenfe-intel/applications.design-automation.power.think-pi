# ------------- Introduction -------------
'''
This is the final phase of the DC FIVR analysis,
where PowerDC simulation results are processed.

This task will perform the following:
- load the xml, and distribution files and process the data
- save report in Excel format

A dictionary of DataFrames
objects is returned with the following catagories:
- 'vrms'
- 'sinks'
- 'power_loss_summary'
- 'power_loss_per_component'
- 'power_loss_per_layer'
- 'power_loss_per_net'
- 'via_plane_current'
- 'volt_dist'
'''

# ------------- User defined parameters -------------

'''
# Inputs
# ------
MERGED_DATABASE_NAME = r'..\thinkpi_test_db\GNR\gnr_hcc_fullstack_pwr_100_2023_08_25_16_26_processed_vxbr_merge.spd'

SIM_RESULT_FILE_NAME = r'..\thinkpi_test_db\GNR\gnr_hcc_fullstack_pwr_100_2023_08_25_16_26_processed_vxbr_merge_Result_Files_091923_161623\gnr_hcc_fullstack_pwr_100_2023_08_25_16_26_processed_vxbr_merge_SimulationResult.xml'
# If you don't have this folder available specify None
VOLT_DIST_PATH = r"..\thinkpi_test_db\GNR\gnr_hcc_fullstack_pwr_100_2023_08_25_16_26_processed_vxbr_merge_Result_Files_091923_161623\gnr_hcc_fullstack_pwr_100_2023_08_25_16_26_processed_vxbr_merge_Distribution_Text_Files"

PWR_NET_NAMES = ['VCC*IODIE00', 'VCC*IODIE04'] # You can also use wildcards
#PWR_NET_NAMES = 'VCCCFC_M0_IODIE00'
GND_NET_NAMES = 'VSS_1'

# Outputs
# -------
PKG_REPORT_NAME = r"..\thinkpi_test_db\GNR\gnr_hcc_fivr_pkg_report.xlsx"
'''

# Inputs
# ------
MERGED_DATABASE_NAME = r'..\thinkpi_test_db\DMR\dmr_ap_ucc1_pwr_vccin_uciea_north_south_23ww42_odb_pdc_ready.spd'

SIM_RESULT_FILE_NAME = r'..\thinkpi_test_db\DMR\dmr_ap_ucc1_pwr_vccin_uciea_north_south_23ww42_odb_pdc_ready_SimulationResult.xml'
# If you don't have this folder available specify None
VOLT_DIST_PATH = None

PWR_NET_NAMES = 'VCCUCIEA_SE' # You can also use wildcards
#PWR_NET_NAMES = 'VCCCFC_M0_IODIE00'
GND_NET_NAMES = 'VSS_1'

# Outputs
# -------
PKG_REPORT_NAME = r"..\thinkpi_test_db\DMR\dmr_vccuciea_report.xlsx"


# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks
from thinkpi.operations import speed as spd

if __name__ == '__main__':
    db = spd.Database(MERGED_DATABASE_NAME)
    db.load_flags['plots'] = False
    db.load_data()

    pkg_ind = tasks.PdcTask(db)
    pkg_ind.select_nets(PWR_NET_NAMES, GND_NET_NAMES)

    results = pkg_ind.parse_fivr_results(SIM_RESULT_FILE_NAME,
                                        VOLT_DIST_PATH,
                                        PKG_REPORT_NAME
                                        )
    
    

    
    
    

    





    