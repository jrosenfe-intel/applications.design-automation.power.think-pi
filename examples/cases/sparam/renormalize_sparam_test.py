from thinkpi.operations.loader import Waveforms


if __name__ == '__main__':
    # Load touchstone
    w = Waveforms()
    #w.load_waves(r"..\thinkpi_test_sparam\gnr_fivr_io_flex_2021_10_11_15_4_ind_west_coax1p0_fixed_30Ohm.S29P")
    w.load_waves(r"..\thinkpi_test_sparam\dmr_ap_ppf_12ch_vccin_pdslice_ccb_io_north_0050422_ports_portbox4_052922_052415_9560_DCfittedP_30ohm.s271p")
    w.renormalize_imp(10)

    # Renormalizes and saves a new Touchstone file
    # in one command
    w.save_touchstone(fname='test', refz=50)
    
    
