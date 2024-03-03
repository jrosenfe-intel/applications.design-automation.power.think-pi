import sys
sys.path.append(r'applications.design-automation.power.think-pi-pr279')
# ------------- Introduction -------------
'''
Example script to build a custom Hspice deck.
Before runing this script, the user is responsible for editing the die and cap maps
as well as placing the brd, pkg, die and cap model in the folders defined in
previous phase.

'''
# ------------- User defined parameters -------------
#import sys
#Path to Think PI version
#sys.path.append(r'./think-pi-dev_pr_127/applications.design-automation.power.think-pi-dev') 

#Set a case name
case_name='case1'

#die
die1_path=r"./die/die_oks_23ww09/cdie_wrapper_32p.inc"
die1_conn_map=r'./maps/c_die_map_oks23ww09.csv'

#caps maps. 
#Note: Map can be read from a file or created programmatically
brd_cap_map="./maps/brd_cap_map_by_port.csv"
pkg_cap_map="./maps/pkg_cap_map_by_port.csv"

#path to the Hspice version to be used. Recommended 2019 or newer.
Hspice_path='C:\synopsys\Hspice_P-2019.06-SP2-3\WIN64\hspice.com'

# ------------- Optional User defined parameters -------------
#optional BRD info
#Specify either a folder containing the model files OR the path to each file.
brd_model_folder=None
brd_db_path=None
brd_idem_mod_path=None
brd_tstone_path=None

#optional PKG info
#Specify either a folder containing the model files OR the path to each file.
pkg_model_folder=None
pkg_db_path=None
pkg_idem_mod_path=None
pkg_tstone_path=None

#Optional socket parameters
brd_skt_refdes=None
pkg_skt_refdes=None

#Optional VR parameters
#For PKG ports, use 'pkg_<name port>', for example: 'pkg_sense'. For board ports use 'brd_<port name>', for example 'brd_ph1'
#Additionally wildcards are valid, for example: '*sense' or '*ph1'
vr_sense=['*sp*','*sense*']
vr_ph=None
#VR tuning
vid='1.8'
avp='0'
f0='100e3'
pm='60'
lout='1n'
rout='.29m'
#LRVR parameters
enable_tlvr=False
l_transformer=''
lc_filter='100n'
rdc_lc='70n'
rout_p='0.125m'
rout_s='0.145m'
k_par='0.89'

#Additional die
die2_path=None
die2_conn_map=None

#Additional die
die3_path=None
die3_conn_map=None

#1A AC
connect_1a_ac_to_die_ports=True

#LF
connect_pulse_icct_to_die_ports=True


               
# -------------Deck construction section -------------
from thinkpi.tools.hspice_deck import HspiceDeck
from thinkpi.tools.hspice_deck import CircuitPortNameSpace
from thinkpi.tools.hspice_deck import VRInfo
from thinkpi.tools.sysutils import ProcessManager
from thinkpi.tools.sysutils import Cmds


#create a Deck object with a given name (case)
deck=HspiceDeck(case_name)

#Init default user data
deck.init_user_data()

#Sim options
deck.sim_option_line=\
"""
.option post=2  post_version = 2001 resmin = 1e-10
*.OPTION POST=1 RESMIN = 1E-10
.OPTION BRIEF
.OPTION PROBE
.option unwrap = 1
.OPTION RUNLVL=3 METHOD = gear
"""

#Parameter required by die model
deck.update_user_data_param('ac_nodes','64')


#connect pkg and brd
deck.load_brd(db_path=brd_db_path,idem_mod_path=brd_idem_mod_path,
              tstone_path=brd_tstone_path,
              model_folder=brd_model_folder)

deck.load_pkg(db_path=pkg_db_path,idem_mod_path=pkg_idem_mod_path,
              tstone_path=pkg_tstone_path,
              model_folder=pkg_model_folder)

deck.connect_skt(brd_skt_name=brd_skt_refdes, pkg_skt_name=pkg_skt_refdes)

#connect die
deck.connect_die_using_mapfile(die1_path,die1_conn_map)

if die2_path and die2_conn_map:
    deck.connect_die_using_mapfile(die2_path,die2_conn_map)

