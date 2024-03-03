from thinkpi.waveforms.measurements import WaveMeasure


if __name__ == '__main__':
    m = WaveMeasure(waves_path=r'..\thinkpi_test_db\OKS\DDR\LF',
                    port_map=r'..\thinkpi_test_db\OKS\DDR\port_map_LF.csv')

    '''
    m.voltage_waveform_measure_LF(tDC_unload=199.785e-6,
                                tfirst_droop=200.001e-6,
                                tsecond_droop=200.043e-6,
                                tthird_droop=201.111e-6,
                                tDC_load=436.156e-6,
                                tfirst_over=450.001e-6,
                                tsecond_over=450.042e-6,
                                tthird_over=452.536e-6
                            )
    '''

    m.voltage_waveform_measure_LF()
    m.create_heatmaps()
    m.create_node_report()
    m.create_group_report('*ch2*', '*ch7*')

    m.plot()

    """

    m = WaveMeasure(waves_path=r'..\thinkpi_test_db\OKS\DDR\LF_Andrea',
                    port_map=r'..\thinkpi_test_db\OKS\DDR\port_map.csv')
    m.voltage_waveform_measure_LF()
    m.create_heatmaps()
    m.create_node_report()
    m.create_group_report('*phy*')
    """




    
