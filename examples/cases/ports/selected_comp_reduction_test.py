from thinkpi.operations import speed as spd
from thinkpi.operations import pman as pm


if __name__ == '__main__':
    db = spd.Database(r'..\thinkpi_test_db\DMR\DMR_PPF_AP_12CH_VCCIN_PDSLICE_CCB_IO_NORTH_proc.spd')
    db.load_data()

    # Place ports on the cores
    pg1 = pm.PortGroup(db)
    pg2 = pg1.auto_port('Signal$surface', 'VCCIN_NORTH', 60,
                        (-28e-3, 27e-3, 28e-3, 44e-3))
    pg2.add_ports(save=False)
    pg2.db.prepare_plots('Signal$surface')
    pg2.db.plot('Signal$surface')

    # Place ports on the caps
    pg3 = pg2.auto_port_comp('Signal$surface', 'VCCIN_NORTH', 'C*')
    pg3.add_ports(save=False)
    pg3.db.prepare_plots('Signal$surface')
    pg3.db.plot('Signal$surface')

    # Reduce caps ports only
    pg4 = pg3.reduce_ports(85, 'C*')
    pg4.add_ports(save=True,
                fname='DMR_PPF_SP_8CH_VCCIN_PDSLICE_CCB_IO_NORTH_reduced.spd',
                )
    #pg3.add_ports(save=False)
    pg4.db.prepare_plots('Signal$surface')
    pg4.db.plot('Signal$surface')
    #print(pg4.group_info)
    


    