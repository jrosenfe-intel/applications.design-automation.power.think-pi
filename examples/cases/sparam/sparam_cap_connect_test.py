from thinkpi.operations.loader import Waveforms
from thinkpi.operations.circuits import Circuits


if __name__ == '__main__':
    # Load touchstone
    w = Waveforms()
    w.load_waves(r"..\thinkpi_test_sparam\AVC_SCH0124_master_0127_fivra_012921_134552_16752_DCfitted.s75p")
    
    caps = Circuits(r'..\thinkpi_test_sparam\cap_models', w)
    caps.load_models()
    caps.create_map(r'..\thinkpi_test_sparam\cap_models\cap_model_map.csv')

    net = w.terminate(('circuit', caps))
    net.plot_overlay(x_scale='M', y_scale='',
                    xaxis_type='log', yaxis_type='log')

