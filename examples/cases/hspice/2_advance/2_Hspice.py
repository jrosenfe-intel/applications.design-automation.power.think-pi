# ------------- Introduction -------------
'''
The second phase of the deck building process involves creating the Spice deck
files. Before runing this script, the user is responsible for editing the deck_template file to indicate brd and package 
models, capacitor models, loading conditions, VR settings,etc.

'''
# ------------- User defined parameters -------------
import sys

#Path to Think PI version
#sys.path.append(r'\\amr\ec\proj\pandi\DPS6\OakStream\RP\PD\ThinkPI\applications.design-automation.power.think-pi-dev-pr-154\applications.design-automation.power.think-pi-dev')
#sys.path.append(r'.\applications.design-automation.power.think-pi-dev-pr-156\applications.design-automation.power.think-pi-dev')
sys.path.append(r'applications.design-automation.power.think-pi-pr279')

#Deck_template path
fpath='Deck_point.xlsx'
#Hspice version to use
hspice_exe='C:\synopsys\Hspice_P-2019.06-SP2-3\WIN64\hspice.exe'

# ------------- Don't modify anything below this line -------------
from thinkpi.tools.hspice_deck import DeckFactory
deck_factory=DeckFactory()
deck_factory.hspice_mt=1
deck_factory.build_and_run(fpath,hspice_exe)