if die3_path and die3_conn_map:
    deck.connect_die_using_mapfile(die3_path,die3_conn_map)

#connect caps
deck.load_attd_caps_models()
#deck.connect_attd_caps_to_brd(brd_cap_map)
#deck.connect_attd_caps_to_pkg(pkg_cap_map)

#build a cap map with the following format: [port,cap,qty]
brd_ports=deck.brd_instance.ports
map1=[]
map1.append([brd_ports[0],'CapTDK_0805_NA_47uF_1p8Vdc_90p2C_EOL.sp',3])

pkg_ports=deck.pkg_instance.ports
map2=[]
map2.append([pkg_ports[0],'Cap_0201_LP_2p2uF_2p5V_1p8DC_EOL_90C_X6T_A95538_014_Kyocera.sp',3])

deck.connect_attd_caps_to_psi_instance_by_port(
    deck.brd_instance,map=map1,category='brd_caps',
    port_name_space=CircuitPortNameSpace.INSTANCE)
deck.connect_attd_caps_to_psi_instance_by_port(
    deck.pkg_instance,map=map2,category='pkg_caps',
    port_name_space=CircuitPortNameSpace.INSTANCE)


#Short VR ports 
vr_ph_ports=deck.find_brd_vr_ph_ports(vr_ph) 
deck.short_ports+=vr_ph_ports


#add probe
deck.probe_v_ac(vr_ph_ports)

#connect VR
#vr_sense_port=deck.find_pkg_vr_sense_port(vr_sense)
#vr_ph_ports=deck.find_brd_vr_ph_ports(vr_ph) 
# if not enable_tlvr:    
#     deck.connect_vrstavggen(vr_ph_ports,vr_sense_port)    
# else:    
#     deck.connect_tlvrstavggen(vr_ph_ports,vr_sense_port)
# 
# #VR tuning
# deck.vr_info=VRInfo()
# deck.vr_info.sense=vr_sense_port        
# deck.vr_info.phs=vr_ph_ports
# deck.vr_info.vid=vid
# deck.vr_info.avp=avp
# deck.vr_info.f0=f0
# deck.vr_info.pm=pm
# deck.vr_info.vin='12'
# deck.vr_info.vramp='1.5'
# deck.vr_info.lout=lout
# deck.vr_info.rout=rout
# 
# #LRVR
# deck.vr_info.tlvr_enabled=enable_tlvr
# deck.vr_info.l_transformer=l_transformer
# deck.vr_info.lc_filter=lc_filter
# deck.vr_info.rdc_lc=rdc_lc
# deck.vr_info.rout_p=rout_p
# deck.vr_info.rout_s=rout_s
# deck.vr_info.k_par=k_par
# 
# ##connect ac
# #if connect_1a_ac_to_die_ports:    
# # deck.connect_1a_ac_to_die_ports()


#save Deck
main_files=[]
main_files+=deck.save_deck(zf=True)

#modify the deck
deck.case='case2'

deck.update_user_data_param('Imin_core','25')


#modify capacitors
deck.attd_cap_groups.clear()
brd_ports=deck.brd_instance.ports
map1=[]
map1.append([brd_ports[0],'CapTDK_0805_NA_47uF_1p8Vdc_90p2C_EOL.sp',10])

pkg_ports=deck.pkg_instance.ports
map2=[]
map2.append([pkg_ports[0],'Cap_0201_LP_2p2uF_2p5V_1p8DC_EOL_90C_X6T_A95538_014_Kyocera.sp',20])

deck.connect_attd_caps_to_psi_instance_by_port(
    deck.brd_instance,map=map1,category='pkg_caps',
    port_name_space=CircuitPortNameSpace.INSTANCE)
deck.connect_attd_caps_to_psi_instance_by_port(
    deck.pkg_instance,map=map2,category='brd_caps',
    port_name_space=CircuitPortNameSpace.INSTANCE)

#save 2nd deck
main_files+=deck.save_deck(zf=True)

#add the decks to the queue to run later
pm=ProcessManager() 
for fname in main_files:            
    command=Cmds.run_hspice_cmd(Hspice_path,fname)       
    pm.schedule_subprocess(command)
#run the decks
subproc_batch_size=2
pm.start(subproc_batch_size)
