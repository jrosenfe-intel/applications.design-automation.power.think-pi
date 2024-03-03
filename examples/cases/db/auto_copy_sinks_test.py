from thinkpi.operations import speed as spd
from thinkpi.flows import tasks

if __name__ == '__main__':

    # Source
    db_src = spd.Database(r'..\thinkpi_test_db\OKS\db\OKS12CH_PI_PF_V1_B_proc_sinks_vrms.spd')
    db_src.load_data()

    # Destination
    db_dst = spd.Database(r'..\thinkpi_test_db\OKS\db\OKS12CH_PI_PF_V1_B_proc_no_sinks_vrms.spd')
    db_dst.load_data()

    db_src = tasks.PdcTask(db_src)
    db_with_copied_sinks = db_src.auto_copy_sinks(db_dst)
    db_with_copied_sinks.db.save(r'..\thinkpi_test_db\OKS\db\OKS12CH_PI_PF_V1_B_proc_no_sinks_vrms_now_with.spd')
    


    