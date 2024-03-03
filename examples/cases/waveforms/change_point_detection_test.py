from thinkpi.operations import loader as ld


if __name__ == '__main__':
    tr = ld.Waveforms()
    #tr.load_waves(r'..\Daniel\dmr', y_unit='A')
    tr.load_waves(r'..\Ruben\GNR', y_unit='A')
    results = tr.detect_change_points()
    for wave_name, result in results.items():
        print(wave_name)
        print(result)
    
