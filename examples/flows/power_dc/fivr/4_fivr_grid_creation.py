# ------------- Introduction -------------
'''
In this phase, sink map .csv file is created
based on existing sinks in the .spd file.
The user should inspect the resulting map and update it if required.
This file is used in the next phase.
'''

# ------------- User defined parameters -------------

# Inputs
# ------
DATABASE_NAME = r'..\thinkpi_test_db\GNR\gnr_hcc_fullstack_pwr_100_2023_08_25_16_26_processed_vxbr_merge.spd'

# Outputs
# -------
SINK_MAP_FILE = r'..\thinkpi_test_db\GNR\sink_map.csv'

# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks
from thinkpi.operations import speed as spd
from thinkpi.waveforms import measurements as msr

if __name__ == '__main__':
    db = spd.Database(DATABASE_NAME)
    #db.load_flags['plots'] = False
    db.load_flags = {'layers': False,
                    'nets': False,
                    'nodes': True,
                    'ports': False,
                    'shapes': False,
                    'padstacks': False,
                    'vias': False,
                    'components': False,
                    'traces': False,
                    'sinks': True,
                    'vrms': False,
                    'plots': False
    }
    db.load_data()

    grid = msr.GridCreator(db)
    grid.create_grid(fname=SINK_MAP_FILE, use_sinks=True)