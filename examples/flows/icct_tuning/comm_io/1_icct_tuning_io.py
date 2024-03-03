# ------------- Introduction -------------
'''
This is the first phase of the Icc(t) tuning for package io communication IPs.
In this phase the user:
- Setups configuration file located at ~\thinkpi\config\icct_config.py

The user is expected to define the following fields by
editing the above file in a text editor:
- raw_waveforms_folder
- dashboard_file
- mul: Non-mandatory parameter. To ignore specify 1.
- suffix: Specifies suffix to add to the new ictt file. Non-mandatory parameter. To ignore specify ''.
- vnom: Specifies nominal voltage in Volts for all Iccts
- BIB_frequency: In Hz. Specify multiple BIB frequencies separated by commas: [f1, f2, ..., fn]
- burst_duty_cycle: Specify multiple duty cycles separated by commas: [d1, d2, ..., dn]

'''


    
