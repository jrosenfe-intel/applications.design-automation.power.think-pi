import queue

from thinkpi.backend_api import api

que = queue.Queue()

if __name__ == '__main__':
    sinks_vrms= api.PortHandler(que)
    response = sinks_vrms.get_sinks_vrms_info(r'..\thinkpi_test_db\DNH\sink_test.spd')

