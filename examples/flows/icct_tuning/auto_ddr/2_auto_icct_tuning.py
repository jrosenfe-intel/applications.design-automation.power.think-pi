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
PATH_TO_ICCT = r'..\thinkpi_test_db\OKS\icct_set1'
FIX = False # If True, removes violated data points from the vector

# User can add as many tuning frequencies as required
# followed by a duty cycle
FREQS = [21.88e6] # In Hz
DUTY_CYCLE = [50] # In %

VNOM = 0.9 # In V
PREAMBLE_START = 0 # In Seconds
PREAMBLE_END = 10e-9 # In Seconds
DATA_START = 20e-9 # In Seconds
DATA_END = 22e-9 # In Seconds
POSTAMBLE_START = 35e-9 # In Seconds
POSTAMBLE_END = 40.05e-9 # In Seconds

# If True, indicating to save the tuned icc(t)
# using the original file name.
# If False will use the waveform name as the file name.
KEEP_ORIGINAL_FNAME = True

# If True and saving in csv format, indicating to save the tuned icc(t)
# with header names. If False and saving in csv format,
# header title will not be used.
INCLUDE_HEADER = False

# A list of waveform names to exclude from the process
# of creating a BIB pattern. Instead, the excluded waveforms, will be
# saved without changes.
EXCLUDE_WAVES = None

# The value of the idle portion of the waveform.
# If None, uses the first point as the idle values.
# Otherwise a tuple of 2 floats should be provided,
# indicating the start and end time window.
# An average value of idle is calculated based on the
# waveform amplitude within this time window per each waveform,
IDLE = None

# Can use any combination of the these formats: 'gpoly', 'PWL', 'csv'
EXPORT_FORMATS = ['csv']


# ------------- Don't modify anything below this line -------------
from thinkpi.operations import loader as ld


if __name__ == '__main__':
    tr = ld.Waveforms()
    tr.load_waves(PATH_TO_ICCT, fix=FIX)

    tuned_icct = tr.tune_icct(preamble_start=PREAMBLE_START,
                            preamble_end=PREAMBLE_END,
                            data_start=DATA_START,
                            data_end=DATA_END,
                            postamble_start=POSTAMBLE_START,
                            postamble_end=POSTAMBLE_END,
                            keep_original_fname=KEEP_ORIGINAL_FNAME,
                            include_header=INCLUDE_HEADER,
                            freqs=FREQS, dutys=DUTY_CYCLE,
                            vnom=VNOM, exclude=EXCLUDE_WAVES,
                            export_formats=EXPORT_FORMATS,
                            idle=IDLE
                        )
    
    # Plot all resulting BIB waveforms
    for waves in tuned_icct.values():
        waves.y_unit = 'A'
        waves.plot_stack()


    
