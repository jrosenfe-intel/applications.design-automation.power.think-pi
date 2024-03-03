# ------------- Introduction -------------
'''
This is a dedicated flow to create all the required ports for
motherboard VR extractions and studies.

This flow will perform these tasks:
- create ports based only on capacitor components
- reduce the capacitor ports to a lower amount as sepcified by the user
- create VRM ports
- create (or transfer from a package or a board) socket ports
'''

# ------------- User defined parameters -------------

r'''DB_PATH_NAME = r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\db\OOKS1_NFF1S_DNOX_PWRsims_ww50e_VCCIN.spd"
CAP_LAYER_TOP = 'Signal$TOP'
REDUCE_TO_NUM_TOP = 30
CAP_LAYER_BOT = 'Signal$BOTTOM'
REDUCE_TO_NUM_BOT = 30
CAP_FINDER = 'C*'
NET_NAME = 'PVCCIN_CPU0_NORTH_1'
VRM_LAYER = 'Signal$TOP'
SOCKET = 'create' # or 'transfer'
# If creating socket ports
SKT_NUM_PORTS = 40

# If transferring socket ports from a package or a board
PKG_PATH_NAME = r'..\thinkpi_test_db\OKS\db\DMR_PPF_AP_12CH_VCCIN_PDSLICE_CCB_IO_NORTH_proc.spd'
SKT_PORT_SUFFIX = 'skt'
FROM_DB_SIDE = 'bottom' # 'bottom' for package and 'top' for a board

REFZ = 10

DB_PORTS_PATH_NAME = r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\db\OOKS1_NFF1S_DNOX_PWRsims_ww50e_VCCIN_allports.spd"
'''

DB_PATH_NAME = r"..\thinkpi_test_db\OKS\JC2_DNO_100523_0v56B_master_proc_cut.spd"
CAP_LAYER_TOP = 'Signal$TOP'
REDUCE_TO_NUM_TOP = 40
CAP_LAYER_BOT = 'Signal$BOTTOM'
REDUCE_TO_NUM_BOT = 40
CAP_FINDER = 'C*'
NET_NAME = 'PVCCIN_EHV1_CPU_1'
VRM_LAYER = 'Signal$TOP'
SOCKET = 'create' # or 'transfer'
# If creating socket ports
SKT_NUM_PORTS = 40

# If transferring socket ports from a package or a board
PKG_PATH_NAME = r'..\thinkpi_test_db\OKS\DMR_PPF_AP_12CH_VCCIN_PDSLICE_CCB_IO_NORTH_proc.spd'
SKT_PORT_SUFFIX = 'skt'
FROM_DB_SIDE = 'bottom' # 'bottom' for package and 'top' for a board

REFZ = 10

DB_PORTS_PATH_NAME = r"..\thinkpi_test_db\OKS\JC2_DNO_100523_0v56B_master_proc_cut_ports.spd"
# ------------- Don't modify anything below this line -------------
from thinkpi.operations import speed as spd
from thinkpi.operations import pman as pm


if __name__ == '__main__':
    # Load database
    db = spd.Database(DB_PATH_NAME)
    db.load_flags['plots'] = False
    db.load_data()

    db_ports = pm.PortGroup(db)
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
                                    num_ports=REDUCE_TO_NUM_TOP)
    db_ports.add_ports(save=False)
    db_ports = db_ports.reduce_ports(layer=CAP_LAYER_BOT,
                                    num_ports=REDUCE_TO_NUM_BOT)
    db_ports.add_ports(save=False)
    db_ports = db_ports.auto_vrm_ports(layer=VRM_LAYER,
                                        net_name=NET_NAME,
                                        ref_z=REFZ)
    db_ports.add_ports(save=False)

    if SOCKET == 'create':
        db_ports = db_ports.auto_port_conn(num_ports=SKT_NUM_PORTS,
                                            side='top',
                                            net_name=NET_NAME,
                                            ref_z=REFZ)
        db_ports.update_ports(DB_PORTS_PATH_NAME, save=True)
    elif SOCKET == 'transfer':
        pkg = spd.Database(PKG_PATH_NAME)
        pkg.load_data()
        pkg = pm.PortGroup(pkg)
        db_ports = pkg.transfer_socket_ports(to_db=db_ports.db,
                                            from_db_side=FROM_DB_SIDE,
                                            to_db_side='top',
                                            suffix=SKT_PORT_SUFFIX)
        db_ports.add_ports(DB_PORTS_PATH_NAME, save=True)

    db_ports.db.prepare_plots(CAP_LAYER_TOP)
    db_ports.db.plot(CAP_LAYER_TOP)
