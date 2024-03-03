from thinkpi.flows import tasks

if __name__ == '__main__':
    """
    # Phase 1
    et = tasks.PackageInductorElectroThermalTask(r'..\thinkpi_test_db\GNR\et_core_vrm_sink_thermal.spd')
    et.et_setup_phase1()
    et.create_tcl('et_phase1.tcl')
    et.run_tcl('et_phase1.tcl',
                r"C:\Cadence\Sigrity2021.1\tools\bin\PowerSI.exe")
    """            

    # Phase 2
    # Reloading the database is required for further setup
    et = tasks.PackageInductorElectroThermalTask(r'..\thinkpi_test_db\GNR\et_core_vrm_sink_thermal.spd')
    et.et_setup_phase2(ind_rail='VCCCORE_C7R5_CDIE09')
    et.create_tcl('et_phase2.tcl')
    et.run_tcl('et_phase2.tcl', et.exec_paths['sigrity'][0])
    

    

    





    