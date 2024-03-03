from thinkpi.flows import tasks


if __name__ == '__main__':
    brd = tasks.PdcTask(
        r'..\thinkpi_test_db\Donahue\brd_DPS_pk187_080421.spd'
    )
    pkg = tasks.PdcTask(
        r'..\thinkpi_test_db\Donahue\pkg_dhv_dc_resistance_odbpp.spd'
    )
    """
    brd = tasks.PdcTask(
        r'..\thinkpi_test_db\OKS\db\M6186002QIR3_doe_proc_pr123.spd'
    )
    pkg = tasks.PdcTask(
        r'..\thinkpi_test_db\OKS\db\gnr-sp-xcc_vccio-flex0_rev08_2022_1_20_proc_pr122.spd'
    )
    """
    brd.merge(pkg, pin_res=1e-3, merged_db_name='brd_pkg_oks.spd')
    brd.create_tcl(('PowerDC', 'IRDropAnalysis'))

    