from thinkpi.flows import tasks

if __name__ == '__main__':
    """
    pkg = tasks.PdcTask(
        r'..\thinkpi_test_db\Donahue\pkg_dhv_dc_resistance_odbpp.spd'
    )
    pkg_ports = pkg.place_sinks(layer='Signal$surface',
                        net_name='VCCDDRD_PHY', num_sinks=10)
    pkg.db.save('sink_test.spd')
    """

    db = tasks.PdcTask(
        r'..\thinkpi_test_db\OKS\db\brd_pkg_OKS_12CH.spd'
    )
    port_db = db.place_sinks(layer='SignalPKG$surface',
                    net_name='VCCIN_NORTH_1', num_sinks=13)
    

