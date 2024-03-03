from thinkpi.operations.loader import Waveforms


if __name__ == '__main__':
    # Load touchstone
    w = Waveforms()
    w.load_waves(r"..\thinkpi_test_sparam\gnr_fivr_io_flex_2021_10_11_15_4_ind_west_coax1p0_fixed_30Ohm.S29P")
    
    # @ 90 MHz
    w.ind_char(freq=90e6)

    # Plot loop inductance and resistance between ports
    # This is good to evaluate decap effectivness
    ind, res = w.heatmap_cap(freq=90e6, cap_ports=['SW0', 'SW1'],
                            exclude_ports=['2:9'])
    print(ind)
    print(res)

    # Create inductance and resistance Excel heatmaps of the package inductor
    w.heatmap_ind_res(r'..\thinkpi_test_sparam\VCCIO_Flex_port_map.csv', 90e6)

