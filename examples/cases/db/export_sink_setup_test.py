from thinkpi.flows import tasks

if __name__ == '__main__':
    brd = tasks.PdcTask(
        r'..\thinkpi_test_db\DMR\dmr_ap_ucc1_dcm_23ww43p3_v2_proc_cut_POR_LSC_24A_et.spd'
    )
    df = brd.export_sink_setup()
    print(df)
