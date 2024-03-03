from thinkpi.operations import speed as spd


if __name__ == '__main__':
    #db = spd.Database(r'..\thinkpi_test_db\k30643-001_r01_odb_2_ports.spd')
    #db = spd.Database(r'..\thinkpi_test_db\OKS\db\OOKS1_NFF1S_DNOX_PWRsims_ww50e_VCCIN_cred_skt_vr.spd')
    
    db = spd.Database(r'..\spd_files\spr_orig1.spd')
    db.load_data()

    # Specify the rails for which the report is generated
    #report_data = db.report(['VCCDDRD_CORE', 'VCCDDQ_DRAM', 'VSS'])
    report_data = db.report(nets='VCCCFC',
                            report_fname=r'..\spd_files\spr_orig1_report.txt')



    
    
