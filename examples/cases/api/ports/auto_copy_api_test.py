import queue

from thinkpi.backend_api import api

que = queue.Queue()

if __name__ == '__main__':
    ports = api.PortHandler(que)
    auto_copy_reponse = ports.auto_copy(
                                src_db=r'..\thinkpi_test_db\GNR\gnr_sp_xcc_cudensity_worst4pd_2022_2_15_VCCD_HV_src.spd',
                                dst_db=r'..\thinkpi_test_db\GNR\DFE_pkg_VCCD_dst.spd',
                                force=False
                        )

    
    
    

    

    