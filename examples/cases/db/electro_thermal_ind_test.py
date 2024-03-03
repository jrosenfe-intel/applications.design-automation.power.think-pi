from thinkpi.flows import tasks

if __name__ == '__main__':
    # Single FIVR example
    r"""
    et = tasks.PackageInductorElectroThermalTask(r'..\thinkpi_test_db\GNR\gnr_x1_core_ET.spd')
    et.place_sinks(pwr_net='VCCCORE_C5R2_CDIE09', num_sinks=6)
    et.place_vrms()
    et.db.save(r'et_core_vrm_sink.spd')
    """

    # Multiple FIVRs example
    et = tasks.PackageInductorElectroThermalTask(r'..\thinkpi_test_db\GNR\gnr_x1_master_m63954-001_03_22_2022_6cores.spd')
    et.place_sinks(pwr_net='VCCCORE*', num_sinks=6, area=None)
    et.place_vrms(vrm_phases='VXBR_CORE*')
    et.db.save(r'et_core_vrm_sink.spd')

    et.export_sink_setup()
    et.export_vrm_setup()

    





    