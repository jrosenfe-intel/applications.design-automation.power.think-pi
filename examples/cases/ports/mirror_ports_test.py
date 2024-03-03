from thinkpi.operations import speed as spd
from thinkpi.operations import pman as pm


if __name__ == '__main__':
    '''
    db1 = spd.Database(r'..\thinkpi_test_db\gnr_x1_pwr_odb_2022_1_19_10_11_prepared_golden.spd')
    db1.load_data()

    pg1 = pm.PortGroup(db1)
    pg2 = pg1.mirror_copy(-0.6144000e-3, 9.4772000e-3,
                            -0.6144000e-3, 8.9919000e-3)
    
    '''
    d1 = spd.Database(r'..\thinkpi_test_db\OKS\db\auto_copy_debug\gnr_sp_xcc_cudensity_worst4pd_2022_2_15_VCCD_HV_clean_test.spd')
    d1.load_data()

    pg1 = pm.PortGroup(d1)
    pg2 = pg1.mirror_copy(-51.4330000e-3, -6.7927000e-3,
                            -81.1670000e-3, -6.7927000e-3)
    '''

    db1 = spd.Database(r'..\thinkpi_test_db\spr\VCCIN_infaon_fix_mockup_clean_1die.spd')
    db1.load_data()

    pg1 = pm.PortGroup(db1)
    pg2 = pg1.mirror_copy(75.5920000e-3, 100.3857000e-3,
                            75.5920000e-3, 69.4200000e-3)
    '''

    pg2.add_ports(save=False)
    pg2.db.prepare_plots('Signal$surface')
    pg2.db.plot('Signal$surface')

    