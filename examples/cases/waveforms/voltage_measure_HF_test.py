from thinkpi.waveforms.measurements import WaveMeasure


if __name__ == '__main__':
    
    r"""
    m = WaveMeasure(waves_path=r'..\thinkpi_test_db\OKS\DDR\wave_measure_test',
                    port_map=r'..\thinkpi_test_db\OKS\DDR\port_map_test.csv')
    m.voltage_waveform_measure_HF()
    m.create_heatmaps()
    m.create_node_report()
    m.create_group_report('*cdie*', 'v(pkg*')
    """
    
    #m.voltage_waveform_measure_HF(tstart=1.5e-8, tend=1.722e-8)
    
    r"""
    m = WaveMeasure(waves_path=r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\debug")
    m.voltage_waveform_measure_HF()
    m.create_node_report()
    m.create_group_report('*data*', '*cmd*')

    """
    
    m = WaveMeasure(waves_path=r'..\thinkpi_test_db\OKS\DDR\tr1',
                    port_map=r'..\thinkpi_test_db\OKS\DDR\nodes_v_thinkPI.csv')

    #m.voltage_waveform_measure_HF(1.5e-6, 1.9e-6)
    m.voltage_waveform_measure_HF()
    m.create_heatmaps()
    m.create_node_report()
    m.create_group_report('v(*ddrd*', 'v(*cmd*')
    
    


   
    
