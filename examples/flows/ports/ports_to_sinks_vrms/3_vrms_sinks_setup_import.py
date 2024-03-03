# ------------- Introduction -------------
'''
In this phase, VRMs and sinks are setup according
to the user input in the previous phase.
'''

# ------------- User defined parameters -------------
DB_WITH_VRMS_SINKS = r'..\Albert\SPR_noTFC_VCCIN_clean_reduced_V21_vrms_sinks.spd'

VRM_SETUP_FILE_NAME = r'..\Albert\SPR_noTFC_VCCIN_clean_reduced_V21_vrm_setup.csv'
SINK_SETUP_FILE_NAME = r'..\Albert\SPR_noTFC_VCCIN_clean_reduced_V21_sink_setup.csv'

# ------------- Don't modify anything below this line -------------
from thinkpi.operations import speed as spd
from thinkpi.flows import tasks

if __name__ == '__main__':
    db = spd.Database(DB_WITH_VRMS_SINKS)
    db.load_flags = {'layers': False, 'nets': False,
                    'nodes': False, 'ports': False,
                    'shapes': False, 'padstacks': False,
                    'vias': False, 'components': False,
                    'traces': False, 'sinks': False,
                    'vrms': False, 'plots': False}
    db.load_data()

    db_vrms_sinks = tasks.PdcTask(db)
    db_vrms_sinks.import_vrm_setup(VRM_SETUP_FILE_NAME)
    db_vrms_sinks.import_sink_setup(SINK_SETUP_FILE_NAME)
    db_vrms_sinks.db.save(DB_WITH_VRMS_SINKS)





    


    