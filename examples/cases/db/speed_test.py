from thinkpi.operations import speed as spd


if __name__ == '__main__':
    #db = spd.Database(r'..\thinkpi_test_db\M4158801B_0p616g_120121_6GND172_cut_V21.spd')
    #db = spd.Database(r'..\thinkpi_test_db\gnr_x1_pwr_odb_2022_1_19_10_11_prepared_golden.spd')
    #db = spd.Database(r'..\thinkpi_test_db\gnr_x1_pwr_odb_2022_1_19_10_11_prepared_v1_3D_golden.spd')
    #db = spd.Database(r'..\thinkpi_test_db\gnr_x1_pwr_odb_2022_1_19_10_11_prepared_golden_rot.spd')
    ##db = spd.Database(r'..\Daniel\k30643-001_r01_odb_2.spd')
    #db = spd.Database(r'..\Albert\SPR_noTFC_VCCIN_clean.spd')
    #db = spd.Database(r'..\Albert\spr_sp_xcc_infaon_fix_22ww21p2_odb_INFAON_reduced.spd')
    #db = spd.Database(r'..\Ian\tiu-630-0078_rev0_pvc2t_FINAL_LAYOUT_20200706_in_infaon.spd')
    #db = spd.Database(r'..\thinkpi_test_db\Donahue\brd_DPS_pk187_080421.spd')
    #db = spd.Database(r'..\thinkpi_test_db\Donahue\don_brd_pkg.spd')
    #db = spd.Database(r'..\thinkpi_test_db\OKS\Bugs\OKS_12CH_PI_V1_ww19.spd')
    #db = spd.Database(r'..\thinkpi_test_db\GNR\GNR_UCC_FIVRA_PDC_Rev0_v21.spd')
    #db = spd.Database(r'..\thinkpi_test_db\OKS\db\dmr_ap_pwr_vcciose_cfcmem_23ww07p5_odb.spd')
    
    #db = spd.Database(r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\db\OKS_12CH_PI_V1_ww19_boxes.spd")
    
    #db = spd.Database(r'..\thinkpi_test_db\DNH\brd_DPS_pk187_080421.spd')
    db = spd.Database(r"D:\jrosenfe\ThinkPI\spd_files\DFE_pkg_VCCD_dst.spd")
    #db.load_flags['plots'] = False
    db.load_data()
    #db.plot('SignalPKG$surface')
    

    