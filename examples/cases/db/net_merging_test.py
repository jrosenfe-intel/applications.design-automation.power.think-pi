from thinkpi.operations import speed as spd


if __name__ == '__main__':
    r'''
    db = spd.Database(r"..\thinkpi_test_db\dmr\dmr_ap_pwr_vcciose_cfcmem_23ww07p5_odb_process.spd")

    #db.load_flags['plots'] = False
    db.load_data()

    nets_to_merge = ['VXBR_UCIEOSE_PH0','VXBR_UCIEOSE_PH1']

    a=db.match_nets(nets_to_merge=nets_to_merge)


    a=db.match_nets(r"..\thinkpi_test_db\dmr\dmr_ap_pwr_vcciose_cfcmem_23ww07p5_odb_process_merged.spd",
                    nets_to_merge=nets_to_merge)
    '''

    r'''
    db = spd.Database(r'C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\SRF\AVC_FAb4_230109_cpu0_srf_ap_zcc_23_01_17_12_00_Proc_reduced.spd')
    db.load_flags['plots'] = False
    db.load_data()

    nets_to_merge = 'VXBR*'

    db.merge_nets(r'C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\SRF\AVC_FAb4_230109_cpu0_srf_ap_zcc_23_01_17_12_00_Proc_reduced_merged.spd',
                    nets_to_merge=nets_to_merge)
    '''

    db = spd.Database(r"..\thinkpi_test_db\SRF\srf_ap_zcc_res_ext_2023_01_19_08_49_proc_vload_t_sense_23ww4p2_cut.spd")
    db.load_flags['plots'] = False
    db.load_data()

    nets_to_merge = ['VXBR_CFC_E_*_CDIE09']

    db.merge_nets(r'..\thinkpi_test_db\SRF\srf_ap_zcc_res_ext_2023_01_19_08_49_proc_vload_t_sense_23ww4p2.spd_cut_merged.spd',
                    nets_to_merge=nets_to_merge)
