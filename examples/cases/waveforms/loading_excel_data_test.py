from thinkpi.operations import loader as ld


if __name__ == '__main__':
    tr = ld.Waveforms()
    tr.load_waves(r'..\Daniel\ddr', y_unit='A')
    tr.plot_stack(x_scale='n', y_scale='m')
    
    
