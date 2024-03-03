# ------------- Introduction -------------
'''
This is the first phase of the Icc(t) tuning procedure.
In this phase the user:
- loads the provided Icc(t)
- Visualizes and inspects them
- Determines the required time windows for the preamble, postamble,
  and data
- Determines the number of bits from which to compose the BIB pattern
'''

# ------------- User defined parameters -------------

# Inputs
# ------
PATH_TO_ICCT = r'..\thinkpi_test_db\OKS\DDR\22ww41p5_hdc2_ddr_gen4_0p0_12.8GHz_fub_icct_fast_read.xlsx'


# ------------- Don't modify anything below this line -------------
from thinkpi.operations import loader as ld


if __name__ == '__main__':
    tr = ld.Waveforms()
    tr.load_waves(PATH_TO_ICCT)
    tr.plot_stack()
    tr # Prints waveform names on the screen to be used in the next phase
    
