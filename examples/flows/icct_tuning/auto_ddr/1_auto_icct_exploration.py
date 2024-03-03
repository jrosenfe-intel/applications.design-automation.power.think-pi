# ------------- Introduction -------------
'''
This is the first phase of the auto Icc(t) tuning procedure.
In this phase the user:
- loads the provided Icc(t)
- Visualizes and inspects them
- Determines the required time windows for the preamble, postamble,
  and data
'''

# ------------- User defined parameters -------------

# Inputs
# ------
PATH_TO_ICCT = r'..\thinkpi_test_db\OKS\icct_set1'


# ------------- Don't modify anything below this line -------------
from thinkpi.operations import loader as ld

if __name__ == '__main__':
    tr = ld.Waveforms()
    tr.load_waves(PATH_TO_ICCT)
    tr.y_unit = 'A'
    tr.plot_stack()
    tr # Prints waveform names on the screen to be used in the next phase



    
