from thinkpi.operations import speed as spd


if __name__ == '__main__':
    #db = spd.Database(r"..\thinkpi_test_db\OKS\db\brd_pkg_OKS_12CH_debug.spd")
    #db = spd.Database(r"..\thinkpi_test_db\OKS\db\dmr_ap_23ww3p6_odb_OKS1_NFF1S_DNOX_PWRsims_ww3.spd")
    
    db = spd.Database(r"..\thinkpi_test_db\OKS\db\gnr_brd_pkg_merge_pr131.spd")
    db.load_flags['plots'] = False
    db.load_data()
    db.find_pwr_gnd_shorts()

    

    