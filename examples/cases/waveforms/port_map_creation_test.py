from thinkpi.waveforms import measurements as msr

if __name__ == '__main__':
    r'''
    grid = msr.GridCreator(db=r"..\thinkpi_test_db\OKS\DDR\gnr_ucc_mbvr_odb_2021_11_3_17_5_VCCDHV0_v1_dg8_5b_7b_2.spd")
    grid.create_grid(r"..\thinkpi_test_db\OKS\DDR\grid.csv",
                    r"..\thinkpi_test_db\OKS\DDR\map_conv.csv",
                    compress=True)
    '''

    '''
    grid = msr.GridCreator(db=r"..\thinkpi_test_db\GNR\gnr_sp_xcc_cudensity_worst4pd_2022_2_15_VCCD_HV_clean.spd")
    grid.create_grid(r"..\thinkpi_test_db\GNR\grid_gnr_sp_vccd.csv",
                    r"..\thinkpi_test_db\GNR\gnr_sp_vccd_name_conv.csv",
                    compress=True)
    '''
    
    grid = msr.GridCreator(db=r"..\thinkpi_test_db\GNR\GNR-SP-XCC_CuDensity_worst4PD_2022_2_15.spd")
    grid.create_grid(r"..\thinkpi_test_db\GNR\grid_gnr_sp_vccfa_ehv.csv",
                    r"..\thinkpi_test_db\GNR\VccFA_EHV_name_conv.csv")



    
