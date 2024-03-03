# ------------- Introduction -------------
'''
In this phase the IdEM optimizer will try to find the best macromodel match
to the original extracted S-parameters.
Note that the user does not need to wait until the the optimization process is exhausted since
the real time intermediate best results are always available.
The user can monitor the intermediate results by inspecting the file idem_opt.log created in the idem folder.
In fact, while the optimization is running, the user can plot the five best results
and compare to the original extracted S-parameters by using the third phase.
Therefore, if a good match is achieved, the user can stop the optimization process.
'''

# ------------- User defined parameters -------------

# Inputs
# ------
SPARAM_PATH_NAME = r"D:\jrosenfe\ThinkPI\idem\OKS1_DNO5_bga9324_ww22_ANAcaps_cut_ports_2nd_071523_181825_32744_DCfitted.s47p"
TERMINATION_FILE_NAME = r"D:\jrosenfe\ThinkPI\idem\termination.csv"
CAPACITOR_MODEL_PATH = None

# The maximum frequency to consider during the optimization process.
# If None, the maximum frequency is derived from the S-parameters touchstone file.
# This parameter determines the frequency comparison range between the original and the macromodel S-parameters.
MAX_DATA_FREQ = 100e6 # Hz

#output_format options
    #1 or ASCII exports state-space matrices of a macromodel to a standard ASCII text file. The extension .mod.txt is used for this files. The format of these files is self-explanatory. 
    #2 or Touchstone exports macromodel to a standard Touchstone file. 
    #3 or SPICE generates the equivalent circuit in standard SPICE language. 
    #4 or ASTAP generates the equivalent circuit in ASTAP (PowerSpice) language. 
    #5 or SPECTRE-netlist generates the equivalent circuit in Cadence Spectre® language using a circuit-based realization. 
    #6 or SPECTRE-ZP generates the equivalent circuit in Cadence Spectre® language using a pole-zero representation. 
    #7 or HSPICE-netlist generates the equivalent circuit in standard Synopsys®HPICE® language using a circuit-based realization. 
    #8 or HSPICE-LAPLACE generates the equivalent circuit in standard Synopsys® HPICE® language using a Lapalce realization. The Laplace element provides a particularly efficient way for using IdEM models in HSPICE® transient simulations. The model is synthesized in pole/reside form (also known as Foster canonical form), and HPICE® uses this format in an efficient way by using a recursive convolution method. 
    #9 or HSPICE-POLE generates the equivalent circuit in standard Synopsys® HPICE® language using a pole-zero representation. 
    #10 or VERILOGA generates the equivalent circuit in Verilog-A language. 
    #11 or VHDL-AMS generates the equivalent circuit in VHDL-AMS language. 
    #12 or ADS generates the equivalent circuit in Agilent's ADS bbn language. 
    #13 or APLAC generates the equivalent circuit in APLAC language. 
    #14 or RFM-HSPICE generates the equivalent circuit in Synopsys® HPICE® language using rational function matrix (RFM). The resulting .rfm file can be read by HSPICE® using the proper syntax. A wrapper netlist is also generated, it will allow to launch the .rfm file directly. Such format will enable faster circuit simulation and is currently supported by circuit solvers for Scattering and Admittance representations only. 
    #15 or RFM-SPECTRE
OUTPUT_FORMAT = 'HSPICE-LAPLACE' # Use 'HSPICE-LAPLACE' for Hspice simulation or 'SPICE' for FIVR framework simulation
TARGET_ACCURACY = 1e-5 # The target accuracy IdEM will try to achieve between the original and macromodel S-parameters

MIN_BANDWIDTH = 90e6 # Minimun bandwidth of the macromodel in Hz
MAX_BANDWIDTH = 100e6 # Maximum bandwidth of the macromodel in Hz
# Specify None if linear point comparison is required.
# Otherwise logarithmic comparison with the specified points per decade will take place.
PTS_PER_DECADE = 15

# Number of points to try.
# The larger the number of steps the more likely to find a better match
# but the optimization time might also increase.
BANDWIDTH_STEPS = 100
REF_Z = [1, 10] # Port reference impedances to use in Ohm. Note that this is not a range.
MIN_ORDER = 2 # Minimum order of the macromodel
STEP_ORDER = 2 # The step to increase the order by
MAX_ORDER = 24 # Maximum order of the macromodel

# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks

if __name__ == '__main__':
    opt = tasks.IdemOptimizer(term_fname=TERMINATION_FILE_NAME,
                                sparam_fname=SPARAM_PATH_NAME,
                                cap_models=CAPACITOR_MODEL_PATH,
                                max_data_freq=MAX_DATA_FREQ,
                                output_format=OUTPUT_FORMAT,
                                acc=TARGET_ACCURACY,
                                pts_per_decade=PTS_PER_DECADE)

    opt.optimize(min_bw=MIN_BANDWIDTH, max_bw=MAX_BANDWIDTH,
                    bw_steps=BANDWIDTH_STEPS, 
                    refzs=REF_Z, order_min=MIN_ORDER,
                    order_step=STEP_ORDER,
                    order_max=MAX_ORDER)
    