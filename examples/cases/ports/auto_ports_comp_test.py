from thinkpi.operations import speed as spd
from thinkpi.operations import pman as pm


if __name__ == '__main__':
    r"""
    db = spd.Database(r'..\thinkpi_test_db\DMR\DMR_PPF_AP_12CH_VCCIN_PDSLICE_CCB_IO_NORTH_proc.spd')
    db.load_data()
    pg1 = pm.PortGroup(db)
    pg2 = pg1.auto_port_comp(layer='Signal$surface',
                            net_name='VCCIN_NORTH_1',
                            comp_find='C*')
    #pg2.add_ports(save=True, fname='DMR_PPF_SP_8CH_VCCIN_PDSLICE_CCB_IO_NORTH_Ports2.spd')
    pg2.add_ports(save=False)
    pg2.db.prepare_plots('Signal$surface')
    pg2.db.plot('Signal$surface')

    
    pg3 = pg2.reduce_ports(layer='Signal$surface', num_ports=285)
    #pg3.add_ports(save=True,
    #            fname='DMR_PPF_SP_8CH_VCCIN_PDSLICE_CCB_IO_NORTH_reduced.spd',
    #            )
    if pg3 is not None:
        pg3.add_ports(save=False)
        pg3.db.prepare_plots('Signal$surface')
        pg3.db.plot('Signal$surface')
        print(pg3.group_info)
    

    db = spd.Database(r'C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\db\OKS8CH_PI_PF_V1_B_proc.spd')
    db.load_data()
    pg1 = pm.PortGroup(db)

    pg2 = pg1.auto_port_comp(layer='Signal$TOP',
                            net_name='PVCCIN_CPU0_1',
                            comp_find='C*')
    #pg2.add_ports(save=True,fname='OKS8CH_PI_PF_V1_B_proc_comp_ports.spd')
    pg2.add_ports(save=False)
    
    pg3 = pg2.auto_port_comp(layer='Signal$BOTTOM',
                            net_name='PVCCIN_CPU0_1',
                            comp_find='C*')
    #pg3.add_ports(save=True,fname='OKS8CH_PI_PF_V1_B_proc_comp_ports.spd')
    pg3.add_ports(save=False)
    
    
    pg4 = pg3.reduce_ports('Signal$BOTTOM', 15,'C*')
    pg4.add_ports(save=True,
                    fname='DMR_PPF_SP_8CH_VCCIN_PDSLICE_CCB_IO_NORTH_reduced.spd',
                )
    """

    db = spd.Database(r'..\thinkpi_test_db\CWF\cwf_ap_point_vccin_23ww52p3_intclean_ports_update_nocap_ports.spd')
    db.load_flags['plots']=False
    db.load_data()

    pg1 = pm.PortGroup(db)
    pg2 = pg1.auto_port_comp(layer='Signal$surface_inner',
                            net_name='VCCIN_1',
                            comp_find='C*')
    pg2.add_ports(save=False)
    
    pg3 = pg2.auto_port_comp(layer='Signal$base_outer',
                            net_name='VCCIN_1',
                            comp_find='C*')
    pg3.add_ports(save=True,fname=r'..\thinkpi_test_db\CWF\cwf_ap_point_vccin_23ww52p3_intclean_ports_update_nocap_ports_addcap.spd')
    
    pg4 = pg3.reduce_ports(layer='Signal$surface_inner', num_ports=7, select_ports='C*')
    pg4.add_ports(save=False)
    
    pg5 = pg4.reduce_ports(layer='Signal$base_outer', num_ports=50, select_ports='C*')    
    pg5.add_ports(save=True,
                fname=r'..\thinkpi_test_db\CWF\cwf_ap_point_vccin_23ww52p3_intclean_ports_update_nocap_ports_addcap_reduce.spd',
                )
    
    pg4.db.prepare_plots('Signal$surface_inner')
    pg4.db.plot('Signal$surface_inner')




    
    
    


    