from thinkpi.flows import tasks
from thinkpi.operations import speed as spd

if __name__ == '__main__':
    db = spd.Database(r'C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\SRF\AVC_FAb4_230109_cpu0_srf_ap_zcc_23_01_17_12_00_Proc_reduced.spd')
    db.load_flags['plots'] = False
    db.load_data()
    
    db = tasks.PdcTask(db)
    db.import_ldo_setup(r'C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\SRF\AVC_FAb4_230109_cpu0_srf_ap_zcc_23_01_17_12_00_Proc_reduced_ldosetup.csv')
    db.db.save()
