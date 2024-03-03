# ------------- Introduction -------------
'''
This is the third phase of the Icc(t) tuning for package io communication procedure.
In this phase the user:
- Runs the icct BIB creation process, based on the provided information
'''

# ------------- Don't modify anything below this line -------------
from thinkpi.operations import loader as ld
from thinkpi.config import icct_config as cfg

if __name__ == '__main__':
    w = ld.Waveforms()
    w.create_BIB_IO(cfg=cfg)