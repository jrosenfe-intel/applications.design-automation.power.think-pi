from thinkpi.flows import tasks

if __name__ == '__main__':
    
    """
    pkg_ind = tasks.ClarityTask(r'..\thinkpi_test_db\GNR\gnr_ucc_cfn_no_sw.spd')
    pkg_ind.place_ports(pwr_net='VCCIO_FLEX3', num_ports=31)
    pkg_ind.db.prepare_plots('Signal$surface')
    pkg_ind.db.plot('Signal$surface')
    """

    """
    pkg_ind = tasks.ClarityTask(r'..\thinkpi_test_db\GNR\gnr_x1_master_m63954-001_03_22_2022_core.spd')
    pkg_ind.place_ports(pwr_net='VCCCORE_C7R6_CDIE09', num_ports=45)
    pkg_ind.db.save('gnr_x1_master_m63954-001_03_22_2022_core_ports.spd')
    pkg_ind.db.prepare_plots('Signal$surface')
    pkg_ind.db.plot('Signal$surface')
    """

    pkg_ind = tasks.ClarityTask(r'..\thinkpi_test_db\spr\spr-mcc_k42410-001_cfc-cfn-io_2020_10_30_22_48_cfc_ios_cfns_thinkPI_process.spd')
    pkg_ind.place_ports(pwr_net='VCCCFNHCB', num_ports=20)
    pkg_ind.db.save('spr-mcc_k42410-001_cfc-cfn-io_2020_10_30_22_48_cfc_ios_cfns_thinkPI_process_ports.spd')
    pkg_ind.db.prepare_plots('Signal$surface_outer')
    pkg_ind.db.plot('Signal$surface_outer')

    pkg_ind.db.match_nets(nets_to_merge='VXBR_VCCCFNHCB*',
                            fname=r'..\thinkpi_test_db\spr\match_nets.csv')
    """
    pkg_ind.setup_clarity_sim()
    pkg_ind.create_tcl('clarity_test.tcl')
    """
