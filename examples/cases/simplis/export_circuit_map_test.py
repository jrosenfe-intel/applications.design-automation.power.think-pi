from thinkpi.flows import tasks

if __name__ == '__main__':
    circuits = tasks.Simplis(r'..\thinkpi_test_db\simplis')
    circuits.export_circuit_map(r'..\thinkpi_test_db\simplis\cir_map2.xlsx')
    