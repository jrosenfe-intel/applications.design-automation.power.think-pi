from thinkpi.operations import speed as spd
from thinkpi.operations import pman as pm


if __name__ == '__main__': 
    r"""
    # Example of boxes to 3D ports
    db = spd.Database(r'..\thinkpi_test_db\DMR\dmr_ap_pwr_vcciose_cfcmem_23ww07p5_odb_process_boxes.spd')
    db.load_data()

    pg1 = pm.PortGroup(db)
    pg2 = pg1.boxes_to_ports(port3D=True)

    pg2.add_ports(save=False)

    pg2.db.prepare_plots('Signal$surface')
    pg2.db.plot('Signal$surface')
    """

    r"""
    db = spd.Database(r'..\thinkpi_test_db\DMR\dmr_ap_ucc1_fivr_cfcmem_cfcio_fixdig_2ia_23ww46p3_odb_fixdig_boxes2.spd')
    db.load_data()

    pg1 = pm.PortGroup(db)
    pg2 = pg1.boxes_to_ports()

    pg2.add_ports(r'..\thinkpi_test_db\DMR\dmr_ap_ucc1_fivr_cfcmem_cfcio_fixdig_2ia_23ww46p3_odb_fixdig_ports2.spd',
                  save=True
                  )

    pg2.db.prepare_plots('Signal$surface')
    pg2.db.plot('Signal$surface')
    """

    db = spd.Database(r'..\thinkpi_test_db\CWF\cwf_ap_point_vccd_hv_ddrd_ddra_23ww23p2_ProcMerge_boxes.spd')
    db.load_data()

    pg1 = pm.PortGroup(db)
    pg2 = pg1.boxes_to_ports()

    pg2.add_ports(r'..\thinkpi_test_db\CWF\cwf_ap_point_vccd_hv_ddrd_ddra_23ww23p2_ProcMerge_boxes_ports.spd',
                  save=True
                  )
    results = pg2.status()
    pg2.db.prepare_plots('Signal$surface_outer')
    pg2.db.plot('Signal$surface_outer')