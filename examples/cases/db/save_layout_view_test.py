from thinkpi.flows import tasks

if __name__ == '__main__':
    brd_pkg = tasks.PdcTask(r'..\thinkpi_test_db\GNR\GNR_UCC_FIVRA_PDC_Rev0_v21.spd')

    brd_pkg.save_layout_views(zoom=False)
    brd_pkg.create_tcl(('PowerDC', 'IRDropAnalysis'))
    brd_pkg.run_tcl()


    





    