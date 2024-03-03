from thinkpi.operations import speed as spd
from thinkpi.operations import pman as pm


if __name__ == '__main__':
    
    # Example of multi layer port copy
    
    r"""
    d1 = spd.Database(r'..\thinkpi_test_db\k30643-001_r01_odb_2_ports.spd')
    d1.load_data()
    d2 = spd.Database(r'..\thinkpi_test_db\k30643-001_r01_odb_2.spd')
    d2.load_data()
    """
    
    r'''
    # Example of a rotated auto copy operation
    d1 = spd.Database(r'..\thinkpi_test_db\gnr_x1_pwr_odb_2022_1_19_10_11_prepared_golden.spd')
    d1.load_data()
    d2 = spd.Database(r'..\thinkpi_test_db\gnr_x1_pwr_odb_2022_1_19_10_11_prepared_golden_rot.spd')
    d2.load_data()
    '''

    r'''
    d1 = spd.Database(r'..\thinkpi_test_db\OKS\db\auto_copy_debug\gnr_sp_xcc_cudensity_worst4pd_2022_2_15_VCCD_HV_clean.spd')
    d1.load_data()
    d2 = spd.Database(r'..\thinkpi_test_db\OKS\db\auto_copy_debug\DFE_pkg_VCCD.spd')
    d2.load_data()
    

    pg1 = pm.PortGroup(d1)
    pg2 = pg1.auto_copy(d2)
    pg2.add_ports(save=False)
    pg2.db.prepare_plots('SignalPKG$surface')
    pg2.db.plot('SignalPKG$surface')
    '''

    r'''
    d1 = spd.Database(r'..\thinkpi_test_db\OKS\db\VccD_BRD_Source.spd')
    d1.load_data()
    d2 = spd.Database(r'..\thinkpi_test_db\OKS\db\VccD_BRD_Destination.spd')
    d2.load_data()

    pg1 = pm.PortGroup(d1)
    pg2 = pg1.auto_copy(d2)
    pg2.add_ports(save=True, fname='VccD_BRD_Ports.spd')
    pg2.db.prepare_plots('SignalBRD$TOP')
    pg2.db.plot('SignalBRD$TOP')
    '''
    
    r'''
    # Source
    d1 = spd.Database(r'..\thinkpi_test_db\GNR\gnr_hcc_vccin-vccd-fivra-inf_odb_2023_05_23_18_44_short_removal_FIVRA_INF_manual_PATCH_src.spd')
    d1.load_data()
    # Destination
    d2 = spd.Database(r'..\thinkpi_test_db\GNR\gnr_hcc_vccin-vccd-fivra-inf_odb_2023_05_23_18_44_short_removal_FIVRA_INF_manual_BRD_INT_PATCH_MLI_INFv2_dst.spd')
    d2.load_data()

    pg1 = pm.PortGroup(d1)
    pg2 = pg1.auto_copy(d2)
    pg2.add_ports(save=True, fname=r'..\thinkpi_test_db\GNR\gnr_hcc_vccin-vccd-fivra-inf_odb_2023_05_23_18_44_short_removal_FIVRA_INF_manual_BRD_INT_PATCH_MLI_INFv2_ports.spd')

    pg2.status()
    '''

    r'''
    # Source
    d1 = spd.Database(r'..\thinkpi_test_db\GNR\gnr_sp_xcc_cudensity_worst4pd_2022_2_15_VCCD_HV_src.spd')
    d1.load_data()
    # Destination
    d2 = spd.Database(r'..\thinkpi_test_db\GNR\DFE_pkg_VCCD_dst.spd')
    d2.load_data()

    pg1 = pm.PortGroup(d1)
    pg2 = pg1.auto_copy(d2)
    pg2.add_ports(save=True, fname='DFE_pkg_VCCD_ports.spd')
    pg2.status()
    pg2.db.prepare_plots('SignalPKG$surface')
    pg2.db.plot('SignalPKG$surface')
    '''

    # Source
    d1 = spd.Database(r'..\thinkpi_test_db\CWF\cwf_ap_point_vccd_hv_ddrd_ddra_23ww23p2_VCCD_HV0_PKG&INT.spd')
    d1.load_data()
    # Destination
    d2 = spd.Database(r'..\thinkpi_test_db\CWF\cwf_ap_point_vccd_hv_ddrd_ddra_23ww23p2_ProcMerge.spd')
    d2.load_data()

    pg1 = pm.PortGroup(d1)
    pg2 = pg1.auto_copy(d2)
    pg2.add_ports(save=True, fname=r'..\thinkpi_test_db\CWF\cwf_ap_point_vccd_hv_ddrd_ddra_23ww23p2_ProcMerge_ports.spd')
    pg2.status()
    pg2.db.prepare_plots('Signal$surface_outer')
    pg2.db.plot('Signal$surface_outer')
    
   
    


    