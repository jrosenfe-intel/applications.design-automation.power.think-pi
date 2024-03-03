import queue

from thinkpi.backend_api import api

que = queue.Queue()

if __name__ == '__main__':
    ports = api.PortHandler(que)
    response = ports.sinks_vrms_to_ports(
                r'..\thinkpi_test_db\OKS\OKS12CH_PI_PF_V1_B_proc_sinks_vrms.spd',
                'both',
                to_fname=r'..\thinkpi_test_db\OKS\OKS12CH_PI_PF_V1_B_proc_sinks_ports.spd',
                sink_suffix='port', vrm_suffix='port'
        )

    


    