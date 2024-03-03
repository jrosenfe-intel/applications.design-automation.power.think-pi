from thinkpi.operations import speed as spd
from thinkpi.operations import pman as pm


if __name__ == '__main__':
    db = spd.Database(r'..\thinkpi_test_db\CWF\cwf_ap_point_vccin_23ww52p3_proc_patch_ian_noports.spd')
    db.load_data()

    pg1 = pm.PortGroup(db)
    skt_db = pg1.auto_port_conn(num_ports=40, side='bottom', net_name='VCCIN')
    skt_db.update_ports(r'..\thinkpi_test_db\CWF\cwf_ap_point_vccin_23ww52p3_proc_patch_ian_ports_mli_ports.spd', save=True)
    
    skt_db.db.prepare_plots('Signal$base_inner')
    skt_db.db.plot('Signal$base_inner')


    


    