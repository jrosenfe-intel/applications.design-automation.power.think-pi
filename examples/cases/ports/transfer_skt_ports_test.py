from thinkpi.operations import speed as spd
from thinkpi.operations import pman as pm


if __name__ == '__main__':
    patch = spd.Database(r'..\thinkpi_test_db\CWF\cwf_ap_point_vccin_23ww52p3_proc_patch_ian_ports.spd')
    patch.load_data()
    inter = spd.Database(r'..\thinkpi_test_db\CWF\cwf_ap_point_vccin_23ww52p3_intclean_noports.spd')
    inter.load_data()

    patch = pm.PortGroup(patch)

    r'''
    # Place ports on board socket
    brd = pm.PortGroup(brd)
    brd = brd.auto_port_conn(num_ports=10, side='top')
    #brd.db.save()
    brd.db.prepare_plots('Signal$TOP')
    brd.db.plot('Signal$TOP')
    '''

    point_ports = patch.transfer_socket_ports(to_db=inter,
                                            from_db_side='bottom',
                                            to_db_side='top',
                                            suffix='MLI_int')
    point_ports.add_ports(save=False)
    point_ports.db.prepare_plots('Signal$surface_inner')
    point_ports.db.plot('Signal$surface_inner')
