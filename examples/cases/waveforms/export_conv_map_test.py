from thinkpi.waveforms.measurements import WaveMeasure

if __name__ == '__main__':
    grid = WaveMeasure(waves_path=r'..\thinkpi_test_db\OKS\DDR\tr')
    grid.export_port_map(r"..\thinkpi_test_db\OKS\DDR\name_conv.csv",
                        r"..\thinkpi_test_db\OKS\DDR\GNR-SP-XCC_CuDensity_worst4PD_2022_2_15.spd")

    


    
