import queue

from thinkpi.backend_api import api

que = queue.Queue()


if __name__ == '__main__':
    db_process = api.DbApi(r'..\thinkpi_test_db\OKS\dmr-ap_ppf_12ch_vccin_pdslice_ccb-io_north_00504221.spd', que)
    db_process.load_data()
    db_process.preprocess(pwr_nets=['VCCIN_NORTH'],
                        gnd_nets='VSS',
                        stackup_fname=None, padstack_fname=None,
                        material_fname=None, default_conduct=3.4e7,
                        cut_margin=5,
                        processed_fname=r'..\thinkpi_test_db\OKS\dmr-ap_ppf_12ch_vccin_pdslice_ccb-io_north_00504221_proc.spd')
    
    
    
    

    

    