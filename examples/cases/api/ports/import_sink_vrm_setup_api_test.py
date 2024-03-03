import queue

from thinkpi.backend_api import api

que = queue.Queue()

if __name__ == '__main__':
    sinks_vrms= api.PortHandler(que)
    sinks_vrms.modify_sink_info(r'..\thinkpi_test_db\DNH\sink_test.spd',
                                {'Name': ['SINK_VCCDDRD_PHY_9',
                                            'SINK_VCCDDRD_PHY_8',
                                            'SINK_VCCDDRD_PHY_7',
                                            'SINK_VCCDDRD_PHY_6',
                                            'SINK_VCCDDRD_PHY_5',
                                            'SINK_VCCDDRD_PHY_4',
                                            'SINK_VCCDDRD_PHY_3',
                                            'SINK_VCCDDRD_PHY_2',
                                            'SINK_VCCDDRD_PHY_1',
                                            'SINK_VCCDDRD_PHY_0'],
                                'Nominal Voltage [V]': ['0.95', '0.95', '0.95', '0.95', '0', '0', '0.95', '0', '0', '0'],
                                'Current [A]': ['0.35', '0', '0', '0.35', '0', '0', '0', '0.35', '0', '0'],
                                'Model': ['2', '2', '2', '2', '2', '2', '2', '2', '2', '2']})

