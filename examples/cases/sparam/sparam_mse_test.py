from thinkpi.operations.loader import Waveforms
from thinkpi.operations.circuits import Circuits


if __name__ == '__main__':
    # Load touchstone
    psi = Waveforms()
    psi.load_waves(r"..\thinkpi_test_sparam\gnr_fivr_io_flex_2021_10_11_15_4_ind_west_coax1p0_fixed_30Ohm.S29P")
    
    idem = Waveforms()
    idem.load_waves(r"..\thinkpi_test_sparam\gnr_fivr_io_flex_2021_10_11_15_4_ind_west_coax1p0_fixed_30Ohm_IDEM.S29P")
    
    # Print the mean square error starting from 1 MHz
    psi.mean_sqaure_error(idem, tstart=1e6)

    # Overlay plot the two groups
    # The reason to load them again since the port name is the same and group plotting may not work
    w = Waveforms(['*30Ohm*.s29p'])
    w.load_waves(r"..\thinkpi_test_sparam")
    wg1 = w.group('0:29')
    print(wg1)
    wg2 = w.group('29:')
    print(wg2)
    w.cplot_overlay([wg1, wg2], clr='group')

