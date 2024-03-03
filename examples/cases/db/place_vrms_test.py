from thinkpi.flows import tasks

if __name__ == '__main__':
    
    brd = tasks.PdcTask(
        r'..\thinkpi_test_db\SKX\H47993-001.spd'
    )
    brd.place_vrms(layer='Signal$TOP',
                    net_name='PVCCIN_CPU0')
    brd.db.save('vrm_test.spd')

    
    """
    brd = tasks.PdcTask(
        r'..\thinkpi_test_db\DMR\dmr_ap_23ww3p6_odb_OKS1_NFF1S_DNOX_PWRsims_ww3.spd'
    )
    brd.place_vrms(layer='SignalBRD$TOP',
                    net_name='PVCCA_HV_1')
    brd.db.save('dmr_vrm_test.spd')
    """
    
    """
    brd = tasks.PdcTask(
        r'..\thinkpi_test_db\OKS\db\brd_pkg_OKS_12CH.spd'
    )
    brd.place_vrms(layer='SignalBRD$TOP',
                    net_name='PVCCIN_CPU0_NORTH')
    brd.db.save('vrm_test.spd')
    """
    

    """
    brd = tasks.PdcTask(
        r'..\thinkpi_test_db\OKS\db\OKS1_NFF1S_DNOX_dmr-16-8ch_ucie_4l_min_ww5p2.spd'
    )
    brd.place_vrms(layer='SignalBRD$TOP',
                    net_name='PVCCINFAON_CPU0')
    brd.db.save('oks_vrm_test.spd')
    """

    """
    brd = tasks.PdcTask(
        r'..\thinkpi_test_db\SFR\AVC_SRF_AP_VIN_VOUT_fullPDC.spd'
    )
    brd.place_vrms(layer='SignalBRD$TOP',
                    net_name=['PVCCIN_CPU0', 'PVCCINF_CPU0',
                                'PVCCFA_EHV_FIVRA_CPU0',
                                'PVCCFA_EHV_CPU0',
                                'PVNN_MAIN_CPU0',
                                'PVCCD1_HV_CPU0',
                                'PVCCD0_HV_CPU0'])
    brd.db.save('AVC_SRF_vrms.spd')
    """
    
