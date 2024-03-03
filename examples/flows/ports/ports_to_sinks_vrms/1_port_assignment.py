# ------------- Introduction -------------
'''
In this phase, a port list (.csv file) is generated for the user to
assign it to be a VRM or a sink. The list will be populated with inferred
initial values.
Based on this assignment list, in the next phase,
the corresponding ports will convert to VRMS and sinks, respectively.
'''

# ------------- User defined parameters -------------

# Inputs
# ------
DB_FILE_NAME = r'..\Albert\SPR_noTFC_VCCIN_clean_reduced_V21.spd'

# Outputs
# -------
PORT_LIST_FILE_NAME = r'..\Albert\SPR_noTFC_VCCIN_clean_reduced_V21_port_list.csv'

# ------------- Don't modify anything below this line -------------
from thinkpi.operations import speed as spd
from thinkpi.operations import pman as pm

if __name__ == '__main__':
    db = spd.Database(DB_FILE_NAME)
    db.load_flags = {'layers': False, 'nets': False,
                    'nodes': True, 'ports': True,
                    'shapes': False, 'padstacks': False,
                    'vias': False, 'components': False,
                    'traces': False, 'sinks': False,
                    'vrms': False, 'plots': False}
    db.load_data()

    db_ports = pm.PortGroup(db)
    db_ports.export_port_info(ports_fname=PORT_LIST_FILE_NAME,
                                names_only=True)



    


    