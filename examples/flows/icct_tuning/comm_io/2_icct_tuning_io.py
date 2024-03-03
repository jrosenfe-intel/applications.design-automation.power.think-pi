# ------------- Introduction -------------
'''
This is the second phase of the Icc(t) tuning for package io communication procedure.
In this phase the user:
- loads the provided Icc(t)
- Visualizes and inspects the signals
- Determines the required start and end time windows for the signals
- Fills out the dashboard .xlsx file with the required information
'''

# ------------- Don't modify anything below this line -------------
from thinkpi.operations import loader as ld
from thinkpi.config import icct_config as cfg

if __name__ == '__main__':
    w = ld.Waveforms()
    w.create_BIB_IO(cfg=cfg, raw_only=True)
    
    
