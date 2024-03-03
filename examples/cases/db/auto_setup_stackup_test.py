from thinkpi.flows import tasks


if __name__ == '__main__':

    r'''
    # Board stackup
    brd = tasks.PsiTask(
        r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\IM4158801B_0p616g_120121_6GND172_VCCD_HV0_CPU0.spd"
    )
    brd.auto_setup_stackup(r"C:..\thinkpi_test_db\IM4158801B_stackup.csv",
                            dielec_thickness=127e-6,
                            metal_thickness=100e-6,
                            conduct=3.4e7)
    brd.create_tcl(r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\IM4158801B_padstack.tcl")
    r'''

    # Package stackup
    pkg = tasks.PsiTask(
        r'..\thinkpi_test_db\GNR\gnr_ucc_cfn.spd'
    )
    pkg.auto_setup_stackup(fname=r'..\thinkpi_test_db\GNR\cfn_stackup.csv',
                            dielec_thickness=2.5e-5,
                            metal_thickness=None,
                            core_thickness=3.5e-5,
                            conduct=None, dielec_material=None,
                            metal_material='Copper', core_material='PB',
                            fillin_dielec_material='FR-4')
    pkg.create_tcl(r'cfn.tcl')

    #pkg.run_tcl(r'cfn.tcl')
    
