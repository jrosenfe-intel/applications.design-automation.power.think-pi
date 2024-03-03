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

# Inputs
# ------
DATABASE_PATH_NAME = r'..\thinkpi_test_db\SRF\socket_et\AVC_SRF_AP_VIN_VOUT_fullPDC_electrothermal_v13.spd'

# PWR_NETS = ['PVCCIN_CPU0', 'VCCIN', 'VCCCFN_FLEX0_IODIE00']
# GND_NETS = ['GND_1', 'VSS', 'VSS']

PWR_NETS = ['VCCIN']
GND_NETS = ['VSS']
PLOT_GROUND = False

SIM_RESULT_FOLDER_NAME = r"..\thinkpi_test_db\SRF\socket_et\results"

# Outputs
# -------
REPORT_NAME = r"..\thinkpi_test_db\SRF\socket_et\result_summary.xlsx"

# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks
from thinkpi.operations import speed as spd

if __name__ == '__main__':
    db = spd.Database(DATABASE_PATH_NAME)
    db.load_flags['plots'] = False
    db.load_data()
    
    skt = tasks.SocketElectroThermalTask(db)
    skt.parse_sim_results(folder_name=SIM_RESULT_FOLDER_NAME,
                            pwr_nets=PWR_NETS, gnd_nets=GND_NETS,
                            report_fname=REPORT_NAME, plot_ground=PLOT_GROUND)
    
    
    