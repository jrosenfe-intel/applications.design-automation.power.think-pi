from thinkpi.flows import tasks


if __name__ == '__main__':
    pkg = tasks.ClarityTask(
        r'..\Ian\tiu-630-0078_rev0_pvc2t_FINAL_LAYOUT_20200706_in_infaon.spd'
    )
    pkg.select_nets(['HDDPS_11_HC0', 'HVDPS_5_HV1'], 'GND')
    pkg.preprocess(
        stackup_fname=r"..\Ian\stackup.csv",
        padstack_fname=r"..\Ian\tiu-630-0078_rev0_pvc2t_FINAL_LAYOUT_20200706_in_infaon_padstack.csv",
        cut_margin=0,
        db_fname=r"tiu-630-0078_rev0_pvc2t_FINAL_LAYOUT_20200706_in_infaon_CLEAN.spd",
        delete_below_layer='Plane$L06_GND'
    )

    pkg.delete_metatl()
    pkg.setup_clarity_sim(sim_temp=100)
    pkg.create_tcl(r"clarity_preprocess_test.tcl")

    