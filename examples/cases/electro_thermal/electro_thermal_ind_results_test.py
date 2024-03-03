from thinkpi.flows import tasks

if __name__ == '__main__':
    et = tasks.PackageInductorElectroThermalTask(r'..\thinkpi_test_db\thermal\et_core_vrm_sink_thermal.spd')
    r = et.parse_sim_results(xml_fname=r'..\thinkpi_test_db\thermal\et_core_vrm_sink_thermal_SimulationResult.xml',
                         pwr_net='VCCCORE_C7R5_CDIE09', gnd_net='VSS',
                         report_fname=r'..\thinkpi_test_db\thermal\result_summary.xlsx')

    





    