from thinkpi.waveforms.measurements import WaveMeasure
from thinkpi.operations.filters import Filter


if __name__ == '__main__':
        r'''
        m = WaveMeasure(waves_path=r'..\thinkpi_test_db\OKS\DDR\wave_measure_test',
                        port_map=r'..\thinkpi_test_db\OKS\DDR\port_map_test.csv')
        
        # Define filters
        low_pass = Filter(filter_name='butterworth',
                        order=5, cutoff_freq=10e6,
                        filter_type='lowpass', ts=100e-12)
        high_pass = Filter(filter_name='butterworth',
                        order=5, cutoff_freq=10e6,
                        filter_type='highpass', ts=100e-12)
        
        #m.filter_waveform_measure(filter=low_pass,
        #                            tstart=2e-9, tend=8e-9)
        m.filter_waveform_measure(filter=high_pass)
        m.create_heatmaps()
        m.create_node_report()
        m.create_group_report('*cdie*', 'v(pkg*')
        '''
        
        r'''
        m = WaveMeasure(waves_path=r'..\OKS\measurements\waveforms',
                        port_map=r'..\OKS\measurements\grid_dmr_ap_vccana_x52_c4.csv')
        
        # Define filters
        lowpass = Filter(filter_name='butterworth',
                        order=3, cutoff_freq=100e3,
                        filter_type='lowpass', ts=1e-10)
        highpass = Filter(filter_name='butterworth',
                        order=3, cutoff_freq=100e3,
                        filter_type='highpass', ts=1e-10)
        filters = [lowpass, highpass]
        
        # Run measurements
        for filter in filters:
        suffix = (f'{filter.filter_type}_'
                f"{str(filter.cutoff_freq/1e6).replace('.', 'p')}MHz")
        m.filter_waveform_measure(filter=filter,
                                        tstart=0, tend=150e-6)
        m.create_heatmaps(suffix=suffix)
        m.create_node_report(suffix=suffix)
        m.create_group_report('v(pkg_c*',
                                suffix=suffix)
        
        m.plot_filtered(suffix=suffix,
                        num_waves=1)
        '''
        
        r"""
        m = WaveMeasure(waves_path=r'..\GNR\measurements\waveforms',
                        port_map='..\GNR\measurements\gnr_hcc_vccin_vccd_fivra_inf_odb_2023_05_23_18_44_PCIE0_cut_process_boxes_updatev3_map.csv')
        
        # Define filters
        lowpass = Filter(filter_name='butterworth',
                        order=3, cutoff_freq=10e6,
                        filter_type='lowpass', ts=1e-10)
        highpass = Filter(filter_name='butterworth',
                        order=3, cutoff_freq=10e6,
                        filter_type='highpass', ts=1e-10)
        filters = [lowpass, highpass]
        
        # Run measurements
        for filter in filters:
        suffix = (f'{filter.filter_type}_'
                f"{str(filter.cutoff_freq/1e6).replace('.', 'p')}")
        m.filter_waveform_measure(filter=filter,
                                        tstart=0, tend=150e-6)
        m.create_heatmaps(suffix=suffix)
        m.create_node_report(suffix=suffix)
        m.create_group_report('v(pkg_c*',
                                suffix=suffix)
        
        m.plot_filtered(suffix=suffix,
                        num_waves=3)
        """
        
        m = WaveMeasure(waves_path=r'..\measurements\GNR\waveforms_spectre_sampled',
                        port_map=None)
    
        # Define filters
        lowpass = Filter(filter_name='butterworth',
                            order=3, cutoff_freq=10e6,
                            filter_type='lowpass', ts=1e-8)
        highpass = Filter(filter_name='butterworth',
                            order=3, cutoff_freq=10e6,
                            filter_type='highpass', ts=1e-8)
        filters = [lowpass, highpass]

        # Run measurements
        for filter in filters:
            suffix = (f'{filter.filter_type}_'
                    f"{str(filter.cutoff_freq/1e6).replace('.', 'p')}MHz")
            m.filter_waveform_measure(filter=filter,
                                      tstart=0.9e-6, tend=3.5e-6)
            #m.create_heatmaps(suffix=suffix)
            #m.create_node_report(suffix=suffix)
            m.create_group_report('Vout*',
                                  suffix=suffix)

            m.plot_filtered(suffix=suffix,
                            num_waves=5)


    


    
