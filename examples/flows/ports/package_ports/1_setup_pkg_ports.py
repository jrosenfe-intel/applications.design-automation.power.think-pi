# ------------- Introduction -------------
'''
This is a dedicated flow to create all the required ports for
motherboard VR rails on the package.

This flow will perform these tasks:
- create ports based on box definitions
- create ports based only on capacitor components
- reduce the capacitor ports to a lower amount as sepcified by the user
- create (or transfer from a board or package) socket ports
'''

# ------------- User defined parameters -------------

# Inputs
# ------
SINK_PORTS = 'boxes' # or 'auto'
# If creating sink ports from boxes specify database name with boxes placed
# Otherwise specify database name without boxes
DB_BOXES_PATH_NAME = r"..\thinkpi_test_db\DMR\dmr_ap_pwr_vccddr_hv_east_22ww50p4_proc_ports_cports_red_23ww20_new_portsspd_box2.spd"
# If creating sink ports automatically specify the following
SINK_PORTS_LAYER = 'Signal$surface'
SINK_PORTS_NUM = 10
AREA = None # To specify an area to place the ports use (x_bot_left, y_bot_left, x_top_right, y_top_right)

NET_NAME='VCCANA1'
CAP_LAYER_TOP = 'Signal$surface'
REDUCE_TO_NUM_TOP = 30
CAP_LAYER_BOT = 'Signal$base'
REDUCE_TO_NUM_BOT = 5
CAP_FINDER = 'C*'

SOCKET = 'create' # or 'transfer'
# If creating socket ports
SKT_NUM_PORTS = 10

# If transferring socket ports
BRD_PATH_NAME = r'OKS1_NFF1S_DNOX_PWRsims_ww03_processed_all_ports_clip.spd'
SKT_PORT_SUFFIX = 'skt'
FROM_DB_SIDE = 'top' # Use 'bottom' for package and 'top' for a board

DB_PORTS_PATH_NAME = r"dmr_ap_pwr_vccddr_hv_east_22ww50p4_proc_ports_cports_red_23ww20_new_portsspd_box2_ports.spd"

REFZ = 10 # All created ports reference impedance

# ------------- Don't modify anything below this line -------------
from thinkpi.operations import speed as spd
from thinkpi.operations import pman as pm


if __name__ == '__main__':
    # Load database
    db = spd.Database(DB_BOXES_PATH_NAME)
    #db.load_flags['plots']=False
    db.load_data()
    
    db_ports = pm.PortGroup(db)
    if SINK_PORTS == 'boxes':
        db_ports = db_ports.boxes_to_ports(ref_z=REFZ)
    elif SINK_PORTS == 'auto':
        db_ports = db_ports.auto_port(layer=SINK_PORTS_LAYER,
                                        net_name=NET_NAME,
                                        num_ports=SINK_PORTS_NUM,
                                        area=AREA,
                                        ref_z=REFZ)
    db_ports.add_ports(save=False)
    
    # Create all the ports
    db_ports = db_ports.auto_port_comp(layer=CAP_LAYER_TOP,
                                        net_name=NET_NAME,
                                        comp_find=CAP_FINDER,
                                        ref_z=REFZ)
    db_ports.add_ports(save=False)   
    db_ports = db_ports.auto_port_comp(layer=CAP_LAYER_BOT,
                                        net_name=NET_NAME,
                                        comp_find=CAP_FINDER,
                                        ref_z=REFZ)
    db_ports.add_ports(save=False)   
    db_ports = db_ports.reduce_ports(layer=CAP_LAYER_TOP,
                                    num_ports=REDUCE_TO_NUM_TOP,
                                    select_ports=CAP_FINDER)
    db_ports.add_ports(save=False)
    db_ports = db_ports.reduce_ports(layer=CAP_LAYER_BOT,
                                    num_ports=REDUCE_TO_NUM_BOT,
                                    select_ports=CAP_FINDER)
    db_ports.add_ports(save=False)
    
    if SOCKET == 'create':
        db_ports = db_ports.auto_port_conn(num_ports=SKT_NUM_PORTS,
                                            side='bottom',
                                            net_name=NET_NAME,
                                            ref_z=REFZ)
        db_ports.update_ports(DB_PORTS_PATH_NAME, save=True)
    elif SOCKET == 'transfer':
        brd = spd.Database(BRD_PATH_NAME)
        brd.load_data()
        brd = pm.PortGroup(brd)
        db_ports = brd.transfer_socket_ports(to_db=db_ports.db,
                                            from_db_side=FROM_DB_SIDE,
                                            to_db_side='bottom',
                                            suffix=SKT_PORT_SUFFIX)
        db_ports.add_ports(DB_PORTS_PATH_NAME, save=True)

    db_ports.db.prepare_plots(CAP_LAYER_TOP)
    db_ports.db.plot(CAP_LAYER_TOP)
