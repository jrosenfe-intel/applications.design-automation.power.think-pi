from thinkpi.flows import tasks

if __name__ == '__main__':
    brd_pkg = tasks.PdcTask(r'..\thinkpi_test_db\tnr\brd_pkg_tnr.spd')
    brd_pkg.db.find_pwr_gnd_shorts()
    brd_pkg.place_vrms(layer='SignalBRD$TOP', net_name='PVNN')
    brd_pkg.place_sinks(layer='SignalPKG$surface',
                        net_name='VNN_NAC', num_sinks=13)
    brd_pkg.db.save(r'brd_pkg_tnr_vrm_sink.spd')

    brd_pkg.export_sink_setup()
    brd_pkg.export_vrm_setup()

    





    