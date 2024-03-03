from thinkpi.operations import speed as spd
from thinkpi.operations import pman as pm


if __name__ == '__main__':
    d1 = spd.Database(r'..\Albert\SPR_noTFC_VCCIN_clean_reduced_V21.spd')
    d1.load_data()
    d2 = spd.Database(r'..\Albert\spr_sp_xcc_infaon_fix_22ww21p2_odb_INFAON_reduced.spd')
    d2.load_data()

    pg1 = pm.PortGroup(d1)
    
    pg2 = pg1.copy(0, -0.2049e-3, force=False)
    pg2.add_ports(save=False)
    pg2.db.prepare_plots('Signal$surface')
    pg2.db.plot('Signal$surface')

    