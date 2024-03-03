import queue

from thinkpi.backend_api import api

que = queue.Queue()

if __name__ == '__main__':
    ports = api.PortHandler(que)
    response = ports.array_copy(r'..\thinkpi_test_db\GNR\gnr_x1_pwr_odb_2022_1_19_10_11_prepared_golden.spd',
                                -0.6144000e-3, 11.2190000e-3,
                                2.5320000e-3, 8.7870000e-3,
                                1, 1)

    