# Definition of input parameters for the iccts.py application

raw_waveforms_folder = r'..\Icct_manipulation\raw_icct'
dashboard_file =  r'..\Icct_manipulation\icct_tuning_data\gnr_cfc_comp_7nm_2p7G_1p05V_100C_tx_icct_tool.xlsx'
mul = 1  # Non-mandatory parameter. To ignore specify 1.
suffix = '_tx'  # Specifies suffix to add to the new ictt file. Non-mandatory parameter. To ignore specify ''.
vnom = 1.05 # Specifies nominal voltage in Volts for all Iccts

# In Hz. Specify multiple BIB frequencies separated by commas: [f1, f2, ..., fn]
BIB_frequency = [6.25e6, 10e6]
# Duty cycle for the BIB waveform in percentage.
# Specify multiple duty cycles separated by commas: [d1, d2, ..., dn]
burst_duty_cycle = [50, 50]
