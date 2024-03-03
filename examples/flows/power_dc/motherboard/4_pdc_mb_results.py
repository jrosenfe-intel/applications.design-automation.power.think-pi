# ------------- Introduction -------------
'''
This is the fourth phase of the DC analysis setup and analysis
where PowerDC simulation results are processed.

This task will perform the following:
- record results as xml file
- load the xml file and process the data
- visualize pin current heatmap in the web-browser
- save report in Excel format

For each package and board results, a dictionary of DataFrames
objects is returned with the following catagories:
- 'via_temperature'
- 'plane_temperature'
- 'vrms'
- 'sinks'
- 'power_loss_summary'
- 'power_loss_per_component'
- 'power_loss_per_layer'
- 'power_loss_per_net'
- 'via_plane_current'
- 'pin_current_bins_pwr'
- 'pin_current_bins_gnd'
- 'volt_dist'
'''

# ------------- User defined parameters -------------
r'''
MERGED_DATABASE_NAME = r'C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\GNR\GNR_UCC_FIVRA_PDC_Rev0_v21.spd'

SIM_RESULT_FILE_NAME = r'C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\GNR\pdc_results_test.xml'
VOLT_DIST_PATH = r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\GNR\gnr_ucc_cfn_io_odb_2020_10_8_13_36_vccio_1stx_v22_Distribution_Text_Files"
BRD_PWR_NET = 'PVCCFA_EHV_FIVRA_CPU0'
BRD_GND_NET = 'GND_1'
PKG_PWR_NET = 'FIVRA'
PKG_GND_NET = 'VSS'
PKG_REPORT_NAME = r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\GNR\pkg_report.xlsx"
BRD_REPORT_NAME = r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\GNR\brd_report.xlsx"
'''

r"""
# Inputs
# ------
MERGED_DATABASE_NAME = r'..\thinkpi_test_db\spr\brd_interposer_pkg_SPR.spd'

SIM_RESULT_FILE_NAME = r'..\thinkpi_test_db\spr\brd_interposer_pkg_SPR_SimulationResult.xml'
# If you don't have this folder available specify None
VOLT_DIST_PATH = r"..\thinkpi_test_db\spr\brd_interposer_pkg_SPR_Distribution_Text_Files"
BRD_PWR_NET = 'PVCCINFAON_CPU0'
BRD_GND_NET = 'GND'
PKG_PWR_NET = 'VCCINFAON'
PKG_GND_NET = 'VSS'

PLOT_GROUND = False # Defines if ground net is plotted
PLOT_SCALE = 1 # Increase to greater than 1 to increase size of plotted pins

# Outputs
# -------
PKG_REPORT_NAME = r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\spr\pkg_report.xlsx"
BRD_REPORT_NAME = r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\spr\brd_report.xlsx"
"""

# Inputs
# ------
MERGED_DATABASE_NAME = r'..\thinkpi_test_db\OKS\OKS1_NFF1S_DNOX_bga9280_vccin8_ww07b_opt2_cut_ports_pkg_merge.spd'

SIM_RESULT_FILE_NAME = r'..\thinkpi_test_db\OKS\OKS1_NFF1S_DNOX_bga9280_vccin8_ww07b_opt2_cut_ports_pkg_merge_Result_Files_070623_104654\OKS1_NFF1S_DNOX_bga9280_vccin8_ww07b_opt2_cut_ports_pkg_merge_SimulationResult.xml'
# If you don't have this folder available specify None
VOLT_DIST_PATH = r"..\thinkpi_test_db\OKS\OKS1_NFF1S_DNOX_bga9280_vccin8_ww07b_opt2_cut_ports_pkg_merge_Result_Files_070623_104654\OKS1_NFF1S_DNOX_bga9280_vccin8_ww07b_opt2_cut_ports_pkg_merge_Distribution_Text_Files"
BRD_PWR_NET = 'PVCCIN_CPU0_NORTH_1'
BRD_GND_NET = 'GND'
PKG_PWR_NET = 'VCCIN_1'
PKG_GND_NET = 'VSS'

PLOT_GROUND = False # Defines if ground net is plotted
PLOT_SCALE = 1 # Increase to greater than 1 to increase size of plotted pins

# Outputs
# -------
PKG_REPORT_NAME = r"..\thinkpi_test_db\OKS\baseline_pkg_report.xlsx"
BRD_REPORT_NAME = r"..\thinkpi_test_db\OKS\baseline_brd_report.xlsx"

# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks
from thinkpi.operations import speed as spd

if __name__ == '__main__':
    db = spd.Database(MERGED_DATABASE_NAME)
    db.load_flags['plots'] = False
    db.load_data()

    brd_pkg = tasks.PdcTask(db)

    pkg_results = brd_pkg.parse_sim_results(SIM_RESULT_FILE_NAME,
                                            PKG_PWR_NET, PKG_GND_NET,
                                            VOLT_DIST_PATH,
                                            PKG_REPORT_NAME,
                                            PLOT_GROUND,
                                            PLOT_SCALE
                                        )

    brd_results = brd_pkg.parse_sim_results(SIM_RESULT_FILE_NAME,
                                            BRD_PWR_NET, BRD_GND_NET,
                                            VOLT_DIST_PATH,
                                            BRD_REPORT_NAME,
                                            PLOT_GROUND,
                                            PLOT_SCALE
                                        )
    

    





    