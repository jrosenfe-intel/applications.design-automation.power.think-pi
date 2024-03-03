import sys
sys.path.append(r'\\amr\ec\proj\pandi\EPS1\EPS_Training\5_Advanced_Trainings\59_ThinkPI\1_ThinkPi_Repo\applications.design-automation.power.think-pi-pr279')

# ------------- Introduction -------------
'''
The initial phase of deck building requires the creation of essential files and
 directories. The user is tasked with the following steps:
1. Placing the script in the deck directory.
2. Creating the 'brd', 'pkg', 'die' and 'caps' directories. 
3. Placing the board and package files (i.e. .spd, .cir, .snp) in the 'brd' and
 'pkg' directories respectively.
4. Adding the capacitor models to the 'caps' directory.
5. Adding the HF icct (if applicable) to the 'icct' directory
5. Modifying the script to reference the correct board and package .spd files.
6. After running the script, editing the generated deck_template, die map and 
cap map files as necessary. It's crucial to save these edited files with new 
names to avoid accidental overwrites in the future.
'''
# ------------- User defined parameters -------------
import sys
#Path to Think PI version
sys.path.append(r'./think-pi-dev_pr_127/applications.design-automation.power.think-pi-dev') 

#Database paths:
brd_db_path=r"./brd/OOKS1_NFF1S_DNOX_PWRsims_ww50e_proc_manual_edits_cports_sktports_ph_ports.spd"
pkg_db_path=r"./pkg/dmr_ap_pwr_vccddr_hv_east_22ww50p4_proc_ports_cports_red_skt.spd"


# ------------- Don't modify anything below this line -------------
from thinkpi.tools.hspice_deck import HspiceDeck,DeckFactory

#Create the deck initial files
deck=HspiceDeck()
deck.load_brd(db_path=brd_db_path)
deck.load_pkg(db_path=pkg_db_path)
deck.init_deck_folder(pkg_cap_map_path_by_port=None,
brd_cap_map_path_by_port=None)
