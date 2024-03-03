from thinkpi.operations import loader as ld


if __name__ == '__main__':
    """
    ac = ld.Waveforms()
    ac.load_waves(r'..\thinkpi_test_db\main_zf_s_3.ac0',
                    x_unit='Hz', y_unit='Ohm')
    ac.plot_overlay(x_scale='M', xaxis_type='log')
    
    """

    tr = ld.Waveforms()
    tr.load_waves(r'..\thinkpi_test_db\OKS\DDR\main_tran_hf_post9601_vprobes_only.tr0',
                    fix=True)
    #tr.load_waves(r'..\thinkpi_test_db\OKS\DDR\main_tran_hf_2vprobes_1cktIprobe.tr0',
    #                fix=True)
    #tr.plot_stack(x_scale='n')

    #tr.load_waves(r'..\thinkpi_test_db\OKS\DDR\LF')
    
