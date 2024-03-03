# ------------- Introduction -------------
'''
In this phase, port map .csv file is created
based on existing ports in the .spd file.
The user should inspect the resulting map and update it if required.
This file is used in the next phase.
'''

# ------------- User defined parameters -------------

# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\GNR\gnr_hcc_vccin-vccd-fivra-inf_odb_2023_05_23_18_44_processed_clarity_ports.spd"

# Outputs
# -------
PORT_MAP_FILE = r'..\thinkpi_test_db\GNR\port_map.csv'

# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks
from thinkpi.waveforms import measurements as msr

if __name__ == '__main__':
    grid = msr.GridCreator(DATABASE_PATH_NAME)
    grid.create_grid(fname=PORT_MAP_FILE)
    
    


    