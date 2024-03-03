from thinkpi.flows import tasks

if __name__ == '__main__':
    #brd_pkg = tasks.PdcTask(r'..\thinkpi_test_db\GNR\GNR_UCC_FIVRA_PDC_Rev0_v21.spd')
    #brd_pkg = tasks.PdcTask()
    r"""
    pkg_results = brd_pkg.parse_sim_results(
        r'..\thinkpi_test_db\GNR\pdc_results_test.xml',
        r'..\thinkpi_test_db\GNR\gnr_ucc_cfn_io_odb_2020_10_8_13_36_vccio_1stx_v22_Distribution_Text_Files',
        pwr_net='FIVRA', gnd_net='VSS'
    )
    brd_results = brd_pkg.parse_sim_results(
        r'..\thinkpi_test_db\GNR\pdc_results_test.xml',
        r'..\thinkpi_test_db\GNR\gnr_ucc_cfn_io_odb_2020_10_8_13_36_vccio_1stx_v22_Distribution_Text_Files',
        pwr_net='PVCCFA_EHV_FIVRA_CPU0', gnd_net='GND_1'
    )
    """
    brd_pkg = tasks.PdcTask(r'..\thinkpi_test_db\OKS\db\brd_pkg_OKS_8CH_pr111.spd')
    pkg_results = brd_pkg.parse_sim_results(
        xml_fname=r'..\thinkpi_test_db\OKS\db\brd_pkg_OKS_8CH_pr111_SimulationResult.xml',
        pwr_net='VCCIN_NORTH', gnd_net='VSS',
        dist_path=r'..\thinkpi_test_db\OKS\db\brd_pkg_OKS_8CH_pr111_Distribution_Text_Files',
        report_fname=r'..\thinkpi_test_db\OKS\db\pkg_pdc_report.xlsx'
    )
    brd_results = brd_pkg.parse_sim_results(
        xml_fname=r'..\thinkpi_test_db\OKS\db\brd_pkg_OKS_8CH_pr111_SimulationResult.xml',
        pwr_net='PVCCIN_CPU0_1', gnd_net='GND',
        dist_path=r'..\thinkpi_test_db\OKS\db\brd_pkg_OKS_8CH_pr111_Distribution_Text_Files',
        report_fname=r'..\thinkpi_test_db\OKS\db\brd_pdc_report.xlsx'
    )

    





    