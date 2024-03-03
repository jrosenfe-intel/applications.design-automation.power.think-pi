import sys
#Path to Think PI version
sys.path.append(r'D:\dgarciam\oks\vccana_ww52\brd\brd\idem\auto\think-pi-dev_pr_143\applications.design-automation.power.think-pi-dev') 


from thinkpi.tools import idem_plus_hspice
from thinkpi.tools import hspice_deck
from thinkpi.tools.hspice_deck import PSITerminationFile



#Create Idem Models
#idemmp_folder=r'C:/"Program Files (x86)"/"CST Studio Suite 2020"/"AMD64"'
idemmp_folder=r'C:\"Program Files (x86)"\"CST Studio Suite 2022"\AMD64'
#Input sparameter file
sparam_fpath='OKS1_NFF1S_DNOX_PWRsims_ww03_processed_all_ports_clip_012623_173538_30544_DCfitted.s29p'
idem_cases_fpath=r'idem_cases.csv'
fitting_xml=r'advance_settings_fitting.fopt.xml'
passivity_xml=r'advance_settings_passivity.popt.xml'



#Hspice path
hspice_path='C:\synopsys\Hspice_P-2019.06-SP2-3\WIN64\hspice.exe'

termination_fpath='termination.csv'

#Sparameters deck 
sparam_deck_fpath='main_zf_s.sp'

#Idem options
macro_fpath="macro.cir"
idem_main_fpath='main_zf_macro.sp'

#Create termination file
#termfile=PSITerminationFile()
#termfile.create_termination(sparam_fpath,termination_fpath)

idem_plus_hspice=idem_plus_hspice.idem_plus_hspice()
#Create and Run macromodels
idem_plus_hspice.simple_idem_plus_hspice_zf(idemmp_folder=idemmp_folder, 
sparam_fpath=sparam_fpath,macro_fpath=macro_fpath,idem_cases_fpath=idem_cases_fpath,
fitting_xml=fitting_xml,passivity_xml=passivity_xml,timeout=30,
hspice_path=hspice_path,sparam_main_fpath=sparam_deck_fpath,
idem_main_fpath=idem_main_fpath,termination_fpath=termination_fpath)