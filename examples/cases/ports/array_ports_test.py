from thinkpi.operations import speed as spd
from thinkpi.operations import pman as pm


if __name__ == '__main__':
    db1 = spd.Database(r'..\thinkpi_test_db\gnr_x1_pwr_odb_2022_1_19_10_11_prepared_golden.spd')
    db1.load_data()

    pg1 = pm.PortGroup(db1)
    pg2 = pg1.array_copy(-0.6144000e-3, 11.2190000e-3,
                            2.5320000e-3, 8.7870000e-3,
                            1, 1)
    
    pg2.add_ports(save=False)
    pg2.db.prepare_plots('Signal$surface')
    pg2.db.plot('Signal$surface')
    