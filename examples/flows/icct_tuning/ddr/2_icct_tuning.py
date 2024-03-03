# ------------- Introduction -------------
'''
This is the second phase in which the user will use the parameters gathered
from the previous phase to create the BIB pattern.
Note that this operation can be performed on an individual waveform
or on a group of waveforms.
'''

# ------------- User defined parameters -------------

# Inputs
# ------
PATH_TO_ICCT = r'..\thinkpi_test_db\OKS\DDR\22ww41p5_hdc2_ddr_gen4_0p0_12.8GHz_fub_icct_fast_read.xlsx'

ICCT_WAVEFORM_NAME = 'vccddr_hv_data'
PREAMBLE_START = 2e-9 # In Seconds
PREAMBLE_END = 6.478e-9 # In Seconds
POSTAMBLE_START = 6.79e-9 # In Seconds
POSTAMBLE_END = 9.176e-9 # In Seconds
BIB_FREQUENCY = 85e6 # In Hz
DUTY_CYCLE = 50 # In %
# Number of bits to create the pattern.
# This number should be divisable by the BIT_PER_PACKET
NUM_BITS = 2
# There should be integer number of packets in the high level of the BIB pattern
BITS_PER_PACKET = 8

# Parameters used to save the new BIB pattern
FORMAT_TYPE = 'PWL' # Can be also 'gpoly' or 'csv'
FILE_NAME = None
VNOM = 1 # Only used with 'gpoly' format
SEP = ',' # Only used with 'csv' format
SUBCKT_NAME = None # Only used with 'gpoly' or 'PWL' formats

# ------------- Don't modify anything below this line -------------
from thinkpi.operations import loader as ld

if __name__ == '__main__':
    tr = ld.Waveforms()
    tr.load_waves(PATH_TO_ICCT)
    tuned_icct = tr.waves[ICCT_WAVEFORM_NAME].create_BIB_DDR(PREAMBLE_START,
                                                            PREAMBLE_END,
                                                            POSTAMBLE_START,
                                                            POSTAMBLE_END,
                                                            BIB_FREQUENCY,
                                                            DUTY_CYCLE,
                                                            NUM_BITS,
                                                            BITS_PER_PACKET
                                                        )
    tuned_icct.y_unit = 'A'
    tuned_icct.plot()
    tuned_icct.save(FORMAT_TYPE, FILE_NAME, VNOM, SEP, SUBCKT_NAME)

    
