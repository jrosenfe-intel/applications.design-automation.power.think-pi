import queue

from thinkpi.backend_api import api

que = queue.Queue()


if __name__ == '__main__':
    
    #db_api = api.DbApi(r'..\thinkpi_test_db\DNH\brd_DPS_pk187_080421.spd', que)
    db_api = api.DbApi(r'..\thinkpi_test_db\OKS\dmr-ap_ppf_12ch_vccin_pdslice_ccb-io_north_00504221.spd', que)
    response = db_api.load_data()
    

    r'''
    dapi = api.DbApi()
    m = dapi.get_material(r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\ACI_Materials_WW5'22.txt")
    '''

    r'''
    dapi = api.DbApi()
    dapi.save_material(r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\test_material.txt",
                        m)
    '''

    r'''
    db_api = api.DbApi(r'..\lib_manager\OKS\db\package\GNR_UCC_FIVRA_PDC_Rev0_v21.spd', que)
    a = db_api.load_data()
    response = db_api.get_stackup()
    '''
    

    