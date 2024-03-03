from thinkpi.flows import tasks
from thinkpi.operations import speed as spd

if __name__ == '__main__':
    r'''
    pkg = tasks.PsiTask(
        r'..\Ian\tiu-630-0078_rev0_pvc2t_FINAL_LAYOUT_20200706_in_infaon.spd'
    )
    
    pkg.update_padstack(r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\Ian\tiu-630-0078_rev0_pvc2t_FINAL_LAYOUT_20200706_in_infaon_padstack.csv"),
    pkg.create_tcl(r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\Ian\daniel_padstack_test.tcl")
    pkg.run_tcl(r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\Ian\daniel_padstack_test.tcl",
                r'C:\Cadence\Sigrity2021.1\tools\bin\powersi.exe')

    '''
    
    r'''
    db = spd.Database(r"..\thinkpi_test_db\SRF\srf_ap_zcc_res_ext_2023_01_19_08_49_proc_vload_t_sense_23ww4p2.spd")
    db.load_flags['plots'] = False
    db.load_data()

    pkg = tasks.PsiTask(db)
    pkg.update_padstack(r"..\thinkpi_test_db\SRF\paddystacky_doe_padstack.csv")
    pkg.create_tcl(r"..\thinkpi_test_db\SRF\padstack_conduct_test.tcl")
    '''

    db = spd.Database(r"..\thinkpi_test_db\OKS\OKS1_DNO5_bga9280_ww21_G4opt1_misc.spd")
    db.load_flags['plots'] = False
    db.load_data()

    pkg = tasks.PsiTask(db)
    pkg.update_padstack(r"..\thinkpi_test_db\OKS\brd_22L_padstack2.csv")
    pkg.create_tcl(('PowerSI', 'extraction'),
                   r"OKSOKS1_DNO5_bga9280_ww21_G4opt1_misc_padstack.tcl")
    pkg.run_tcl(r"OKSOKS1_DNO5_bga9280_ww21_G4opt1_misc_padstack.tcl",
               pkg.exec_paths['sigrity'][0])
    

    