from thinkpi.operations import loader as ld


if __name__ == '__main__':
    tr = ld.Waveforms()
    tr.load_waves(r'..\thinkpi_test_db\OKS\DDR\22ww41p5_hdc2_ddr_gen4_0p0_8GHz_fub_icct_slow_write.xlsx',
                    sheets=['data', 'cmd', 'clk'])

    tuned_icct = tr.tune_icct(preamble_start=2e-9, preamble_end=5.164e-9,
                                postamble_start=6.88e-9, postamble_end=1e-8,
                                freqs=[10e6, 25e6, 50e6], dutys=[50, 50, 50],
                                vnom=0.9, exclude=['vccddr_hv_clk'],
                                export_formats=['gpoly', 'PWL', 'csv'],
                                idle=(1.2e-6, 1.6e-6)
                            )
    
    #tuned_icct.y_unit = 'A'
    #tuned_icct.plot_stack()


    
