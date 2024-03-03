import os
import subprocess
from thinkpi.tools import hspice_deck
from thinkpi.tools import idem
from thinkpi.tools import sysutils
import pandas as pd
class idem_plus_hspice:    
    def simple_idem_plus_hspice_zf(self,idemmp_folder,
        sparam_fpath,macro_fpath=None,
        idem_cases_fpath=None,fitting_xml=None,passivity_xml=None,
        timeout=None,
        hspice_path=None,sparam_main_fpath='main_s.sp',
        idem_main_fpath='main_macro.sp',        
        termination_fpath=None): 
        """_summary_

        :param idemmp_folder: _description_
        :type idemmp_folder: _type_
        :param sparam_fpath: _description_
        :type sparam_fpath: _type_
        :param macro_fpath: _description_, defaults to None
        :type macro_fpath: _type_, optional
        :param idem_cases_fpath: _description_, defaults to None
        :type idem_cases_fpath: _type_, optional
        :param fitting_xml: _description_, defaults to None
        :type fitting_xml: _type_, optional
        :param passivity_xml: _description_, defaults to None
        :type passivity_xml: _type_, optional
        :param timeout: _description_, defaults to None
        :type timeout: _type_, optional
        :param hspice_path: _description_, defaults to None
        :type hspice_path: _type_, optional
        :param sparam_main_fpath: _description_, defaults to 'main_s.sp'
        :type sparam_main_fpath: str, optional
        :param idem_main_fpath: _description_, defaults to 'main_macro.sp'
        :type idem_main_fpath: str, optional
        :param termination_fpath: _description_, defaults to None
        :type termination_fpath: _type_, optional        
        """
           


        idemmp_fitting_path	=	idemmp_folder + r'/idemmp_fitting.exe'
        idemmp_passivity_path	=	idemmp_folder + r'/idemmp_passivity.exe'
        idemmp_export_path		=	idemmp_folder + r'/idemmp_export.exe'

        if sparam_main_fpath:
            #run Sparams Deck
            s_param_deck=hspice_deck.HspiceDeck()

            term_df=None
            if termination_fpath:
                term_df=pd.read_csv(termination_fpath)
            s_param_deck.write_test_zf_deck(sparam_main_fpath,sparam_fpath,
            term_df)

            cmd=sysutils.Cmds.run_hspice_cmd(hspice_path,sparam_main_fpath)
            proc=sysutils.ProcessManager()
            proc.schedule_subprocess(commands=cmd,timeout=timeout)
            proc.start()

        #create idem decks
        idem_hspice_deck=hspice_deck.HspiceDeck()

        #Deck Run        
        my_idem=idem.idem()
        my_idem.set_idemmp_path(idemmp_folder)

        proc=sysutils.ProcessManager()
        
        ###
        idem_cases=[]
        import csv
        with open(idem_cases_fpath) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                idem_cases.append([row[0],row[1],row[2],row[3],row[4]])


        for i,row in enumerate(idem_cases[1:]):
            order_min=row[0]
            order_step=row[1]
            order_max=row[2]
            bw=row[3]
            tol=row[4]
            try:
                #create unique file name per case                
                macromodel_it=sysutils.Io.custom_file_path(macro_fpath,f'{i}')                
                #run Idem 

                #h5 file requred by IDEM
                mod_h5_fpath=sysutils.Io.update_file_extension(macromodel_it,
                '.mod.h5')              

                #fitting
                proc=sysutils.ProcessManager()
                cmd=sysutils.Cmds.idemmp_fitting(idemmp_fitting_path,sparam_fpath,
                mod_h5_fpath,order_min,order_step,order_max,bw,1,tol,fitting_xml)
                proc.clear_queue()
                proc.schedule_subprocess(commands=cmd,timeout=timeout)
                proc.start()
                #passive
                cmd=sysutils.Cmds.idemmp_passivity(idemmp_passivity_path,
                mod_h5_fpath,mod_h5_fpath,1,passivity_xml)
                proc.clear_queue()
                proc.schedule_subprocess(commands=cmd,timeout=timeout)
                proc.start()
                #export
                cmd=sysutils.Cmds.idemmp_export(idemmp_export_path,
                mod_h5_fpath,macromodel_it)
                proc.clear_queue()
                proc.schedule_subprocess(commands=cmd,timeout=timeout)
                proc.start()
                
                if idem_main_fpath:
                    deck_it=sysutils.Io.custom_file_path(idem_main_fpath,f'{i}')
                    idem_hspice_deck.write_test_zf_deck(deck_it,macromodel_it,
                    term_df)
                    #run hspice
                    cmd=sysutils.Cmds.run_hspice_cmd(hspice_path,deck_it)

                    proc.clear_queue()
                    proc.schedule_subprocess(commands=cmd,timeout=timeout)
                    proc.start()
                
            except Exception as e:
                print(e)            

        
       