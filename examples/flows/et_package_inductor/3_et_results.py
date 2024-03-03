# ------------- Introduction -------------
r'''
After running the electro-thermal simulation, an .xml result file should be created.
The user need to provide this file name to ThinkPI which will extract the information,
organize it, and calculate the new EM spec based on the simulation results.

Note that currently, there is a bug in PDC/Celsius and the user must manually
check the option to generate this .xml result file:
Tools > Options > Edit Options... > Simulation > Basic > Automatically save simulation result(.xml)

This phase will perform the following:
- load the xml file and process the data
- save report in Excel format

For this analysis the tabs of interest in the output Excel file are 'power_loss_summary'
and 'via_plane_current'. From the 'power_loss_summary' compute the total power, W_DC.
Next, upload the s-parameters of the extraction into PDA and record the
AC power loss, W_AC, at the total DC current, I_DC, that was used in the current
PowerDC simulation.
Calculate the 'inflated' new DC current to account for these AC losses and
rerun the simulation with this new total current:
I_inflated = I_DC*SQRT((W_AC + W_DC)/W_DC)

These steps are also explained in the BKM located at:
"\\amr\ec\proj\pandi\EPS1\EPS_Training\5_Advanced_Trainings\34_ACI_thermal_analysis\BKM\IDP-TH-0028-Current and Thermal Analysis Procedure for Inductors in PKG Substrate of Server Products_latest.pptx"
'''

# ------------- User defined parameters -------------

r'''
# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\GNR\gnr_lcc_patch_rev05a_2023_11_11_19_21_proc_et.spd"
SIM_RESULT_FILE_NAME = r"..\thinkpi_test_db\GNR\gnr_lcc_patch_rev05a_2023_11_11_19_21_proc_et_SimulationResult.xml"
IND_PWR_NET = 'VCCCORE_C4R6_CDIE09'
GND_NET = 'VSS_1'
PRODUCT_LIFETIME = 7 # Years

# Outputs
# -------
REPORT_NAME = r"..\thinkpi_test_db\GNR\result_summary.xlsx"
'''

r'''
# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\DMR\dmr_ap_ucc1_pwr_23ww43p3_VCCR_et_bottom_top_air_dev_splitvxbr_LDO.spd"
SIM_RESULT_FILE_NAME = r"..\thinkpi_test_db\DMR\dmr_ap_ucc1_pwr_23ww43p3_VCCR_et_bottom_top_air_dev_splitvxbr_LDO_SimulationResult.xml"
IND_PWR_NET = ['VCCR_C01_S3_*', 'VCCR_C23_s0', 'VXBR_R_CLST23_S0_*']
GND_NET = 'VSS_1'
PRODUCT_LIFETIME = 7 # Years

PKG_GND_PLATING = 18e-6 # In meters
PKG_PWR_PLATING = 25e-6 # In meters. For Coax 1.0 use 18e-6.

# Outputs
# -------
REPORT_NAME = r"..\thinkpi_test_db\DMR\ET_results_multinet.xlsx"
'''

# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\DMR\dmr_ap_ucc1_dcm_23ww43p3_v2_proc_cut_POR_LSC_24A_et.spd"
SIM_RESULT_FILE_NAME = r"..\thinkpi_test_db\DMR\dmr_ap_ucc1_dcm_23ww43p3_v2_proc_cut_POR_LSC_24A_et_SimulationResult.xml"
IND_PWR_NET = ['VCCDCM_D0_S0_2', 'VXBR_DCM_D0_S0_P0*']
GND_NET = 'VSS_1'
PRODUCT_LIFETIME = 7 # Years

PKG_GND_PLATING = 18e-6 # In meters
PKG_PWR_PLATING = 25e-6 # In meters. For Coax 1.0 use 18e-6.

# Outputs
# -------
REPORT_NAME = r"..\thinkpi_test_db\DMR\ET_results_DCM_24A.xlsx"

# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks

if __name__ == '__main__':
    pkg_ind = tasks.PackageInductorElectroThermalTask(DATABASE_PATH_NAME)

    pkg_ind.select_nets(IND_PWR_NET, GND_NET)
    pkg_ind.report_sim_results(xml_fname=SIM_RESULT_FILE_NAME,
                            pwr_plating=PKG_PWR_PLATING,
                            gnd_plating=PKG_GND_PLATING,
                            product_life=PRODUCT_LIFETIME,
                            report_fname=REPORT_NAME)
    
    
    