from thinkpi.flows import tasks

if __name__ == '__main__':
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

    opt = tasks.IdemOptimizer(term_fname=r"E:\Users\jrosenfe\ThinkPI\data\idem_optimizer\termination.csv",
                                sparam_fname=r"E:\Users\jrosenfe\ThinkPI\data\idem\sparams\OKS1_NFF1S_DNOX_PWRsims_ww03_processed_all_ports_clip_012623_173538_30544_DCfitted.s29p",
                                cap_models=r'E:\Users\jrosenfe\ThinkPI\data\idem_optimizer\caps',
                                max_data_freq=200e6,
                                output_format='SPICE',
                                acc=1e-5)
    
    opt.optimize(min_bw=100e6, max_bw=200e6, bw_steps=100, 
                 refzs=[1, 10], order_min=2, order_step=2,
                 order_max=24)
    