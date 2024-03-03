from thinkpi.flows import tasks
from thinkpi.operations import speed as spd


if __name__ == '__main__':
    r"""
    pkg = tasks.PsiTask(
        r'..\thinkpi_test_db\OKS\Bugs\OKS_12CH_PI_V1_ww19.spd'
    )

    
    pkg.update_stackup(r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\bugs\OKS_12CH_PI_V1_ww19_stackup.csv")
    pkg.create_tcl(r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\bugs\mod_stackup_test.tcl")
    #pkg.run_tcl(r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\bugs\mod_stackup_test.tcl",
    #            r'C:\Cadence\Sigrity2021.1\tools\bin\powersi.exe')
    """

    r'''
    pkg = tasks.PsiTask(
        r'..\thinkpi_test_db\OKS\VCCANA\OKS1_NFF1S_DNOX_PWRsims_ww03_processed.spd'
    )
    pkg.update_stackup(r'..\thinkpi_test_db\OKS\VCCANA\BRD_OKS_STACKUP_22L.csv')
    pkg.create_tcl('BRD_OKS_STACKUP.tcl')
    pkg.run_tcl(r'..\thinkpi_test_db\OKS\VCCANA\BRD_OKS_STACKUP.tcl',
               r'C:\Cadence\Sigrity2021.1\tools\bin\powersi.exe')
    '''

    r'''
    db = spd.Database(r"..\thinkpi_test_db\SRF\srf_ap_zcc_res_ext_2023_01_19_08_49_proc_vload_t_sense_23ww4p2.spd")
    db.load_flags['plots'] = False
    db.load_data()

    pkg = tasks.PsiTask(db)
    pkg.update_stackup(r"..\thinkpi_test_db\SRF\whateverIwant_doe_stackup.csv")
    pkg.create_tcl(r"..\thinkpi_test_db\SRF\stackup_conduct_test.tcl")
    '''

    db = spd.Database(r"..\thinkpi_test_db\OKS\debug\Daniel\target_OKS1_DNO5_bga9280_ww21_G4opt1_misc.spd")
    db.load_flags['plots'] = False
    db.load_data()

    pkg = tasks.PsiTask(db)
    pkg.update_stackup(r"..\thinkpi_test_db\OKS\debug\Daniel\brd_22L_stackup.csv")
    pkg.create_tcl(('PowerSI', 'extraction'),
                   r"..\thinkpi_test_db\OKS\debug\Daniel\stackup.tcl")