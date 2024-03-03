import thinkpi.operations.loader as ld
from thinkpi.operations import calculations as calc


if __name__ == '__main__':
    waves = ld.Waveforms()
    waves.load_waves(r"D:\jrosenfe\ThinkPI\measurements\OKS\vccin_waveform")
    waves.plot_stack()

    tuned_waves = waves.resonance_tuning(
                        low2high_start=0.102e-6,
                        high2low_start=1.1e-6,
                        freq=1.5e6, duty=50)
    tuned_waves.save('PWL')
    tuned_waves.plot_stack()
    