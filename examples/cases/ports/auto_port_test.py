from thinkpi.operations import speed as spd
from thinkpi.operations import pman as pm


if __name__ == '__main__':
    """
    db = spd.Database(r'..\thinkpi_test_db\OKS\db\OKS_12CH_PI_V1_ww19_boxes.spd')
    db.load_data()

    pg1 = pm.PortGroup(db)
    pg2 = pg1.auto_port(layer='Signal$TOP', net_name='PVCCFA_EHV_FIVRA_CPU0',
                        num_ports=5,
                        area=(82e-3, 334.1e-3, 107e-3, 358e-3))
    pg2.add_ports(save=False)

    pg2.db.prepare_plots('Signal$TOP')
    pg2.db.plot('Signal$TOP')
    

    pg3 = pg2.auto_port(layer='Signal$surface', net_name='VCCIN',
                        num_ports=4,
                        area=(-79.7e-3, 6.31e-3, -73.8e-3, 6.65e-3))
    
    pg3.add_ports(save=False)


    pg3.db.prepare_plots('Signal$surface')
    pg3.db.plot('Signal$surface')
    """

    db = spd.Database(r'..\thinkpi_test_db\OKS\db\OKS12CH_PI_PF_V1_B_proc.spd')
    db.load_data()

    pg1 = pm.PortGroup(db)
    pg2 = pg1.auto_port(layer='Signal$TOP', net_name='PVCCIN_CPU0_NORTH',
                        num_ports=50,
                        area=(60.8076e-3, 293.6041e-3, 130.153e-3, 435.0152e-3))
                            # bottom left x,y ; top right x,y ; in m

    pg2.add_ports(save=True,
                fname='OKS12CH_PI_PF_V1_B_proc_autoports.spd',
                )

    pg2.db.prepare_plots('Signal$TOP')
    pg2.db.plot('Signal$TOP')
