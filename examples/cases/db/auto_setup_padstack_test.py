from thinkpi.flows import tasks


if __name__ == '__main__':

    # Board padstack
    r"""
    brd = tasks.PsiTask(
        r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\IM4158801B_0p616g_120121_6GND172_VCCD_HV0_CPU0.spd"
    )
    brd.auto_setup_padstack(r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\IM4158801B_padstack.csv",
                            'board')
    brd.create_tcl(r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\IM4158801B_padstack.tcl")
    """

    # Package padstack
    pkg = tasks.PsiTask(
        r'..\thinkpi_test_db\GNR\gnr_ucc_cfn.spd'
    )
    pkg.auto_setup_padstack(fname=r'..\thinkpi_test_db\GNR\cfn_padstack.csv',
                            db_type='package',
                            material='cot_mat',
                            innerfill_material=None,
                            outer_thickness=1e-6,
                            outer_coating_material='PB')
    pkg.create_tcl(r'cfn.tcl')

    #pkg.run_tcl(r'cfn.tcl')
    
