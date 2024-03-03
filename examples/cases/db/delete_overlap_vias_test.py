from thinkpi.operations import speed as spd


if __name__ == '__main__':
    #db = spd.Database(r'..\thinkpi_test_db\OKS\db\dmr_ap_pwr_vcciose_cfcmem_23ww07p5_odb.spd')
    #db = spd.Database(r'..\thinkpi_test_db\SRF\srf_ap_zcc_res_ext_2023_01_19_08_49_proc_vload_t_sense_23ww4p2.spd')
    #db = spd.Database(r'..\thinkpi_test_db\GNR\gnr_ucc_b0_dd_odb_2022_12_09_11_03_new.spd')
    db = spd.Database(r'..\thinkpi_test_db\CWF\cwf_sp.spd')
    db.load_flags['plots'] = False
    db.load_data()

    db.delete_overlap_vias(save=False)
    

    