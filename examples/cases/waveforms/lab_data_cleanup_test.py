import thinkpi.operations.loader as ld
from thinkpi.operations.filters import Filter
from thinkpi.waveforms.measurements import WaveMeasure


if __name__ == '__main__':
    w = ld.Waveforms()
    w.load_waves(r"..\measurements\OKS\lab", add_fname=True)

    # NOTE: All the operations below can be applied on a group
    # of waveforms as well.

    # Print the loaded waveforms
    # You can access individual waveforms by w[0], w[1], etc. notation
    print(w)

    # Plot all waveforms in a stackup form
    w.plot_stack()

    # Define a filter
    # To see all the filter options invoke help(Filter)
    lowpass = Filter(filter_name='butterworth',
                    order=3, cutoff_freq=100e3,
                    filter_type='lowpass', ts=1e-6)
    
    # Shift waveform to start from time 0
    # and apply filter on a specific waveform
    filtered_waveform = w[0].shift().filt(lowpass)
    
    # Overlay the plots of w[0] before and after filtering
    w.plot_overlay([w[0].shift(), filtered_waveform])

    # Denoise a waveform to reduce noise but keep
    # the rise and fall time as sharp as in the original waveform.
    # The denoised function will automatically plot the before and after results.
    # To explore the denoise function parameters invoke help(w[5].denoise)
    w[5].denoise()

    r'''Another approach would be to apply post processing operations
        on a given waveform or a folder of waveforms.
        This includes, clipping, shifting, and resampling.
        The new generated waveform(s) are saved as .csv files.
    
    m = WaveMeasure()
    m.post_process(fname=r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\DDR\wave_measure_test",
                    tstart_clip=1e-8,
                    tend_clip=1.4e-8)
    '''
   
    
