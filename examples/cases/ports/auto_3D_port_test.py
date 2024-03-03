from thinkpi.operations import speed as spd
from thinkpi.operations import pman as pm


if __name__ == '__main__':

    
    db = spd.Database(r'..\thinkpi_test_db\k30643-001_r01_odb_2.spd')
    db.load_data()

    pg1 = pm.PortGroup(db)
    pg2 = pg1.auto_port('Signal$surface', 'VCCDDRD_CORE', 30,
                        (-2.2249e-3, -1.8066e-3, 2.7075e-3, 1.8758e-3),
                        port3D=True)
    
    '''
    db = spd.Database(r'..\derrick\gnr_x1_pwr_odb_2022_1_19_10_11_prepared.spd')
    db.load_data()

    pg1 = pm.PortGroup(db)
    pg2 = pg1.auto_port('Signal$surface', 'VCCCORE_C8R7_CDIE09', 30,
                        (-0.3843e-3, 9.2576e-3, 1.4195e-3, 12.2406e-3),
                        port3D=True)
    '''
    
    pg2.add_ports(save=False)
    pg2.db.prepare_plots('Signal$surface')
    pg2.db.plot('Signal$surface')