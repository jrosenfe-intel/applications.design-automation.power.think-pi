from thinkpi.flows import tasks


if __name__ == '__main__':
    pkg = tasks.PsiTask(
        r'..\Ian\tiu-630-0078_rev0_pvc2t_FINAL_LAYOUT_20200706_in_infaon.spd'
        #r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\db\DMR_PPF_AP_12CH_VCCIN_PDSLICE_CCB_IO_NORTH_proc.spd"
    )
    stackup, padstack = pkg.export_stackup_padstack()
