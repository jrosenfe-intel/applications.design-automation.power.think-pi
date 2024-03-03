from thinkpi.operations.loader import Waveforms


if __name__ == '__main__':
    # Load touchstone
    w = Waveforms()
    w.load_waves(r"..\thinkpi_test_sparam\gnr_fivr_io_flex_2021_10_11_15_4_ind_west_coax1p0_fixed_30Ohm.S29P")
    
    # Plot s, z, or y, parameters

    # Overlay all z-parameters
    w.cplot_overlay()
    # Overlay all s-parameters
    w.cplot_overlay(net_type='s')
    # Overlay element (3, 6)
    w.cplot_overlay(i=3, j=6)
    # Plot only Vout1, Vout3, and Vout5
    w.cplot_overlay(['Vout1', 'Vout3', 'Vout5'])
    # Create a new group of waveforms and plot it
    sw_group = w.group('SW0', 'SW1')
    sw_group.cplot_overlay()
    
