from thinkpi.waveforms.measurements import WaveMeasure


if __name__ == '__main__':
    m = WaveMeasure()

    m.post_process(fname=r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\DDR\wave_measure_test",
                    tstart_clip=1e-8,
                    tend_clip=1.4e-8)
   
    
