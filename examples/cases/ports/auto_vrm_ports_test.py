from thinkpi.operations import pman as pm

if __name__ == '__main__':
    """
    pg = pm.PortGroup(r'..\thinkpi_test_db\OKS\db\brd_pkg_OKS_12CH.spd')
    port_db = pg.auto_vrm_ports(layer='SignalBRD$TOP',
                                net_name='PVCCIN_CPU0_NORTH')
    """

    pg = pm.PortGroup(r'..\thinkpi_test_db\OKS\db\M6186002QIR3_doe_processed.spd')
    port_db = pg.auto_vrm_ports(layer='Signal$TOP',
                                net_name='PVCCIN_CPU0')
    port_db.add_ports(save=False)
    port_db.db.prepare_plots('Signal$TOP')
    port_db.db.plot('Signal$TOP')
    

