import queue

from thinkpi.backend_api import api

que = queue.Queue()

if __name__ == '__main__':
    """
    pg = pm.PortGroup(r'..\thinkpi_test_db\OKS\db\brd_pkg_OKS_12CH.spd')
    port_db = pg.auto_vrm_ports(layer='SignalBRD$TOP',
                                net_name='PVCCIN_CPU0_NORTH')
    """

    ports = api.PortHandler(que)
    response = ports.auto_vrm_ports(r'..\thinkpi_test_db\OKS\M6186002QIR3_doe_processed.spd',
                                    layer='Signal$TOP',
                                    power_nets=['P12V_S3_AUX_CPU0_NVDIMM',
                                                'PVCCINFAON_CPU0', 'PVCCIN_CPU0'],
                                    to_fname=r'..\thinkpi_test_db\OKS\M6186002QIR3_doe_processed_ports.spd')

    
