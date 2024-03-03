from thinkpi.operations import speed as spd
from thinkpi.operations import pman as pm


if __name__ == '__main__':
    db1 = spd.Database(r'..\thinkpi_test_db\gnr_x1_pwr_odb_2022_1_19_10_11_prepared_golden.spd')
    db1.load_data()
    db2 = spd.Database(r'..\thinkpi_test_db\gnr_x1_pwr_odb_2022_1_19_10_11_prepared_golden_rot.spd')
    db2.load_data()

    pg1 = pm.PortGroup(db1)
    pg2 = pg1.rotate_copy(-10.1010000e-3, 10.6253000e-3,
                            -6.3747000e-3, -76.6990000e-3, -90,
                            db2)
    
    pg2.add_ports(save=False)
    pg2.db.prepare_plots('Signal$surface')
    pg2.db.plot('Signal$surface')
    