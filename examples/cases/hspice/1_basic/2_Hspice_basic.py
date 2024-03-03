import sys
sys.path.append(r'\\amr\ec\proj\pandi\EPS1\EPS_Training\5_Advanced_Trainings\59_ThinkPI\1_ThinkPi_Repo\applications.design-automation.power.think-pi-pr279')

# ------------- Introduction -------------
'''
The second phase of the deck building process involves creating the Spice deck
files. Before runing this script, the user is responsible for editing the die and cap maps
as well as placing the brd, pkg, die and cap model in the folders defined in
previous phase.

'''
# ------------- User defined parameters -------------
import sys
#Path to Think PI version
sys.path.append(r'./think-pi-dev_pr_127/applications.design-automation.power.think-pi-dev') 

#Set a case name
Case='12p8G'

#die
die1_path=r"./die/22ww48/diemdl_ddrio_vccddr_hv_gen4p5_4fold_ww47.sp"
die1_conn_map=r'./maps/die_map.csv'

#caps
brd_cap_map="./maps/brd_cap_map_by_comp.csv"
pkg_cap_map="./maps/pkg_cap_map_by_comp.csv"
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


# ------------- Don't modify anything below this line -------------
from thinkpi.tools.hspice_deck import HspiceDeck
from thinkpi.tools.hspice_deck import VRInfo

deck=HspiceDeck(Case)

#Init default user data
deck.init_user_data()

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
deck.connect_attd_caps_to_brd(brd_cap_map)
deck.connect_attd_caps_to_pkg(pkg_cap_map)

#find VR ports
vr_sense_port=deck.find_pkg_vr_sense_port(vr_sense)
vr_ph_ports=deck.find_brd_vr_ph_ports(vr_ph) 


#connect VR
if not enable_tlvr:    
    deck.connect_vrstavggen(vr_ph_ports,vr_sense_port)    
else:    
    deck.connect_tlvrstavggen(vr_ph_ports,vr_sense_port)

#VR tuning
deck.vr_info=VRInfo()
deck.vr_info.sense=vr_sense_port        
deck.vr_info.phs=vr_ph_ports
deck.vr_info.vid=vid
deck.vr_info.avp=avp
deck.vr_info.f0=f0
deck.vr_info.pm=pm
deck.vr_info.vin='12'
deck.vr_info.vramp='1.5'
deck.vr_info.lout=lout
deck.vr_info.rout=rout

#LRVR
deck.vr_info.tlvr_enabled=enable_tlvr
deck.vr_info.l_transformer=l_transformer
deck.vr_info.lc_filter=lc_filter
deck.vr_info.rdc_lc=rdc_lc
deck.vr_info.rout_p=rout_p
deck.vr_info.rout_s=rout_s
deck.vr_info.k_par=k_par

#connect ac
if connect_1a_ac_to_die_ports:    
    deck.connect_1a_ac_to_die_ports()

if connect_pulse_icct_to_die_ports:
    deck.connect_icct_pulse_to_die_ports()

#save Decks
deck.save_deck(zf_s_s=True,lf=True,tune_vr=True)