from thinkpi.flows import tasks


if __name__ == '__main__':
    brd_pkg = tasks.PdcTask(r'..\thinkpi_test_db\tnr\brd_pkg_tnr.spd')
    
    brd_pkg.import_sink_setup(r'..\thinkpi_test_db\tnr\brd_pkg_tnr_sinksetup.xlsx')
    brd_pkg.import_vrm_setup(r'..\thinkpi_test_db\tnr\brd_pkg_tnr_vrmsetup.xlsx')
    brd_pkg.db.save()
    
    brd_pkg.pdc_setup(sim_temp=100)
    brd_pkg.create_tcl(('PowerDC', 'IRDropAnalysis'))





    