import queue

from thinkpi.backend_api import api

que = queue.Queue()


if __name__ == '__main__':
    db = api.DbApi(r'..\thinkpi_test_db\OKS\dmr-ap_ppf_12ch_vccin_pdslice_ccb-io_north_00504221.spd', que)
    db.load_data()
    result = db.auto_setup_padstack(
                        fname=r'..\thinkpi_test_db\OKS\padstack_test.csv',
                        db_type='package',
                        brd_plating=None,
                        pkg_gnd_plating=18e-3, pkg_pwr_plating=25e-3,
                        conduct=3.4e7, material=None,
                        innerfill_material=None, outer_thickness=0.1e-3,
                        outer_coating_material=None, unit='mm'
                )
    
    
    
    

    

    