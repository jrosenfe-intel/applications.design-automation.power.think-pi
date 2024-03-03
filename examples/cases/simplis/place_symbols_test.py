from thinkpi.flows import tasks

if __name__ == '__main__':
    circuits = tasks.Simplis(r'..\thinkpi_test_db\simplis')

    #circuits.import_circuit_map(r'..\thinkpi_test_db\simplis\cir_map.xlsx')
    
    circuits.place_cir()
    circuits.connect_cir(r'..\thinkpi_test_db\simplis\cir_map.xlsx')
    circuits.create_sxscr(r"..\thinkpi_test_db\simplis\main.sxscr",
                          r"..\thinkpi_test_db\simplis\main.sxsch")
    circuits.run_sxscr(r"..\thinkpi_test_db\simplis\main.sxscr")
