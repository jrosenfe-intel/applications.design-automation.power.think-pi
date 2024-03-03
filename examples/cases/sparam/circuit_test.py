from thinkpi.operations.loader import Waveforms
from thinkpi.operations.circuits import Circuits


if __name__ == '__main__':
    # Load touchstone
    w = Waveforms()
    w.load_waves(r"..\thinkpi_test_sparam\AVC_SCH0124_master_0127_fivra_012921_134552_16752_DCfitted.s75p")
    
    caps = Circuits(r'..\thinkpi_test_sparam\cap_models', w)
    caps.load_models()
    caps.create_map(r'..\thinkpi_test_sparam\cap_models\cap_model_map.csv')

    # Can also use tuples
    caps2 = Circuits(r'..\thinkpi_test_sparam\cap_models', w)
    caps2.load_models()
    caps2.create_map(('C2104_bot_0805_47u', 'CapTDK_0201_VLP_100nF_1Vdc_90C_EOL.sp'),
                    ('C236_bot_0805_47u', 'CapTDK_0201_VLP_100nF_1Vdc_90C_EOL.sp'))

