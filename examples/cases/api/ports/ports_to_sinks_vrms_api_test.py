import queue

from thinkpi.backend_api import api

que = queue.Queue()

if __name__ == '__main__':
    sinks_vrms = api.PortHandler(que)
    response = sinks_vrms.ports_to_vrms_sinks(r'..\thinkpi_test_db\SPR\SPR_noTFC_VCCIN_clean_reduced_V21.spd',
                                            r'..\thinkpi_test_db\SPR\SPR_noTFC_VCCIN_clean_reduced_V21_sinks_vrms.spd',
                                            vrm_suffix='vrm', sink_suffix='sink')



    
