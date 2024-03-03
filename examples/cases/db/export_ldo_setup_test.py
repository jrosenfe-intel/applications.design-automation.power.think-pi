from thinkpi.flows import tasks
from thinkpi.operations import speed as spd

if __name__ == '__main__':
    db = spd.Database(r"D:\jrosenfe\thinkpi_env\thinkpi_test_db\dmr_ap_ucc1_dcm_23ww43p3_v2_proc_cut_POR_LSC_24A_et.spd")
    db.load_flags['plots'] = False
    db.load_data()
    
    db = tasks.PdcTask(db)
    db.export_ldo_setup()
