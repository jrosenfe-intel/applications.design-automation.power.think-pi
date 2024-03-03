import sys
#sys.path.append(r'\\amr\ec\proj\pandi\EPS1\EPS_Training\5_Advanced_Trainings\59_ThinkPI\1_ThinkPi_Repo\applications.design-automation.power.think-pi-pr279')
sys.path.append(r'applications.design-automation.power.think-pi-pr279')

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
sys.path.append('../../') 

#Database paths:
brd_db_path=r"D:\dgarciam\think_PI_testing\PoInt\GNR_SP_VCCD\hspice\board\M6186203_beechnut_BRD_VCCD_22WW13_ports_clean.spd"
pkg_db_path=None
pkg_patch_db_path=r"D:\dgarciam\think_PI_testing\PoInt\GNR_SP_VCCD\hspice\pkg\pkg_patch\gnr_hcc_vccin-vccd-fivra-inf_odb_2023_05_23_18_44_proc_patch_VCCD_HV0_quiet.spd"
#pkg_patch_db_path=None
pkg_int_db_path=r"D:\dgarciam\think_PI_testing\PoInt\GNR_SP_VCCD\hspice\pkg\pkg_int\gnr_hcc_vccin-vccd-fivra-inf_odb_2023_05_23_18_44_proc_1ohm_interposer_VCCD_HV0.spd"
#pkg_int_db_path=None



# ------------- Don't modify anything below this line -------------
from thinkpi.tools.hspice_deck import HspiceDeck,DeckFactory

#Create the deck initial files
deck=HspiceDeck()
deck.load_brd(db_path=brd_db_path)
if pkg_db_path:
    deck.load_pkg(db_path=pkg_db_path)
if pkg_patch_db_path:
    deck.load_pkg_patch(db_path=pkg_patch_db_path)
if pkg_int_db_path:
    deck.load_pkg_int(db_path=pkg_int_db_path)
deck.init_deck_folder()

#Create the deck excel template file
deck_factory=DeckFactory()
deck_factory.clone_template()

