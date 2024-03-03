from thinkpi.operations import speed as spd
from thinkpi.flows import tasks

if __name__ == '__main__':

    # Source
    db_src = spd.Database(r'..\thinkpi_test_db\DMR\copy_vrms\dmr_ap_ucc1_fivr_imh_23ww46p3_odb_proc_vrms_cut.spd')
    db_src.load_data()

    # Destination
    db_dst = spd.Database(r'..\thinkpi_test_db\DMR\copy_vrms\dmr_ap_ucc1_fivr_cfcmem_cfcio_fixdig_mio_proc.spd')
    db_dst.load_data()

    db_src = tasks.PdcTask(db_src)
    # db_with_copied_vrms = db_src.auto_copy_vrms(db_dst,
    #                                             dx=113.7569000e-3 - 113.7569000e-3, # x_dst - x_src
    #                                             dy=418.1213000e-3 - 418.1213000e-3, # y_dst - y_src
    #                                             dx_sense=95.4062000e-3 - 95.4062000e-3, # x_dst - x_src
    #                                             dy_sense=349.7255000e-3 - 349.7255000e-3 # y_dst - y_src
    #                                         )

    db_with_copied_vrms = db_src.auto_copy_vrms(db_dst,
                                                dx=-15.9200000e-3 - -25.2078000e-3,  # x_dst - x_src
                                                dy=-9.0302000e-3 - -12.6498000e-3,  # y_dst - y_src)
    )
    if db_with_copied_vrms is not None:
        db_with_copied_vrms.db.save(r'..\thinkpi_test_db\DMR\copy_vrms\dmr_ap_ucc1_fivr_cfcmem_cfcio_fixdig_mio_proc_no_vrms_vrmscopied.spd')
    