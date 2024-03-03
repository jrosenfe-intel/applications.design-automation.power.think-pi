# ------------- Introduction -------------
'''
Based on the list generated and updated by the user from the previous phase,
in this phase, ports will be converted to VRMS and sinks, respectively.

Specifically, the following is executed:
- Assigned ports are converted to VRMs
- Assigned ports are converted to sinks
- Operating points to be filled in by the user 
  as .xlsx files are exported for both VRMS and sinks
'''

# ------------- User defined parameters -------------

# Inputs
# ------
DB_FILE_NAME = r'..\Albert\SPR_noTFC_VCCIN_clean_reduced_V21.spd'
PORT_LIST_FILE_NAME = r'..\Albert\SPR_noTFC_VCCIN_clean_reduced_V21_port_list.csv'

# Outputs
# -------
DB_WITH_VRMS_SINKS = r'..\Albert\SPR_noTFC_VCCIN_clean_reduced_V21_vrms_sinks.spd'

VRM_SETUP_FILE_NAME = r'..\Albert\SPR_noTFC_VCCIN_clean_reduced_V21_vrm_setup.csv'
SINK_SETUP_FILE_NAME = r'..\Albert\SPR_noTFC_VCCIN_clean_reduced_V21_sink_setup.csv'

# ------------- Don't modify anything below this line -------------
from thinkpi.operations import speed as spd
from thinkpi.flows import tasks

if __name__ == '__main__':
    db = spd.Database(DB_FILE_NAME)
    db.load_flags = {'layers': False, 'nets': False,
                    'nodes': True, 'ports': True,
                    'shapes': False, 'padstacks': False,
                    'vias': False, 'components': False,
                    'traces': False, 'plots': False}
    db.load_data()

    db_vrms_sinks = tasks.PdcTask(db)
    db_vrms_sinks.ports_to_vrms(port_fname=PORT_LIST_FILE_NAME)
    db_vrms_sinks.ports_to_sinks(port_fname=PORT_LIST_FILE_NAME)
    db_vrms_sinks.db.save(DB_WITH_VRMS_SINKS)

    db_vrms_sinks.export_vrm_setup(VRM_SETUP_FILE_NAME)
    db_vrms_sinks.export_sink_setup(SINK_SETUP_FILE_NAME)



    


    