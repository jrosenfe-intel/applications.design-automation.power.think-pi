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
    
    db_with_copied_sinks = db_src.auto_copy_sinks(db_dst,
                                                  dx=108.6762000e-3 - 108.6762000e-3, # x_dst - x_src
                                                  dy=390.0653000e-3 - 390.0653000e-3 # y_dst - y_src
                                                )


    db_with_copied_vrms_sinks = db_src.auto_copy_vrms(db_with_copied_sinks.db,
                                                        dx=113.7569000e-3 - 113.7569000e-3, # x_dst - x_src
                                                        dy=418.1213000e-3 - 418.1213000e-3, # y_dst - y_src
                                                        dx_sense=95.4062000e-3 - 95.4062000e-3, # x_dst - x_src
                                                        dy_sense=349.7255000e-3 - 349.7255000e-3 # y_dst - y_src
                                                    )
    
    if db_with_copied_sinks is not None or db_with_copied_vrms_sinks is not None:
      db_with_copied_vrms_sinks.db.save(r'..\thinkpi_test_db\OKS\db\OKS12CH_PI_PF_V1_B_proc_no_sinks_vrms_now_with.spd')


    
