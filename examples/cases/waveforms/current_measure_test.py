from thinkpi.waveforms.measurements import WaveMeasure


if __name__ == '__main__':
    m = WaveMeasure(waves_path=r'..\thinkpi_test_db\OKS\DDR\wave_measure_test',
                    port_map=r'..\thinkpi_test_db\OKS\DDR\port_map_test.csv')
    
    '''
    m.current_waveform_measure(tmin=(6.5e-11, 5.6e-10),
                                tmax=(3.374e-9, 1.7e-8),
                                tslew=(6.598e-10, 9.2e-10),
                                tpeak=(None, None)
                            )
    '''
    m.current_waveform_measure()
    m.create_heatmaps()
    m.create_node_report('i(x_cdie*')
    m.create_group_report('i(x_cdie*')


    
