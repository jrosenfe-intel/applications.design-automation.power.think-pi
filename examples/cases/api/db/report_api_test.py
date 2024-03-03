import queue

from thinkpi.backend_api import api

que = queue.Queue()


if __name__ == '__main__':
    r'''
    db_api = api.DbApi(r'..\thinkpi_test_db\OKS\dmr-ap_ppf_12ch_vccin_pdslice_ccb-io_north_00504221.spd', que)
    '''

    db_api = api.DbApi(r'..\spd_files\brd_pkg_OKS_12CH.spd')
    db_api.load_data()
    response = db_api.report(['VCCIN_NORTH_1'], cap_finder='*C*')
    
    

    