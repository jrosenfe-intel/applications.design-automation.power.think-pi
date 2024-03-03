import os
import csv
import pathlib
import shutil
import re
from math import log10
import numpy as np
from enum import Enum
from collections import OrderedDict
import pandas as pd

from thinkpi.operations import speed as spd
from thinkpi.tools.sysutils import TextProcessor,EventLogger,Io,Cmds,ProcessManager


class SubcktParsingState(Enum):
    """
    Enum class representing the different states of a subckt parsing activity.

    NOT_STARTED: Parsing has not started yet.
    NAME: Parsing the subckt name.
    NODES: Parsing the subckt port names.
    PARAMS: Parsing the subckt parameter names.
    COMPLETED: The parsing process is completed.
    """
    NOT_STARTED=0
    NAME=1
    NODES=2
    PARAMS=3
    COMPLETED=4

class CircuitInstanceTextFormat(Enum):
    """
    Enum class representing the different text formats for a circuit instance.
    
    MULTI_LINE: Instance text spans multiple lines.
    IN_LINE: Instance text is in a single line.
    PAR_MULTI_LINE: Instance text is in a single line, except for the 
    instance parameters, which are each placed on a separate line.
    """
    MULTI_LINE=1
    IN_LINE=2
    PAR_MULTI_LINE=3

class AnalysisType(Enum):
    """
    Enum class to represent the different Spice Analysis Types.

    BODE: Bode analysis
    ZF: AC Impedance profile analysis 
    LF: Transient LF analyhsis
    HF: Transient HF analysis
    """
    BODE=1
    ZF=2
    LF=3
    HF=4
    LIN=5   
    TUNE_VR=6

class PsiModelType(Enum):
    """
    Enum class to represent the different PSI models

    TSTONE: Bode analysis
    MACRO1: IDEM Macromodel #1    
    """
    TSTONE=0
    MACRO1=1


class Subckt:
    """
    Class to represent a SPICE subcircuit (.subckt) definition
    
    :param path: The full path of the file that contains the .subckt
    :type path:str    
    :param name: The subckt name.
    :type name:str
    :param ports: The list of port (nodes) names.
    :type name:List[str]
    :param params: The list of parameter names.        
    :type name:List[str]
    :param parsing_state: subckt parsing state.
    :type name:SubcktParsingState
    """
    def __init__(self,fpath=None):       
        """Initialize the Subckt object.

        :param fpath: The spice file path to load data from, defaults to None
        :type fpath: _type_, optional
        """
        self.fpath=fpath                
        self.name=None
        self.ports=[]
        self.params=[]        
        
        self.parsing_state=SubcktParsingState.NOT_STARTED
        if fpath:
            self.load_data(fpath)        
                                       
    def load_data(self, fname):
        """Load information associated with a subckt from a text file.

        :param fname: Name of the text file that contains the '.subckt.'
        Typically is a file with extention .inc,.cir,.sp or .txt
        :type fname: str
        """
        fname=os.path.abspath(fname)        
        self.fpath=fname             
        lines=[]        
        with open(fname) as f:
            lines = f.readlines()

        self.parsing_state=SubcktParsingState.NAME
        for line in lines:
            if self.parsing_state != SubcktParsingState.COMPLETED:
                self.parse_line(line)        
        
    @property
    def filename(self):
        """Get the filename of the model file

        :return: The filename of the model file
        :rtype: _type_
        """
        return os.path.basename(self.fpath)

    def parse_line(self,line):
        """Process each line of a subckt definition to identify the subckt name,
        nodes and parameters.
        :param line: The line to be processed.
        :type line: str        
        """
        line=line.lower()
        match = re.compile(r"^\*")
        if re.search(match,line):        
            return

        match = re.compile(r"^.inc")
        if re.search(match,line):        
            return        
        if  self.parsing_state==SubcktParsingState.NODES or \
            self.parsing_state==SubcktParsingState.PARAMS:         
            match = re.compile(r"^\+")
            if not re.search(match,line):        
                self.parsing_state=SubcktParsingState.COMPLETED
                return

                   
        line=line.replace('=', ' = ')
        line=line.replace('+', '+ ')
        words=line.split()
        
        i=0
        while i < len(words):
            
            if self.parsing_state==SubcktParsingState.NAME:
                if(words[i].lower()=='.subckt'):
                    i+=1
                    self.name=words[i]
                    i+=1
                    self.parsing_state=SubcktParsingState.NODES
                    continue  
                else:
                    i+=1
            if self.parsing_state==SubcktParsingState.NODES:
                                
                if(words[i]=='+'):
                    i+=1                                                  
                
                if(i+1<len(words)):                    
                    if(words[i+1]=='='):
                        self.parsing_state=SubcktParsingState.PARAMS
                        
                    else:
                        self.ports.append(words[i])
                        i+=1
                else:
                    self.ports.append(words[i])
                    i+=1
            if self.parsing_state==SubcktParsingState.PARAMS:
                
                if(words[i]=='+'):
                        i+=1
                        continue
                if(i+2<len(words)):
                    if(words[i+1]=='='):
                        self.params.append([words[i],words[i+2]])
                        i+=1
                    else:
                        i+=1
                else:
                    break


class SubcktInstance:
    """
    Represents an instance of a circuit in a Spice deck.
    
    Attributes:
        name (str): The name of the instance.
        ports (List[str]): A list of the ports of the instance.
        model (Subckt): The subcircuit model of the instance.
        params (dict[str,str]): A dictionary of parameters for the instance where the
        key is the parameter name and the value is the parameter value.
    """
    
    def __init__(self):          
       self.name='my_circuit'
       self.ports=[]
       self.model=Subckt()
       self.params={}       

    def init_instance_port_names(self,ref_ports='vss*'):
        """
        Initialize the instance port names by combining the instance name and the model port name.
        Any port that matches the wildcard pattern in `ref_ports` will be given the name '0'.
        :param ref_ports: A wildcard pattern used to match certain port names.
        :type ref_ports: string
        """
        self.ports=[]
        for port in self.model.ports:
            if TextProcessor.match(port,ref_ports):
                self.ports.append('0')
            else:
                self.ports.append(self.name+'_' + port)  

    def replace_text_in_ports(self,old_text,new_text):
        """Replace all occurrences of 'old_text' with 'new_text' in the 
        instance's port names.

        :param old_text: the text to be replaced.
        :type old_text: str
        :param new_text: the replacement text.
        :type new_text: str
        """
        new_ports=[]
        for p in self.ports:
            new_ports.append(p.replace(old_text,new_text))
        self.ports=new_ports

    def get_instance_port_name(self,model_port_name):
        """Return the instance port name corresponding to the model port name

        :param model_port_name: the name of a model port
        :type model_port_name: str
        :return: the name of the instance port corresponding to the given model \
        port name.
        :rtype: str
        """
        for i in range(len(self.model.ports)):
            if self.model.ports[i]==model_port_name.lower():
                return self.ports[i]
    
    def get_ports_by_name(self,
        port_names='*ph*'):        
        """Get ports that match the given names.

        :param port_names: port_names (str, optional): The port names to match. \
        Wildcards are supported, defaults to '*ph*'
        :type port_names: str, optional
        :return: A list of port names that match the given names
        :rtype: List[str]
        """
        ports=[]        
        for port in self.ports: 
            if TextProcessor.match(port,port_names):
                ports.append(port)            
        return ports

    def to_text(self,text_format=CircuitInstanceTextFormat.MULTI_LINE):
        """Return the SPICE-compatible text representing this circuit instance.

        :param text_format: Text format, defaults to CircuitInstanceTextFormat.\
        MULTI_LINE
        :type text_format: CircuitInstanceTextFormat, optional
        :return: A list of text lines representing this circuit instance.
        :rtype: List[str]
        """
        lines=[]        
        if text_format == CircuitInstanceTextFormat.MULTI_LINE:
            lines.append(f'x_{self.name}\n' )        
            for port in self.ports:        
                lines.append(f'+{port}\n')               
            lines.append(f'+{self.model.name}\n')
            lines.append('+\n')
            for par_name in self.params:
                par_value=self.params[par_name]                                    
                lines.append(f'+{par_name} = \'{par_value}\'\n')

        elif text_format == CircuitInstanceTextFormat.IN_LINE:
            line=f'x_{self.name} ' 
            for port in self.ports:
                line+= port+' '
            line+=self.model.name+ ' '
            for par_name in self.params:
                par_value=self.params[par_name]                    
                line+=f'{par_name} = \'{par_value}\' '            
            line+='\n'
            lines.append(line)

        elif text_format == CircuitInstanceTextFormat.PAR_MULTI_LINE:
            line=f'x_{self.name} ' 
            for port in self.ports:
                line+= port+' '
            line+=self.model.name+ '\n'
            lines.append(line)
            for par_name in self.params:
                par_value=self.params[par_name]
                lines.append(f'+{par_name} = \'{par_value}\'\n')                 
        return lines            

class Tstone:
    def __init__(self):
        self.name =''
        self.fpath = None
        self.ports = []        
    
    def load_data(self,name,fpath,port_names_fpath):
        self.fpath=fpath   
        with open(port_names_fpath) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:                
                self.ports.append(row[0])
            
            print(self.ports)       
    
class TstoneInstance:
    def __init__(self):
        self.name =''
        self.model=None        
        self.ports = []
    def get_ports_by_name(self,port_names='*ph*'):        
        
        ports=[]        
        for port in self.ports:            
            if TextProcessor.match(port,port_names):
                ports.append(port)            
        return ports        
        
class CompInPsiPort:
    """Auxiliary class for representing a component associated with PSI ports.

    :ivar name: The name of the component.
    :vartype name: str
    :ivar part: A list of parts associated with the component.
    :vartype part: list
    :ivar pos_pins: A list of positive pins associated with the component.
    :vartype pos_pins: list
    :ivar neg_pins: A list of negative pins associated with the component.
    :vartype neg_pins: list
    """
    def __init__(self):        
        self.name = ''
        self.part = []
        self.pos_pins = []
        self.neg_pins = []
        

class PsiPort:
    """Auxiliary class for representing a PSI port associated with one or more \
    components.

    :ivar name: The name of the port.
    :vartype name: str
    :ivar comps: A list of components associated with the port.
    :vartype comps: list of CompInPsiPort objects
    """
    def __init__(self):
        """Initialize a PsiPort object with the name 'port' and an empty list \
        of components."""
        self.name = 'port'
        self.comps = []        

    def __str__(self):
        """Return the name of the port as a string."""
        return self.name

class ModPsi:
    
    """A Class to represent a PSI model.

        :ivar name: The name of the model.
        :vartype name: str
        :ivar db_path: The path of the database file.
        :vartype db_path: str
        :ivar db_ports: The list of ports in the database file.
        :vartype db_path: list
        :ivar db_skt_name: The socket ref desc in the database file.
        :vartype db_skt_name: str
        :ivar tstone_path: The path of the .snp file.
        :vartype tstone_path: str
        :ivar tstone_mod_name (str): The name of the model in the .snp file.
        :vartype tstone_mod_name: str
        :ivar macro (str or None): The .cir (macro model) associated with the model.
        :vartype macro: str
    """

    def __init__(self):
       self.name=''
       self.db_path=''
       self.db_ports=[]
       self.db_skt_name=''
       self.db_conn_refdes_top=''
       self.db_conn_refdes_bot=''
       
       self.tstone_path=''       
       self.tstone_mod_name='brd'       

       self.macro= None
              
    def load_data(self, db_path=None,idem_mod_path=None,tstone_path=None,
        model_folder=None,conn_side='top'):
        """Load information asociated to a PSI model.

        :param db_path: .spd path
        :type db: str
        :param inc_path: .cir or .spn path
        :type inc_path: str
        """

        if model_folder:
            files=Io.find_in_folder(model_folder,'*.spd',False)            
            if len(files)==0:
                EventLogger.raise_value_error(f'.spd file not found in folder: {model_folder}.')
            elif len(files)==1:
                db_path=files[0]
            else:
                EventLogger.raise_value_error(f'multiple .spd files in folder: {model_folder}.')
            files=Io.find_in_folder(model_folder,'*.cir',False)
            if len(files)==0:                
                EventLogger.raise_value_error(f'.cir file not found in folder: {model_folder}.')
            elif len(files)==1:                
                idem_mod_path=files[0]
            else:
                EventLogger.raise_value_error(f'multiple .cir files in folder: {model_folder}.')

            files=Io.find_in_folder(model_folder,'*.s*p',False)
            if len(files)==0:                
                EventLogger.raise_warning(f'.snp file not found in folder: {model_folder}.')
            elif len(files)==1:
                tstone_path=files[0]
            else:
                EventLogger.raise_warning(f'multiple .snp files in folder: {model_folder}.')


        db = spd.Database(db_path)
        db.load_flags['shapes']=False
        db.load_flags['plots']=False        
        db.load_flags['vias']=False        
        db.load_flags['traces']=False        
        db.load_flags['padstacks']=False            
        db.load_data()
        
        folder_file = os.path.split(db_path)
        self.name=folder_file[1]
        self.db_path=db_path
        try:
            self.db_skt_name=db.get_conn(conn_side).name
        except ValueError as e:
            EventLogger.raise_warning('Cannot find skt for db: '+db_path)

        try:
            self.db_conn_refdes_bot=db.get_conn('bottom').name
        except ValueError as e:
            EventLogger.raise_warning('Cannot find bottom conn for db: '+db_path)
        
        try:
            self.db_conn_refdes_top=db.get_conn('top').name
        except ValueError as e:
            EventLogger.raise_warning('Cannot find top conn for db: '+db_path)
            
        self.load_db_ports(db)

        if idem_mod_path:            
            self.macro=Subckt(idem_mod_path)                        

        self.tstone_path=tstone_path
        self.init_tstone_mod_name()
        
                        
    def find_comp_models_in_ports(self,comp_names='C*'):
        """Find components in ports matching the given names.

        :param comp_names: Wildcard pattern to match component names., \
        defaults to 'C*'
        :type comp_names: str, optional
        :return: List containing the name of the port, the component part, and \
        the count of components found in that port
        :rtype: List[str,str,str]
        """
        comps=[]
        for model_port in self.db_ports:            
            for comp in model_port.comps:
                if TextProcessor.match(comp.name,comp_names):
                    comps.append([model_port.name,comp.part])                
        comps_summary=[]
        for c in comps:
            found=False
            for i in range(len(comps_summary)):
                c_sum=comps_summary[i]
                if c[0]==c_sum[0] and c[1]==c_sum[1]: #match port and part
                    comps_summary[i]=[c_sum[0],c_sum[1],c_sum[2]+1]
                    found=True

            if found==False:
                comps_summary.append([c[0],c[1],1])        
        return comps_summary

    def get_comp_model_names(self,comp_names='C*'):
        """Get the model names of components matching the given names

        :param comp_names: Wildcard pattern to match component names, defaults to 'C*'
        :type comp_names: str, optional
        :return: Set of unique component model names
        :rtype: set(str)
        """
        comp_parts=set()        
        for port in self.db_ports:
            for comp in port.comps:                
                if TextProcessor.match(comp.name,comp_names):
                    comp_parts.add(comp.part) 
        return comp_parts
    
    def get_comp_names(self,comp_names='C*'):   
        """Get the list of all components matching the given names

        :param comp_names: Wildcard pattern to match component names, defaults to 'C*'
        :type comp_names: str, optional
        :return: List of component names
        :rtype: List(str)
        """     
        data=[]
        for port in self.db_ports:
            for comp in port.comps:                
                if TextProcessor.match(comp.name,comp_names):
                    data.append(comp.name) 
        return data
    
    def load_db_ports(self,db):
        """Load the port information from the dabase

        :param db: Database
        :type db: str
        :return: Summary of the components asociated to all ports
        :rtype: List
        """        
        ports_info=[]
        for port in db.ports:    
            port_info=PsiPort()        
            port_info.name=port                    
            for node in db.ports[port].pos_nodes:
                if(node.type=='pin'):
                    comp=self.get_comp_from_pin(db,node.name)                                                
                    found=False
                    if not comp:
                        EventLogger.raise_warning(f'No comp found for port: {port}, pin {node.name}')
                        continue
                    for comp_in_port in port_info.comps:                                        
                        if comp_in_port.name==comp.name:
                            found=True                
                            comp_in_port.name=comp.name
                            comp_in_port.part=comp.part
                            comp_in_port.pos_pins.append(node.name)
                    if found==False:
                        comp_in_port=CompInPsiPort()
                        comp_in_port.name=comp.name
                        comp_in_port.part=comp.part
                        comp_in_port.pos_pins.append(node.name)
                        port_info.comps.append(comp_in_port)
            for node in db.ports[port].neg_nodes:
                if(node.type=='pin'):
                    comp=self.get_comp_from_pin(db,node.name)                                                
                    found=False
                    if not comp:
                        EventLogger.raise_warning(f'No comp found for port: {port}, pin {node.name}')
                        continue
                    for comp_in_port in port_info.comps:                                        
                        if comp_in_port.name==comp.name:
                            found=True                
                            comp_in_port.name=comp.name
                            comp_in_port.part=comp.part
                            comp_in_port.neg_pins.append(node.name)
                    if found==False:
                        comp_in_port=CompInPsiPort()
                        comp_in_port.name=comp.name
                        comp_in_port.part=comp.part
                        comp_in_port.neg_pins.append(node.name)
                        port_info.comps.append(comp_in_port)                                      
            ports_info.append(port_info)
        
        self.db_ports=ports_info    
    
    def init_tstone_mod_name(self):
        """Initialize the tstone model name 
        """
        if self.tstone_path:
            folder_file = os.path.split(self.tstone_path)
            root_ext = os.path.splitext(folder_file[1])
            self.tstone_mod_name=root_ext[0]        
        
    def get_comp_from_pin(self,db,node_name):
        """Return the component information asociated to a pin name

        :param db: Database
        :type db: spd.Database        
        :param node_name: Node name
        :type node_name: str
        :return: Component information
        :rtype: component object
        """
        comps=db.find_comps("*",False)    
                
        for comp in comps:
            
            comp_nodes=db.connects[comp.name].nodes
            for comp_node in comp_nodes:
                if(comp_node==node_name):
                    return comp

    def get_db_port_pin_count(self,port_name): 
        """Get the pin count in the ports that match the given name

        :param port_name: Port Name
        :type port_name: str
        :return: List containing number of pins for hte possitive and negative terminal
        :rtype: List[str,str]
        """
        pos_pins=0  
        neg_pins=0
        for port in self.db_ports:                    
            if(port.name==port_name):
                for comp in port.comps:                    
                    pos_pins+=len(comp.pos_pins)
                    neg_pins+=len(comp.neg_pins)
        return [pos_pins,neg_pins]

    def save_db_port_list(self,fpath):                  
        """Save the port List into a file

        :param data_path: file path
        :type data_path: str
        """
        with open(fpath, 'w',newline='') as f:            
            writer = csv.writer(f)
            for port in self.db_ports:
                writer.writerow([port.name])
    
              
            
    def save_db_comp_mod_names(self,data_path,comp_names='C*'):  
        """Save the components belonging to the ports of a model.
        
        :param data_path: output file path
        :type data_path: str
        :param comp_names: Wildcard to filter the parts, defaults to 'C*'
        :type comp_names: str, optional
        """        
        data=self.get_comp_model_names(comp_names)
           
        with open(data_path, 'w',newline='') as f:            
            writer = csv.writer(f)
            for row in data:
                writer.writerow([row])   

    
 

class InsPsi:
    """Psi model Instance information
    """
    def __init__(self):
       
       self.model=ModPsi()
       
       self.name='mybrd'
       self.ports=[]

    def init_instance_port_names(self):
        """set the initial names for the instance ports        
        """
        self.ports=[]
        for port in self.model.db_ports:
            self.ports.append(self.name+'_' + port.name)
        self.ports.append('0')

    def find_comp_models_in_ports(self,comp_names='C*'):
        """Return the components asociated to the ports 

        :param comp_names: Wildcard to return the matching components, 
        defaults to 'C*'
        :type comp_names: str, optional
        :return: return a list of the matching components belonging to the 
        ports that match 
        :rtype: _type_
        """
        
        comps_sum_model=self.model.find_comp_models_in_ports(comp_names)
        comps_sum=[]
        for row in comps_sum_model:
            comps_sum.append([self.get_instance_port_name(row[0]),row[1],row[2]])
        return comps_sum

    def get_instance_port_name(self,model_port_name):
        """Return the instance port name corresponding to the model port name

        :param model_port_name: PSI model port name
        :type model_port_name: str
        :return: Instance port name
        :rtype: str
        """
        for i in range(len(self.model.db_ports)):
            if self.model.db_ports[i].name==model_port_name:
                return self.ports[i]
        
    def replace_text_in_ports(self,old_text,new_text):
        """_summary_

        :param old_text: _description_
        :type old_text: _type_
        :param new_text: _description_
        :type new_text: _type_
        """
        new_ports=[]
        for p in self.ports:
            new_ports.append(p.replace(old_text,new_text))
        self.ports=new_ports


    def find_ports_by_name(self,port_names='*ph*'):        
        """Find the ports that match the provided wildcard.

        :param port_names: List or string with the wildcards to match, defaults to '*ph*'
        :type port_names: str, optional
        :return: List containing the ports that match the provided wildcard
        :rtype: List[str]
        """
        ports=[]        
        for port in self.ports:            
            if TextProcessor.match(port,port_names):
                ports.append(port)            
        return ports
    
    def find_ports_by_comp_name(self,comp_names='*U*'):
        ports=set()        
        for model_port in  self.model.db_ports:            
            for comp in model_port.comps:   
                if TextProcessor.match(comp.name,comp_names):
                    ports.add(self.get_instance_port_name(model_port.name))                

        return list(ports)
    
    def find_port_by_model_port_name(self,port_names='*ph*'):
        ports=set()        
        for model_port in  self.model.db_ports:                        
            if TextProcessor.match(model_port.name,port_names):
                ports.add(self.get_instance_port_name(model_port.name))                

        return list(ports)

class InsGroup:
    """A class to contain multiple circuit instances
    """
    def __init__(self):        
        self.name='group'
        self.instances={}

    def get_iprobe_name(self):
        """Return the current probe name that represents the total current for
        all instances in the group

        :return: current probe name
        :rtype: str
        """
        return 'itot_'+self.name

class VRInfo:
    """A class to contain the VR information
    """
    def __init__(self):        
        self.sense=None
        self.phs=None
        self.vid=None
        self.avp=None
        self.f0=None
        self.pm=None
        self.vin=None
        self.lout=None
        self.rout=None
        self.vramp=None        
        #TLVR
        self.tlvr_enabled=False
        self.l_transformer=None
        self.lc_filter=None
        self.rdc_lc=None
        self.rout_p=None
        self.rout_s=None
        self.k_par=None

        self.core_relative_path='/vr_tuning_engine/'
    
    @property
    def vr_tune_core_folder(self):
        """return the abs path for folder containing the Matlab tuning engine

        :return: folder path
        :rtype: str
        """
        return  os.path.abspath(os.path.dirname(__file__)+self.core_relative_path)
    

    def save_matlab_tuning(self,fpath,tstone_file,comp_file):
        """Save the tuning script to be run in Matlab for tuning

        :param fpath: Matlab script file to be created
        :type fpath: str
        :param tstone_file: plat Touchstone file (.s2p)
        :type tstone_file: str
        :param comp_file: path for the CSV file that the Matlab engine should 
        create containing the Type III tuning parameters
        :type comp_file: str
        """

        lout=TextProcessor.eng_to_float(self.lout)/1e-9
        rout=TextProcessor.eng_to_float(self.rout)/1e-3
        avp=TextProcessor.eng_to_float(self.avp)/1e-3
        f0=TextProcessor.eng_to_float(self.f0)

        lines=[]
        lines.append('%tuning script\n')        
        lines.append('\n')
        lines.append(f'addpath(\'{self.vr_tune_core_folder}\')')
        lines.append('\n')
        lines.append(f'%Parameters\n')
        lines.append(f'ph_count = {len(self.phs)} % count\n')
        lines.append(f'avp = {avp} % m-Ohms\n')
        lines.append(f'vin = {self.vin} % V\n')
        lines.append(f'vramp = {self.vramp} % V\n')
        lines.append(f'f0 = {f0} % f0 Hz\n')
        lines.append(f'pm = {self.pm} % deg\n')
        lines.append(f'lout = {lout} % nH\n')
        lines.append(f'rout = {rout} % m-Ohms\n')
        lines.append(f'vid = {self.vid} % V\n')
        lines.append(f'tstone_file=\'{tstone_file}\'\n')
        lines.append(f'vr_mod_file=\'\'\n')
        lines.append(f'comp_file=\'{comp_file}\'\n')

        lines.append(f'tune_vr(ph_count,avp,vin,vramp,f0,pm,lout,rout,vid,tstone_file,vr_mod_file,comp_file)')
        Io.create_text_file(fpath,lines)
    
    def load_comp_file(self,fpath):
        """Load a CSV file containing the Type III compensator parameters.
        and create a dictionary where the key is the parameter name and the value
        is the parameter value 

        :param fpath: path to the CSV file to be loaded
        :type fpath: str
        :return: dictionary containing the type III tuning parameters
        :rtype: dic[str]
        """
        data = {}        
        with open(fpath, newline='') as csvfile:            
            reader = csv.reader(csvfile)            
            next(reader)            
            for row in reader:                
                data[row[0]] = row[1]
        
        return data

class PSITerminationFile:
    """Class to handle Termination files for quick impedance profile
    """
    def __init__(self):        
        self.termination_df=pd.DataFrame()
        
    def get_port_list_from_psi_snp(self,fpath):
        """Get port list from a psi .snp file

        :param fpath: path to the .snp file
        :type fpath: str
        :return: list of ports
        :rtype: list[str]
        """
        fpath=os.path.abspath(fpath)        
        self.fpath=fpath             
        lines=[]        
        ports=[]
        with open(fpath) as f:            
            lines = f.readlines()[1:]  

        for i,line in enumerate(lines):                            
                if TextProcessor.match(line,'!'):
                    break
                line=line.replace('::','_').replace('! ','').replace('\n','')
                ports.append(line)                
        return ports
    def get_port_list_from_idem_cir(self,fpath):
        fpath=os.path.abspath(fpath)        
        self.fpath=fpath             
        lines=[]        
        ports=[]
        with open(fpath) as f:            
            lines = f.readlines()[13:]  

        for i,line in enumerate(lines):            
                
                if TextProcessor.match(line,'** '):
                    break
                line=line.replace('::','_').replace('**  ','').replace('\n','')
                ports.append(line)
        return ports
    def load_csv(self,termination_fpath):        
        #termination file is provided   
        termination_desc=[]
        with open(termination_fpath) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')            
            for row in csv_reader:
                termination_desc.append(row)
            self.termination_df=termination_desc
    
    def load_df(self,termination_df):        
        #termination file is provided   
        termination_df=termination_df.replace(np.nan,'',regex=True)      
        self.termination_df=termination_df

    def create_termination(self,model_fpath,termination_file=None):
        """Create a termination file based on a .snp file. The termination file
        is CSV format, where the 1st row is the header, the 1st column contains
        the port list, the 2nd column contains the termination and the 3rd column
        contains the termination count. Additionally there are two other columsn
        'R' and 'L' these are used to indicate for the parasitics of a non ideal
        capacitor model.
        If the output file path is not provided, the file will NOT created.

        :param model_fpath: path to the .snp file
        :type model_fpath: str
        :param termination_file: Output file path
        :type termination_file: str, optional
        :return: List containing the created termination information
        :rtype: list[str]
        """
        model_fpath=os.path.abspath(model_fpath)          
        
        ports=self.get_port_list_from_psi_snp(model_fpath)
        termination_desc=[]
        #termination_desc.append()

        #create the termination
        die_ports=[]
        skt_ports=[]
        vr_ports=[]
        mli_ports=[]
        for p in ports:      
            #clasify ports as die, skt,mli,vr,sp
            if TextProcessor.match(p,['*c4*','*die*','vout*']):
                if TextProcessor.match(p,['*vr*','*ph*','sw*']):
                    vr_ports.append(p)
                else:
                    die_ports.append(p)   
            elif TextProcessor.match(p,['*skt*']):
                skt_ports.append(p)   
            elif TextProcessor.match(p,['*vr*','*ph*','sw*']):
                vr_ports.append(p)
            elif TextProcessor.match(p,['*mli*']):
                mli_ports.append(p)
        
        if die_ports and skt_ports:
            print('Model identified as monolitic pkg based on port names')
            #pkg model detected
            for p in ports:
                if p in die_ports:
                    termination_desc.append([p,'1a_dis'])
                elif p in skt_ports:
                    termination_desc.append([p,'sc'])
                else:
                    termination_desc.append([p,'1uF'])  
                    
        elif vr_ports and skt_ports:
            print('Model identified as motherboard based on port names')
            #brd model detected
            for p in ports:
                if p in skt_ports:
                    termination_desc.append([p,'1a_dis','','',''])
                elif p in vr_ports:
                    termination_desc.append([p,'sc','','',''])  
                else:
                    termination_desc.append([p,'1uF','','',''])  
                    
        elif vr_ports and die_ports:            
            print('Model identified as FIVR based on port names')
            #FIVR
            for p in ports:
                if p in die_ports:
                    termination_desc.append([p,'1a_dis','','',''])
                elif p in vr_ports:
                    termination_desc.append([p,'sc','','',''])
                else:
                    termination_desc.append([p,'open','','',''])  
                    
        elif mli_ports and die_ports:            
            #Patch
            print('Model identified as PoINT(Patch) based on port names')
            for p in ports:
                if p in die_ports:
                    termination_desc.append([p,'1a_dis','','',''])
                elif p in mli_ports:
                    termination_desc.append([p,'sc','','',''])
                else:
                    termination_desc.append([p,'1uF','','',''])  
                    
        elif skt_ports and mli_ports:       
            print('Model identified as PoINT(Interposer) based on port names')
            #Int
            for p in ports:
                if p in mli_ports:
                    termination_desc.append([p,'1a_dis','','',''])
                elif p in skt_ports:
                    termination_desc.append([p,'sc','','',''])
                else:
                    termination_desc.append([p,'1uF','','',''])  
        else:
            print('Unknown model. Default termination file to be created')
            #not detected:
            if len(ports)==1:
                termination_desc.append([ports[0],'1a_dis','','',''])
            elif len(ports)==2:
                termination_desc.append([ports[0],'1a_dis','','',''])
                termination_desc.append([ports[1],'sc','','',''])
            elif len(ports)==3:
                termination_desc.append([ports[0],'1a_dis','','',''])
                termination_desc.append([ports[1],'1uF','','',''])
                termination_desc.append([ports[2],'sc','','',''])
            else:
                for i,p in enumerate(ports):
                    if i<len(ports)/3:
                        termination_desc.append([p,'1a_dis','','',''])
                    elif i>len(ports)*2/3:
                        termination_desc.append([p,'sc','','',''])  
                    else:
                        termination_desc.append([p,'1uF','','',''])       
        
        self.termination_df=pd.DataFrame(termination_desc,columns=['Port',
                                                           'Term','Qty','R','L'])
        if termination_file:
            termination_file=os.path.abspath(termination_file)  
            self.termination_df.to_csv(termination_file,index=False)  
        return termination_desc
        

    def text_for_ac_probe(self, termination_wildcard=['1a_dis']):
        """Return spice compatible text for probing nodes 
        :param termination_wildcard: keyword that indicates the termination type
        :type termination_wildcard: string or list of strings        
        :return: list of strings
        :rtype: list
        """
        lines=[]
        for _,row in self.termination_df.iterrows():            
            if TextProcessor.match(row['Term'],termination_wildcard):
                lines.append(f".probe ac vm({row['Port']})\n")
        return lines
    
    def text_for_short(self, termination_wildcard=['short','sc']):
        """Return spice compatible text to short nodes
        :param termination_wildcard: keyword that indicates the termination type
        :type termination_wildcard: string or list of strings        
        :return: list of strings
        :rtype: list
        """
        lines=[]
        for _,row in self.termination_df.iterrows():
            if TextProcessor.match(row['Term'],termination_wildcard):
            #if(row[1]==termination_to):                                
                lines.append(f"v_cc_{row['Port']} {row['Port']} 0 0\n")
        return lines
    
    def text_for_open(self,termination_wildcard=['open','oc']):
        """Return spice compatible text to open nodes
        :param termination_wildcard: keyword that indicates the termination type
        :type termination_wildcard: string or list of strings        
        :return: list of strings
        :rtype: list
        """
        lines=[]
        for _,row in self.termination_df.iterrows():
            #if(row[1]==termination_to): 
            if TextProcessor.match(row['Term'],termination_wildcard):
                lines.append(f"r_oc_{row['Port']} {row['Port']} 0 1e6\n")
        return lines
    
    def text_for_ideal_cap(self):
        """Return spice compatible text to terminate ports with 1uF cap
        :param termination_wildcard: keyword that indicates the termination type
        :type termination_wildcard: string or list of strings        
        :return: list of strings
        :rtype: list
        """
        lines=[]
        for _,row in self.termination_df.iterrows():
            term=row['Term'].strip()
            Qty=row['Qty']
            R=row['R']
            L=row['L']
            if TextProcessor.isCapacitance(term) or TextProcessor.isnumeric(term):
                if R or L:
                    if not R:
                        R='1u'
                    if not L:
                        R='1f'
                    if not Qty:
                        Qty='1'
                    lines.append(f"x_{row['Port']}_{row['Term']} {row['Port']} \
0 cap_1leg C={row['Term']} R={R} L={L} NCAPS={Qty}\n")
                else:
                    if Qty:
                        lines.append(f"c_{row['Port']}_{row['Term']} {row['Port']} \
0 '{row['Term']}*{Qty}'\n")
                    else:
                        lines.append(f"c_{row['Port']}_{row['Term']} {row['Port']} \
0 {row['Term']}\n")
        return lines
    
    def text_for_cap_model(self,caps_folder=None):
        """Return Spice compatible text for capacitor instances asociated to a 
        termination file
        :param termination_wildcard: keyword that indicates the termination type
        :type termination_wildcard: string or list of strings        
        :return: list of strings
        :rtype: list
        """
        if caps_folder is None:
            caps_folder=os.curdir
        lines=[]
        cap_lines=[]
        inc_lines=set()
        caps_folder=os.path.abspath(caps_folder)
        xnames=[]
        for index,row in self.termination_df.iterrows():
            file_extension = pathlib.Path(row['Term']).suffix
            #if file_extension in termination_wildcard:                                                    
            if(file_extension=='.sp' or file_extension=='.cir' or file_extension=='.inc'):  
                #there is a cap termination for this node
                #add the include 
                #Get path for the cap:
                cap_path=Io.find_in_folder(caps_folder,row['Term'],True)
                if  cap_path:
                    cap_path=cap_path[0]
                else:
                   EventLogger.raise_value_error("File not found:"+row['Term']+"in caps_folder" ) 
                #
                
                inc_lines.add(f'.inc {cap_path}\n')                
                #create the cap instance
                sub=self.get_model_name(cap_path)
                xname=f"x_cap_{index}_{row['Port']}"                    
                if len(row)>2 and row[2]:
                    cap_lines.append(f"{xname} {row['Port']} 0 {sub} NCAPS = {row['Qty']}\n")
                else:
                    cap_lines.append(f"{xname} {row['Port']} 0 {sub}\n")
        #combine the lncludes and the instances lines
        for row in inc_lines:
            lines.append(row)
        lines+=cap_lines
        return lines
    
    def text_for_1a_dis(self,termination_wildcard=['1a_dis']):
        """Return Spice compatible text for 1A distributed across nodes
        :param termination_wildcard: keyword that indicates the termination type
        :type termination_wildcard: string or list of strings        
        :return: list of strings
        :rtype: list
        """
        lines=[]
        lines_with_1a_dis=[]
        numnodes=0
        for _,row in self.termination_df.iterrows():
            #if(row[1]==termination_wildcard):                                
            if TextProcessor.match(row[1],termination_wildcard):
                numnodes+=1
                lines_with_1a_dis.append(f"I_cc_{row['Port']} {row['Port']} 0 ac=\'1/num_nodes\' \n")        
        lines.append(f'.par num_nodes={numnodes}\n')
        lines+=lines_with_1a_dis
        return lines
    
    def get_ports(self):
        """Return the ports asociated with the termination file
        :param termination_desc: list with the nodes and the terminations
        :type termination_desc: list
        :return: Node list
        :rtype: list
        """
        ports=self.termination_df['Port'].tolist()        
        return ports    
    
    def get_model_name(self,filename):
        """Given a spice compatible include or .cir file, this fuction will 
        return the 1st  subcircuit name in that file. 

        :param filename: path to the file
        :type filename: string
        :return: subcircuit name
        :rtype: string
        """
        lines=[]
        sub=''
        with open(filename) as f:
            lines = f.readlines()
            
        for line in lines:
            parts=line.split()            
            if(len(parts)>1):                               
                if(parts[0].lower()=='.subckt'):
                    sub=parts[1]    
        return sub


class HspiceDeck:
    """Class to build Hspice decks
    """
    def __init__(self,case='',deck_path=os.curdir,traceback_limit=0):
        self.deck_path=os.path.abspath(deck_path)
        self.case=case                
        self.local_paths={}
        self.init_local_paths(case)
        


        #debug
        EventLogger.int_log(deck_path+'/log/')                
        EventLogger.traceback_limit=traceback_limit        
        EventLogger.info('HSPICE Deck Builder launched')
        EventLogger.info('Deck folder: '+ os.path.abspath(deck_path))     

        
        
        self.sim_option_line=['.option POST=2  POST_VERSION = 2001 PROBE\n']
        self.ac_analysis_line=['.ac dec 100 1 2e+09\n']
        self.lf_analysis_line=['.tran 1n 1m\n']
        self.hf_analysis_line=['.tran 1p 5u\n']        

        self.spice_models={}
        self.die_instances={}
        self.vr_instance=None

        
        self.lf_icct_groups={}
        
        self.hf_icct_groups={}


        self.psi_models={}
        self.brd_instance=None
        self.pkg_instance=None

        self.pkg_patch_instance=None
        self.pkg_int_instance=None
        
        

        self.attd_cap_models={}
        self.brd_attd_cap_instances={}
        self.pkg_attd_cap_instances={}
        self.attd_cap_groups={}


        self.rl_conn_models={}

        self.skt_groups={}
        self.mli_groups={}
        self.c4_groups={}

        #1A distributed
        self.ac_1a_ports=[]
        #probes
        self.probe_v_tran_ports={}
        self.probe_v_ac_ports={}
        
        self.short_ports=[]

        self.lin_ports=[]

        self.include_lines=[]


        self.die_params=[]
        
        
        self.ph_count=0

        
        self.lin_z0=0.1
        

        self.pkg_id='pkg_model'
        self.brd_id='brd_model'
        self.analysis_type='analysis_type'


        self.tstones=[]
        self.tstone_ins=[]

        #set initial Top global parameters.
        self.glob_params=OrderedDict()
        self.set_analysis_type(AnalysisType.ZF)
        self.set_pkg_model_type(PsiModelType.MACRO1)
        self.set_brd_model_type(PsiModelType.MACRO1)

        #variable for spice compatible text that will be placed on the deck
        self.user_data=None

        self.header_for_cap_map_by_comp_model=['PowerSI capacitor model name ',
        'SPICE model name/file name']
        self.header_for_cap_map_by_port=['PowerSI port',
        'SPICE model name/file name','NCAP']

        self.header_for_die_map=['PowerSI port',
        'die_instance_1','die_instance_2']

        self.header_for_skt_map=['BRD PowerSI port','PKG PowerSI port',
        'p_count','n_count','pin_r','pin_l']
        
        self.vr_info=None        

        self.main_files=[]



    
    def init_local_paths(self,case=''):
        self.case=case    
        self.local_paths['brd_mod_folder']='/brd/'
        self.local_paths['pkg_mod_folder']='/pkg/'
        self.local_paths['pkg_patch_mod_folder']='/pkg/patch/'
        self.local_paths['pkg_int_mod_folder']='/pkg/int/'
        self.local_paths['cap_mod_folder']='/caps/'
        self.local_paths['vr_mod_file']='/vr/vrstavggen.inc'
        self.local_paths['tlvr_mod_file']='/vr/tlvrstavggen.inc'
        self.local_paths['rl_conn_mod_file']='/connectors/rl_conn.inc'

        #self.local_paths['lf_icct_mod_file']='/icct/gen_pulse.inc'
        self.local_paths['icct_folder']='/icct'
        #case dependant
        self.local_paths['die_ins_file']=f'/die_call/die_call.inc'
        self.local_paths['c4_ins_file']=f'/c4_call/c4_call.inc'
        self.local_paths['pkg_ins_file']=f'/pkg_call/pkg_call.inc' 
        self.local_paths['pkg_tstone_ins_file']=f'/pkg_call/pkg_call_sparam.inc' 

        self.local_paths['pkg_patch_ins_file']=f'/pkg_call/pkg_patch_call.inc' 
        self.local_paths['pkg_patch_tstone_ins_file']=f'/pkg_call/pkg_patch_call_sparam.inc' 
        self.local_paths['pkg_int_ins_file']=f'/pkg_call/pkg_int_call.inc' 
        self.local_paths['pkg_int_tstone_ins_file']=f'/pkg_call/pkg_int_call_sparam.inc' 


        self.local_paths['brd_ins_file']=f'/brd_call/brd_call.inc'
        self.local_paths['brd_tstone_ins_file']=f'/brd_call/brd_call_sparams.inc'
        self.local_paths['mli_ins_file']=f'/mli_call/mli_call.inc'         
        self.local_paths['skt_ins_file']=f'/skt_call/skt_call.inc'         
        self.local_paths['cap_ins_file']=f'/cap_call/cap_call.inc' 
        self.local_paths['one_a_ac_file']=f'/1a_ac/1a_ac.inc'
        self.local_paths['main_zf_file']=f'/main_zf/main_zf.sp'
        self.local_paths['main_s_s_zf_file']=f'/main_zf/main_s_zf.sp'
        self.local_paths['main_m_s_zf_file']=f'/main_zf/main_brd_idem_pkg_spar_zf.sp'
        self.local_paths['main_s_m_zf_file']=f'/main_zf/main_brd_spar_pkg_idem_zf.sp'
        self.local_paths['main_tran_lf_file']=f'/main_tran_lf/main_tran_lf.sp'
        self.local_paths['main_tran_hf_file']=f'/main_tran_hf/main_tran_hf.sp'
        self.local_paths['main_bode_file']=f'/main_bode/main_bode.sp'                
        self.local_paths['main_lin_file']=f'/main_lin/main_lin.sp'        
        self.local_paths['main_s_s_lin_file']=f'/main_lin/main_spar_lin.sp'        
        self.local_paths['main_m_s_lin_file']=f'/main_lin/main_brd_idem_pkg_spar_lin.sp'        
        self.local_paths['main_s_m_lin_file']=f'/main_lin/main_brd_spar_pkg_idem_lin.sp'        

        self.local_paths['tran_vprobe_file']=f'/probes/tran_v.inc'
        self.local_paths['ac_vprobe_file']=f'/probes/ac_v.inc'
        self.local_paths['lf_icct_ins_file']=f'/icct_call/lf_icct.inc'        
        self.local_paths['hf_icct_ins_file']=f'/icct_call/hf_icct.inc'
        self.local_paths['main_vr_tune_file']=f'/main_vr_tune/main_tune.sp'


        #for templates
        self.local_paths['icct_template']=f'/templates/icct'
        


    @property
    def brd_mod_folder(self):
        return self.deck_path+self.local_paths['brd_mod_folder']        
    
    @property
    def pkg_mod_folder(self):
        return self.deck_path+self.local_paths['pkg_mod_folder']        

    @property
    def pkg_patch_mod_folder(self):
        return self.deck_path+self.local_paths['pkg_patch_mod_folder']        

    @property
    def pkg_int_mod_folder(self):
        return self.deck_path+self.local_paths['pkg_int_mod_folder']        

    @property
    def cap_mod_folder(self):
        return self.deck_path+self.local_paths['cap_mod_folder']        
    
    #@property
    #def vr_mod(self):
    #    return self.deck_path+self.local_paths['vr_mod_file']        
    #
    #@property
    #def tlvr_mod(self):
    #    return self.deck_path+self.local_paths['tlvr_mod_file']        
    
    @property
    def rl_conn_mod_file(self):
        return self.deck_path+self.local_paths['rl_conn_mod_file']        
    
    #@property
    #def lf_icct_mod_file(self):
    #    return self.deck_path+self.local_paths['lf_icct_mod_file']        
    
    @property
    def icct_folder(self):
        return self.deck_path+self.local_paths['icct_folder']        


    @property
    def vr_mod_file(self):
        base_file_path=self.deck_path+self.local_paths['vr_mod_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.ph_count}ph')        
    @property
    def tlvr_mod_file(self):
        base_file_path=self.deck_path+self.local_paths['tlvr_mod_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.ph_count}ph')        
    
    @property
    def die_ins_file(self):
        base_file_path=self.deck_path+self.local_paths['die_ins_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def c4_ins_file(self):
        base_file_path=self.deck_path+self.local_paths['c4_ins_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def pkg_ins_file(self):
        base_file_path=self.deck_path+self.local_paths['pkg_ins_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def pkg_tstone_ins_file(self):
        base_file_path=self.deck_path+self.local_paths['pkg_tstone_ins_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    

    @property
    def pkg_patch_ins_file(self):
        base_file_path=self.deck_path+self.local_paths['pkg_patch_ins_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def pkg_patch_tstone_ins_file(self):
        base_file_path=self.deck_path+self.local_paths['pkg_patch_tstone_ins_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def pkg_int_ins_file(self):
        base_file_path=self.deck_path+self.local_paths['pkg_int_ins_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def pkg_int_tstone_ins_file(self):
        base_file_path=self.deck_path+self.local_paths['pkg_int_tstone_ins_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')


    @property
    def brd_ins_file(self):
        base_file_path=self.deck_path+self.local_paths['brd_ins_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def brd_tstone_ins_file(self):
        base_file_path=self.deck_path+self.local_paths['brd_tstone_ins_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def mli_ins_file(self):
        base_file_path=self.deck_path+self.local_paths['mli_ins_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def skt_ins_file(self):
        base_file_path=self.deck_path+self.local_paths['skt_ins_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def cap_ins_file(self):
        base_file_path=self.deck_path+self.local_paths['cap_ins_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def onea_ac_file(self):
        base_file_path=self.deck_path+self.local_paths['one_a_ac_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')

    @property
    def main_zf_file(self):
        base_file_path=self.deck_path+self.local_paths['main_zf_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def main_s_s_zf_file(self):
        base_file_path=self.deck_path+self.local_paths['main_s_s_zf_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def main_s_m_zf_file(self):
        base_file_path=self.deck_path+self.local_paths['main_s_m_zf_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')
        
    @property
    def main_m_s_zf_file(self):
        base_file_path=self.deck_path+self.local_paths['main_m_s_zf_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def main_tran_lf_file(self):
        base_file_path=self.deck_path+self.local_paths['main_tran_lf_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def main_tran_hf_file(self):
        base_file_path=self.deck_path+self.local_paths['main_tran_hf_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')

    @property
    def main_bode_file(self):
        base_file_path=self.deck_path+self.local_paths['main_bode_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def main_lin_file(self):
        base_file_path=self.deck_path+self.local_paths['main_lin_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def main_s_s_lin_file(self):
        base_file_path=self.deck_path+self.local_paths['main_s_s_lin_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')

    @property
    def main_m_s_lin_file(self):
        base_file_path=self.deck_path+self.local_paths['main_m_s_lin_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')

    @property
    def main_s_m_lin_file(self):
        base_file_path=self.deck_path+self.local_paths['main_s_m_lin_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')

    @property
    def main_vr_tune_file(self):
        base_file_path=self.deck_path+self.local_paths['main_vr_tune_file']
        base_file_path=os.path.abspath(base_file_path)
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def vr_tune_file_s2p(self):
        return os.path.abspath(Io.update_file_extension(self.main_vr_tune_file,'.s2p'))
    
    @property
    def vr_tuning_script(self):
        return os.path.abspath(Io.update_file_extension(self.main_vr_tune_file,'.m'))
    
    @property
    def vr_tune_compfile(self):
        return os.path.abspath(Io.update_file_extension(self.main_vr_tune_file,'_comp.csv'))
        
    
    
    
    @property
    def tran_vprobe_file(self):
        base_file_path=self.deck_path+self.local_paths['tran_vprobe_file']
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def ac_vprobe_file(self):
        base_file_path=self.deck_path+self.local_paths['ac_vprobe_file']
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def lf_icct_ins_file(self):
        base_file_path=self.deck_path+self.local_paths['lf_icct_ins_file']
        return Io.custom_file_path(base_file_path,f'_{self.case}')
    
    @property
    def hf_icct_ins_file(self):
        base_file_path=self.deck_path+self.local_paths['hf_icct_ins_file']
        return Io.custom_file_path(base_file_path,f'_{self.case}')

    @property
    def icct_folder_template(self):        
        return os.path.abspath(os.path.dirname(__file__)+self.local_paths['icct_template'])
        
    
    def init_user_data(self):
        self.user_data=\
"""                
*SKT
.param skt_pin_r='30m'
.param skt_pin_l='3n'
*C4
.param c4_pin_r='1.92m'
.param c4_pin_l='9.7p'
*VR
.param
+vid = '1.1'
+avp = '0'
+lout = '100n'
+rout = '0.29m'
+ r1 = '4.000000k'
+ r2 = '2.983821k'
+ r3 = '0.037528k'
+ c1 = '37.076077p'
+ c2 = '3.951850n'
+ c3 = '2.920503n'

"""

    def set_lf_sim_time(self,step='1n',end='1m'):
        """set the low frequency simulation time parameters

        :param step: simulation step, defaults to '1n'
        :type step: str, optional
        :param end: simulation end time, defaults to '1m'
        :type end: str, optional
        """
        self.lf_analysis_line=[f'.tran {step} {end}\n']

    def set_hf_sim_time(self,step='1p',end='5u'):
        """set the high frequency simulation time parameters

        :param step: simulation step, defaults to '1n'
        :type step: str, optional
        :param end: simulation end time, defaults to '1m'
        :type end: str, optional
        """
        self.hf_analysis_line=[f'.tran {step} {end}\n']

        
    def update_user_data_param(self,param_name,param_value):  
                
        if not param_value:
            #skip parameters not defined
            return
        # Split the SPICE code into a list of lines
        if isinstance(self.user_data,str):
            lines = self.user_data.split("\n")
        else:
            lines =self.user_data

        # Initialize a flag to indicate if the parameter was found
        found = False        
        # Iterate over the lines of the SPICE code
        for i, line in enumerate(lines):
            # Check if the line starts with the parameter name
            match = re.search(param_name+r"\s*=\s*[^,\s]*", line)
            if match:                
                # Update the parameter value
                new_line = match.string.replace(match.group(), param_name + " = '" + param_value + "'")
                lines[i] = new_line
                found = True                
                break

        if not found:
            lines.append("+" + param_name + " = '" + param_value + "'")

        self.user_data=lines
        
    def text_for_sim_options(self):        
        lines=[]
        lines+=self.text_for_comment('Simulation options')
        lines+=self.sim_option_line
        return lines
    
    def text_for_analysis(self):

        lines=[]
        lines+=self.text_for_commented_tittle('Analysis type')

        lines+=self.text_for_if(f'{self.analysis_type} == {AnalysisType.BODE.value}')
        lines+=self.text_indent(self.text_for_comment('Bode analysis'))
        lines+=self.text_indent(self.ac_analysis_line)        
        
        lines+=self.text_for_elseif(f'{self.analysis_type} == {AnalysisType.ZF.value}')
        lines+=self.text_indent(self.text_for_comment('Z(F) analysis'))
        lines+=self.text_indent(self.ac_analysis_line)

        lines+=self.text_for_elseif(f'{self.analysis_type} == {AnalysisType.LF.value}')
        lines+=self.text_indent(self.text_for_comment('Transient LF analysis'))
        lines+=self.text_indent(self.lf_analysis_line)

        lines+=self.text_for_elseif(f'{self.analysis_type} == {AnalysisType.HF.value}')
        lines+=self.text_indent(self.text_for_comment('Transient HF analysis'))
        lines+=self.text_indent(self.hf_analysis_line)

        lines+=self.text_for_elseif(f'{self.analysis_type} == {AnalysisType.LIN.value}')
        lines+=self.text_indent(self.text_for_comment('LIN analysis'))
        lines+=self.text_indent(self.ac_analysis_line)        

        lines+=self.text_for_endif()
        return lines
    
    def text_for_bode_variable(self):

        lines=[]
        lines+=self.text_for_commented_tittle('Bode')

        lines+=self.text_for_if(f'{self.analysis_type} == {AnalysisType.BODE.value}')
        lines+=self.text_indent(self.text_for_param('bode','1'))
        
        lines+=self.text_for_else()
        lines+=self.text_indent(self.text_for_param('bode','0'))        
        lines+=self.text_for_endif()
        return lines
    def text_for_loading_conditions(self,start):

        lines=[]
        lines+=self.text_for_commented_tittle('Loading conditions')        
        lines+=self.text_for_if(f'{self.analysis_type} == {AnalysisType.ZF.value}')
        lines+=self.text_indent(self.text_for_comment('1A AC distributed'))
        if self.ac_1a_ports:
            lines+=self.text_indent(self.text_for_include(self.onea_ac_file,start))

        lines+=self.text_for_elseif(f'{self.analysis_type} == {AnalysisType.LF.value}')
        lines+=self.text_indent(self.text_for_comment('LF icct'))
        if self.lf_icct_groups:
            #lines+=self.text_indent(self.text_for_include(self.lf_icct_mod_file,
            #start))
            lines+=self.text_indent(self.text_for_lf_icct_mods(start))
            lines+=self.text_indent(self.text_for_include(self.lf_icct_ins_file,
            start))

        lines+=self.text_for_elseif(f'{self.analysis_type} == {AnalysisType.HF.value}')        
        lines+=self.text_indent(self.text_for_comment('HF icct'))
        if self.hf_icct_groups:
            lines+=self.text_indent(self.text_for_hf_icct_mods(start))
            lines+=self.text_indent(self.text_for_include(self.hf_icct_ins_file,
            start))

        lines+=self.text_for_endif()
        return lines
        
    def text_for_ac_analysis(self):
        lines=[]
        lines+=self.text_for_comment('AC analysis')
        lines+=self.ac_analysis_line
        return lines
        

    def text_for_lf_analysis(self):
        lines=[]
        lines+=self.text_for_comment('Transient LF analysis')
        lines+=self.lf_analysis_line
        return lines

    def text_for_hf_analysis(self):
        lines=[]
        lines+=self.text_for_comment('Transient HF analysis')
        lines+=self.hf_analysis_line
        return lines

    def text_for_insgroup_iprobed(self,ins_group,probe_port_index=0):                
        lines=[]
        lines+=self.text_for_comment("instances for " +ins_group.name)
        
        intances=ins_group.instances
        probing_ports=[]               
        mid_ports=[]
        for ins_name in intances:
            ins=intances[ins_name]
            #probe current
            ports_updated=ins.ports.copy()
            probing_ports.append(ports_updated[probe_port_index])
            mid_port='mid1_'+ins_group.name+'_'+ports_updated[probe_port_index]                        
            mid_ports.append(mid_port)                

            ports_updated[probe_port_index]=mid_port
            lines+=self.text_for_inline_instance(ins.name,ports_updated,
            ins.model.name,ins.params)

        #i probes
        v_source_names=[]
        lines+=self.text_for_comment("current probe")
        for i in range(len(probing_ports)):
            port=probing_ports[i]
            mid_port=mid_ports[i]
            name='v_'+ port+ins_group.name 
            v_source_names.append(name)                        
            lines.append(f'{name} {port} {mid_port} 0\n')        
        #itot
        lines+=self.text_for_comment("group current for "+ ins_group.name)
        par_line=f".probe {ins_group.get_iprobe_name()} = par('"
        for name in v_source_names:
            if name!=v_source_names[-1]:
                par_line+=f'i({name})+'
            else:
                par_line+=f'i({name})'
        par_line+="')\n"
        if len(par_line)>4000:
            EventLogger.raise_warning('current probe length exceeds hspice\
                                       limit for '+ins_group.name)
            lines.append('* Probe automatically commented. length exceed hspice limit\n')
            lines.append('*'+par_line)
        else:
            lines.append(par_line)
        return lines
    
    def text_for_insgroups_iprobed(self,insgroups,itot_probename='itot'):
        lines=[]
        itots=[]
        for group_name in insgroups:              
            itots.append(insgroups[group_name].get_iprobe_name())
            lines+=self.text_for_insgroup_iprobed(insgroups[group_name])

        if len(itots)>1:
            lines+=self.text_for_comment("Total current")        
            line=f".probe {itot_probename}=par('"
            for itot in itots:
                if itot!=itots[-1]:
                    line+=itot+'+'
                else:
                    line+=itot
            line+="')\n"
            lines.append(line)
        return lines
        
    def text_for_commented_tittle(self,section_name='Section',n_asterisk=3):
        """Return a list of string to represent a commented tittle in SPICE language.

        :param comment: The title, defaults to 'Section'
        :type comment: str, optional
        :param n_asterisk: The number of times to repeat the '*' character before and after the section name.
        :type n_asterisk: int, optional
        :return: list of strings
        :rtype: List[str]
        """        
        lines=[]
        char='*'
        lines.append(f'{char*(n_asterisk+len(section_name)+8)}''\n')
        lines.append(f'{char*n_asterisk} {section_name} {char*n_asterisk} \n')
        lines.append(f'{char*(n_asterisk+len(section_name)+8)}''\n')
        return lines

    def text_for_comment(self,comment='',n_asterisk=3):
        """Return a list of strings with a comment in SPICE language.

        :param comment: The comment text, defaults to ''
        :type comment: str, optional
        :param n_asterisk: The number of times to repeat the '*' character before and after the commenct.
        :type n_asterisk: int, optional
        :return: A list of strings with the commented section in SPICE language.
        :rtype: List[str]
        """

        char='*'
        lines=[]
        lines.append(f'{char*n_asterisk} {comment} {char*n_asterisk}\n')
        return lines    
        
    def text_for_header(self,header_comment='Deck generated by thinkPI'):
        """Create Spice compatible header 

        :param deck_name: Header comment, defaults to 'Deck generated by thinkPI'
        :type deck_name: str, optional
        :return: _description_
        :rtype: _type_
        """
        return self.text_for_commented_tittle(header_comment)
    def text_for_param(self,param,value):
        lines=[]
        lines.append(f'.param {param} = \'{value}\'\n')
        return lines    
    def text_for_sim_settings_ac(self, points=20,
                                 f_start=10, f_end=200e6):
        """Create Spice compatible AC simulation settings

        :param points: points, defaults to 20
        :type points: int, optional
        :param f_start: start frequency, defaults to 10
        :type f_start: float, optional
        :param f_end: end frequency, defaults to 200e6
        :type f_end: float, optional
        :return: list of strings
        :rtype: list
        """
        lines=[]
        lines.append('*********Simulation definition*********\n')
        #lines.append('.option probe post\n')
        lines.append('.option probe POST=2  POST_VERSION = 2001\n')
        
        lines.append(f'.ac dec {points} {f_start} {f_end}\n')        
        return lines 

    def text_for_sim_settings_tran(self,t_start=0.1e-9,t_stop=1e-3):
        """
        """
        lines=[]
        lines.append('*********Simulation definition*********\n')
        #lines.append('.option probe post\n')
        lines.append('.option probe POST=2  POST_VERSION = 2001\n')
        lines.append(f'.tran {t_start} {t_stop}\n')        
        return lines 
        
    def text_for_tstonefile_include(self,model_name, model_path,start=None):
        """Return Spice compatible text to include a tstone file

        :param model_name: model name
        :type model_name: string
        :param model_path: model path
        :type model_path: string
        :return: list of strings
        :rtype: list
        """
        if not start:
            model_path=os.path.abspath(model_path)
        else:
            model_path=os.path.relpath(model_path,start)
        lines=[]
        lines.append(f'.model {model_name}	s	tstonefile = \'{model_path}\'\n')
        return lines
        
    def text_for_tstone_instance(self,instance_name, model_name, node_list):
        """Return Spice compatible text for tstone instance

        :param instance_name: Instance Name
        :type instance_name: string
        :param model_name: model name
        :type model_name: string
        :param node_list: node list
        :type node_list: list
        :return: list of strings_
        :rtype: lists
        """
        lines=[]
        lines.append(f's_{instance_name}\n')        
        for node in node_list:        
            lines.append(f'+{node}\n')
        #lines.append(f'+0\n')
        lines.append(f'+mname = {model_name}\n')
        lines.append('\n') 
        return lines

    
    def text_for_ac_probe_from_termination_desc(self, termination_to_probe,
        termination_desc):
        """Return spice compatible text for probing nodes 

        :param termination_to_probe: keyword that indicates the probing nodes
        :type termination_to_probe: string
        :param termination_desc: list of nodes and terminatios
        :type termination_desc: list
        :return: list of strings
        :rtype: list
        """

        lines=[]
        for row in termination_desc:
            if(row[1]==termination_to_probe):                
                lines.append(f'.probe ac vm({row[0]})\n')
                
        return lines

    def text_for_short_from_termination_desc(self, termination_to_short,
        termination_desc):
        """Return spice compatible text to short nodes

        :param termination_to_short: keyword for short_circuit
        :type termination_to_cc: string
        :param termination_desc: list of nodes and terminations
        :type termination_desc: list
        :return: list of strings
        :rtype: list
        """

        lines=[]
        for row in termination_desc:
            if(row[1]==termination_to_short):                                
                lines.append(f'v_cc_{row[0]} {row[0]} 0 0\n')
        return lines
    
    def text_for_open_from_termination_desc(self,termination_to_cc,
        termination_desc):
        """Return spice compatible text to open nodes

        :param termination_to_cc: keyword for open_circuits
        :type termination_to_cc: string
        :param termination_desc: list of nodes and terminations
        :type termination_desc: list
        :return: text ready to be added to a spice file
        :rtype: list
        """

        lines=[]
        for row in termination_desc:
            if(row[1]==termination_to_cc):                                
                lines.append(f'r_oc_{row[0]} {row[0]} 0 1e6\n')
        return lines
    
    def text_for_1uF_from_termination_desc(self,termination_to,
        termination_desc):
        """Return spice compatible text to terminate ports with 1uF cap

        :param termination_to: keyword for to identify ports to terminate
        :type termination_to: string
        :param termination_desc: list of ports and terminations
        :type termination_desc: list
        :return: text ready to be added to a spice file
        :rtype: list
        """

        lines=[]
        for row in termination_desc:
            if(row[1]==termination_to):                                
                lines.append(f'c_1u_{row[0]} {row[0]} 0 1u\n')
        return lines

    def text_for_caps_from_termination_desc(self,termination_desc,caps_path):
        """Return Spice compatible text for capacitor instances asociated to a 
        termination file

        :param termination_desc: List with the ports and the desired termination
        :type termination_desc: list
        :param caps_path: path to the caps models
        :type caps_path: string
        :return: text ready to be added to a spice file
        :rtype: list
        """
        lines=[]
        cap_lines=[]
        inc_lines=set()
            
        for row in termination_desc:
            file_extension = pathlib.Path(row[1]).suffix
            if(file_extension=='.sp' or file_extension=='.cir' or file_extension=='.inc'):  
                #there is a cap termination for this node
                #add the include 
                inc_lines.add(f'.inc {caps_path}/{row[1]}\n')                
                #create the cap instance
                
                sub=self.get_model_name(f'{caps_path}/{row[1]}')
                if len(row>2):
                    cap_lines.append(f'x_cap_{row[0]} {row[0]} 0 {sub} NCAP = {row[2]}\n')
                else:
                    cap_lines.append(f'x_cap_{row[0]} {row[0]} 0 {sub}\n')
        
        #combine the lncludes and the instances lines
        for row in inc_lines:
            lines.append(row)
        lines+=cap_lines
        return lines
        
    def text_for_1a_dis_from_termination_desc(self,termination_to_1a_dis,
        termination_desc):
        """Return Spice compatible text for 1A distributed across nodes

        :param termination_to_1a_dis: text that represent 1A distrubted
        :type termination_to_1a_dis: string
        :param termination_desc: List with the ports and the desired termination
        :type termination_desc: list
        :return: Text ready to be added to a spice file
        :rtype: list
        """

        lines=[]
        lines_with_1a_dis=[]
        numnodes=0
        for row in termination_desc:
            if(row[1]==termination_to_1a_dis):                                
                numnodes+=1
                lines_with_1a_dis.append(f'I_cc_{row[0]} {row[0]} 0 ac=\'1/num_nodes\' \n')        
        lines.append(f'.par num_nodes={numnodes}\n')
        lines+=lines_with_1a_dis
        return lines
        
    def text_for_end_file(self):
        """Return Spice compatible text to indicate the end of a file

        :return: Text ready to be added to a spice file
        :rtype: list
        """
        lines=[]
        lines+=self.text_for_newline()
        lines.append('.end')        
        return lines
        
    def text_for_newline(self):
        """Return Spice compatible text for a new line

        :return: Text ready to be added to a spice file
        :rtype: list
        """
        lines=[]
        lines.append('\n')
        return lines
            
    def text_for_include(self,inc_file,start=None):
        lines=[]  
        if not inc_file:
            return lines

        if not start:
            inc_file=os.path.abspath(inc_file)
        else:
            inc_file=os.path.relpath(inc_file,start)
        
              

        already_included_file=[]
        if inc_file not in self.include_lines:
            self.include_lines.append(inc_file)        
            lines.append(f'.inc \'{inc_file}\'\n')
        elif inc_file not in already_included_file:
            already_included_file.append(inc_file)            
        return lines
    
    def text_for_inline_instance(self,insname, ports,modname,params):
        lines=[]

        line=f'x_{insname} ' 
        for p in ports:
            line+= p+' '
        line+=modname+ ' '
        if isinstance(params,str):
            line+=params
        elif params == None:
            pass
        else:
            for par_name in params:
                par_value=params[par_name]                    
                line+=f'{par_name} = \'{par_value}\' '            
        line+='\n'
        lines.append(line)        
        return lines
    def text_for_circuit_instance(self,instance_name,model_name,node_list):
        """Return Spice compatible text to create an circuit instance

        :param instance_name: Instance name
        :type instance_name: string
        :param model_name: Model name
        :type model_name: string
        :param node_list: List of nodes
        :type node_list: list
        :return: Text ready to be added to a spice file
        :rtype: list
        """
        lines=[]
        lines.append(f'x_{instance_name}\n')        
        for node in node_list:        
            lines.append(f'+{node}\n')        
        lines.append(f'+{model_name}\n')
        lines.append('\n') 
        return lines
    
    def text_for_lin_ports(self,snp_file_path,start,model_name='pdn'):
        
        if not start:
            snp_file_path=os.path.abspath(snp_file_path)
        else:
            snp_file_path=os.path.relpath(snp_file_path,start)

        lines=[]     
        lines+=self.text_for_comment('Lin Ports')
        for i,node in enumerate(self.lin_ports):            
            lines.append(f'port{i+1} {node} 0  port = {i+1} zo={self.lin_z0} dc=1 ac=1\n')
        lines.append(f'.LIN sparcalc=1 modelname="{model_name}" filename="{snp_file_path}"\n')
        lines.append(f'+format=touchstone noisecalc=0 gdcalc=0 dataformat=RI SPARDIGIT=18')
        lines.append('\n') 
        return lines
    
    def text_for_vr_ins(self,bode='0'):
        lines=[]                
        lines+=self.vr_instance.to_text(CircuitInstanceTextFormat.PAR_MULTI_LINE)
        return lines

    def create_text_file(self,file_path,lines):        
        """Save the deck file

        :param out_deck_filename: target filename
        :type out_deck_filename: str
        :param lines: text to be added in the file
        :type lines: list
        """
        folder_file = os.path.split(file_path)
        self.create_folder(folder_file[0])

        with open(file_path, 'w') as f:
            for line in lines:        
                f.write(line)

    def Read(self,filename):
        """Read a file

        :param filename: File path
        :type filename: str
        :return: text in the file
        :rtype: list
        """
        lines=[]
        
        with open(filename,'r') as f:
            lines = f.readlines()
        return lines

    def create_folder(self,path):
        if not os.path.exists(path):
            os.makedirs(path)
    
	
    def get_port_list_from_psi_snp(self,fpath):
        fpath=os.path.abspath(fpath)        
        self.fpath=fpath             
        lines=[]        
        ports=[]
        with open(fpath) as f:            
            lines = f.readlines()[1:]  

        for i,line in enumerate(lines):                            
                if TextProcessor.match(line,'!'):
                    break
                line=line.replace('::','_').replace('! ','').replace('\n','')
                ports.append(line)                
        return ports
    def get_port_list_from_idem_cir(self,fpath):
        fpath=os.path.abspath(fpath)        
        self.fpath=fpath             
        lines=[]        
        ports=[]
        with open(fpath) as f:            
            lines = f.readlines()[13:]  

        for i,line in enumerate(lines):            
                
                if TextProcessor.match(line,'** '):
                    break
                line=line.replace('::','_').replace('**  ','').replace('\n','')
                ports.append(line)
        return ports


    def write_test_zf_deck(self, zf_spice_file_path, model_fpath,
                           termination_df=None, caps_folder=None, bw=1e9):
        """Create a spice main file (.sp) to run the ZF analysis for a \
        PSI snp file or an IDEM .cir file.

        :param sparam_zf_spice_file_path: Output file path
        :type sparam_zf_spice_file_path: string
        :param model_fpath: path to the model file (.snp or .cir)
        :type model_fpath: string
        :param termination_df: Dataframe describing the \
        termination of each port. the 1st column indicates the ports, the \
        2nd column indicates the termination and the 3rd column indicates the\
        quantity.
        Accepted terminations are '1a_dis','sc','short','oc','open','1uF', '4.7uF', etc. 
        if not provided, an automatic termination will be defined.
        :type termination_df: pandas df
        :param caps_folder: path to the folder containing the caps models.
        :type caps_folder: str        
        """        
        zf_spice_file_path=os.path.abspath(zf_spice_file_path)
        model_fpath=os.path.abspath(model_fpath)                
        root, ext = os.path.splitext(model_fpath)                
        
        if caps_folder is None:
            caps_folder=os.path.abspath(os.curdir)
                
        termfile=PSITerminationFile()
        if termination_df is None:            
            termfile.create_termination(model_fpath)            
        else:            
            termfile.load_df(termination_df)            

        lines=[]
        
        lines+=self.text_for_header()
        lines+=self.text_for_newline()
        
        lines+=self.text_for_newline()
        lines+=self.text_for_sim_settings_ac(100, 1, bw)

        lines+=self.text_for_newline()
        lines+=self.text_for_comment('Capacitor model')
        lines+=self.text_for_cap_1leg()
       
        if TextProcessor.match(ext,'.s*p'):
            lines+=self.text_for_newline()
            lines+=self.text_for_comment('include model')
            lines+=self.text_for_tstonefile_include('mymodel',model_fpath)
            lines+=self.text_for_newline()
                    
            nodes=termfile.get_port_list_from_psi_snp(model_fpath)
            lines+=self.text_for_tstone_instance('model','mymodel',nodes)
           
        else:        
            lines+=self.text_for_newline()
            lines+=self.text_for_comment('include model')
            lines+=self.text_for_include(model_fpath)
            lines+=self.text_for_newline()
            
            cir=self.get_model_name(model_fpath)
            nodes=termfile.get_port_list_from_idem_cir(model_fpath)            
            nodes.append('0')
            lines+=self.text_for_circuit_instance('mymodel',cir,nodes)
       
        lines+=self.text_for_newline()        
        lines+=self.text_for_comment('probes')

        lines+=termfile.text_for_ac_probe('1a_dis')
        
        lines+=self.text_for_newline()   
        lines+=self.text_for_comment('1a dis')
        lines+=termfile.text_for_1a_dis('1a_dis')

        lines+=self.text_for_newline()   
        lines+=self.text_for_comment('shorts')
        lines+=termfile.text_for_short('sc')

        lines+=self.text_for_newline()   
        lines+=self.text_for_comment('ideal caps')
        lines+=termfile.text_for_ideal_cap()

        lines+=self.text_for_newline()   
        lines+=self.text_for_comment('opens')
        lines+=termfile.text_for_open('oc')
        
        lines+=self.text_for_newline()   
        lines+=self.text_for_comment('caps')

        lines+=termfile.text_for_cap_model(caps_folder)
       
        lines+=self.text_for_newline()   
        lines+=self.text_for_end_file()
        
        self.create_text_file(zf_spice_file_path,lines) 
    
    def text_for_end_statement(self, type='file'):
        lines=[]
        if type == 'file':
            lines.append('.end\n')
        elif type == 'subciruit':
            lines.append('.ends\n')
        elif type == 'if':
            lines.append('.endif\n')
        return lines
 
    def open_port(self, desc=None):
        lines=[]  
        lines.append(f".subckt {desc}_open in gnd\n")
        lines.append("\tr1 in gnd 100meg\n")
        lines+=self.text_for_end_statement(type='subciruit')
        return lines
    
        
    def text_for_measure_ac(self,node,freq):    
        """Return Spice compatible text to measure one node during AC analysis

        :param node: node to be measured
        :type node: str
        :param freq: frequency to be meased at 
        :type freq: str
        :return: Text ready to be added to a spice file
        :rtype: list
        """
        lines=[]        
        lines.append(f'.MEASURE AC {node}_{freq} FIND vm({node}) AT={freq}')        
        return lines

    def text_for_rl_connector_model(self,start):
        """Return Spice compatible text to define the simple RL model

        :return: Text ready to be added to a spice file
        :rtype: list
        """                
        lines=[]
        if self.skt_groups or self.c4_groups or self.mli_groups:
            lines+=self.text_for_comment('Generic RL connector model for SKT, BGA & C4')
            lines+=self.text_for_include(self.rl_conn_mod_file,start)                                   
        return lines        
                            

    
    

    def text_for_insgroup_models(self,insgroups,top_commeent='includes',start=None):
        """Return Spice compatible text to include ATTD cap models

        :return: Text ready to be added to a spice file
        :rtype: list
        """    
        lines=[]
        incs=set()            
        for group_name in insgroups:
            group=insgroups[group_name]            
            for ins_name in group.instances:
                if group.instances[ins_name].model == 'port_open':
                    pass
                else:
                    incs.add(group.instances[ins_name].model.fpath)                
        inc_lines=[]
        for inc in incs:                        
            inc_lines+=self.text_for_include(inc,start)
        if inc_lines:
            lines+=self.text_for_comment(top_commeent)
            lines+=inc_lines
        
            
                
        return lines

    def text_for_attd_cap_models(self,start=None):
        """Return Spice compatible text to include ATTD cap models

        :return: Text ready to be added to a spice file
        :rtype: list
        """    
        lines=[]
        incs=set()            
        for group_name in self.attd_cap_groups:
            group=self.attd_cap_groups[group_name]            
            for ins_name in group.instances:
                incs.add(group.instances[ins_name].model.fpath)
        for inc in incs:                        
            lines+=self.text_for_include(inc,start)                                   
        return lines
    

    def text_for_hf_icct_mods(self,start=None):        
        lines=[]
        incs=set()            
        for group_name in self.hf_icct_groups:
            group=self.hf_icct_groups[group_name]
            for icct_name in group.instances:                
                icct_ins=group.instances[icct_name]
                incs.add(icct_ins.model.fpath)
        for inc in incs:                        
            lines+=self.text_for_include(inc,start)                                   
        return lines

    def text_for_lf_icct_mods(self,start=None):        
        lines=[]
        incs=set()            
        for group_name in self.lf_icct_groups:
            group=self.lf_icct_groups[group_name]
            for icct_name in group.instances:                
                icct_ins=group.instances[icct_name]
                incs.add(icct_ins.model.fpath)
        for inc in incs:                        
            lines+=self.text_for_include(inc,start)                                   
        return lines

    

    def text_for_attd_cap_instances(self):
        """Return Spice compatible text to include ATTD cap instances

        :return: Text ready to be added to a spice file
        :rtype: list
        """ 
        lines=[]      
        lines+=self.open_port(desc='port')
        lines.append('\n')  
        for category in self.attd_cap_groups:
            group=self.attd_cap_groups[category] 
            lines.append('\n\n')
            lines+=self.text_for_comment(category)                     
            for cap_name in group.instances:  
                cap=group.instances[cap_name]
                if cap.model == 'port_open':
                    lines+=self.text_for_inline_instance(cap.name,cap.ports,
                    cap.model,params=None)
                else:
                    lines+=self.text_for_inline_instance(cap.name,cap.ports,
                    cap.model.name,cap.params)            
        return lines
            
    def text_for_short_ports(self):       
        """Return Spice compatible text to short ports

        :return: Text ready to be added to a spice file
        :rtype: list
        """  
        lines=[]
        if self.short_ports:
            lines+=self.text_for_newline()                    
            lines+=self.text_for_comment('shorts')
            for port in self.short_ports:
                lines.append(f'v_short_{port} {port} 0 0\n')  
            lines+=self.text_for_newline()
                          
        return lines

    def text_for_1a_ac_ports(self):      
        """Return Spice compatible text to include distribute 1A AC

        :return: Text ready to be added to a spice file
        :rtype: list
        """   
        lines=[]                
        numnodes=len(self.ac_1a_ports)
        lines.append(f'.par num_nodes={numnodes}\n')

        for port in self.ac_1a_ports:          
                lines.append(f'I_cc_{port} {port} 0 ac=\'1/num_nodes\' \n')
       
        return lines
    
    def text_for_probe_tran_v_ports(self):      
        """Return Spice compatible text to transient voltage probes

        :return: Text ready to be added to a spice file
        :rtype: list
        """   
        lines=[]
        for category in self.probe_v_tran_ports:    
            lines+=self.text_for_comment(category)
            for port in self.probe_v_tran_ports[category]:
                lines.append(f'.probe tran v({port})\n')

        return lines
    
    def text_for_probe_ac_ports(self):      
        """Return Spice compatible text to ac voltage probes

        :return: Text ready to be added to a spice file
        :rtype: list
        """   
        lines=[]
        for category in self.probe_v_ac_ports:    
            lines+=self.text_for_comment(category)
            for port in self.probe_v_ac_ports[category]:
                lines.append(f'.probe ac vm({port})\n')

        return lines

    def get_model_name(self,filename):
        """Given a spice compatible include or .cir file, this fuction will 
        return the 1st  subcircuit name in that file. 

        :param filename: path to the file
        :type filename: string
        :return: subcircuit name
        :rtype: string
        """
        lines=[]
        sub=''
        with open(filename) as f:
            lines = f.readlines()
            
        for line in lines:
            parts=line.split()            
            if(len(parts)>1):                               
                if(parts[0].lower()=='.subckt'):
                    sub=parts[1]    
        return sub
    
    def text_for_global_params(self):
        lines=[]
        #sort        
        if self.glob_params:            
            lines+=self.text_for_commented_tittle('Global Parameters')                        

        for category_name in self.glob_params:
            params=self.glob_params[category_name]
            if params:
                lines+=self.text_for_comment(category_name)
                for par_name in params:
                    par=params[par_name]
                    value=par[0]
                    desc=par[1]
                    if desc:                        
                        desclines=desc.splitlines()
                        for descline in desclines:
                            lines+=self.text_for_comment(descline,1)                                
                    lines.append(f'.param {par_name} = \'{value}\'\n')            
        return lines
        
    def copy_deck(self, src,dst):
        """Create a copy of the deck file

        :param src: source file path
        :type src: str
        :param dst: des file path
        :type dst: str
        """
        src=os.path.abspath(src)
        dst=os.path.abspath(dst)
        shutil.copy(src,dst)
        
        
    def replace_block(self, filename,begin,end,block):
        """Replace a block of one existing file

        :param filename: filename path
        :type filename: string
        :param begin: Text line that determines the globegining of the block that
         will be replaced
        :type begin: string
        :param end: Text line that determines the ending of the block that
         will be replaced
        :type end: string
        :param block: new block that will replace the previous block
        :type block: list
        """
        lines=self.Read(filename)
        a_part=[]
        b_part=[]
        index=0
        a_index=-1
        b_index=-1
        
        for line in lines:            
            if(line==begin):
                a_index=index
            if(line==end):
                b_index=index
            index+=1        
        self. create_text_file(filename,lines[:a_index+1]+   block +  lines[b_index:])
        #return    
        
    def logsampling(self, min_range, max_range, points_per_decade):
        ndecades = log10(max_range) - log10(min_range)
        npoints = int(ndecades) * points_per_decade
        points = np.logspace(log10(min_range), log10(max_range), num=npoints, 
        endpoint=True, base=10)

        points = list(points)        
        return points

    def get_nodes_from_termination_desc(self,termination_desc):
        """Return the nodes asociated with a termination file

        :param termination_desc: list with the nodes and the terminationsf
        :type termination_desc: list
        :return: list with the nodes
        :rtype: list
        """
        nodes=[]
        for termination in termination_desc:
            nodes.append(termination[0])
        return nodes    
    
    def create_psi_conn_map(self,brd_ports, brd_skt_comp_name,
        pkg_ports, pkg_skt_comp_name):
            
        skt_conn_pos=[]
        skt_conn_neg=[]
        for brd_port in brd_ports:
            for brd_comp in brd_port.comps:
                #check for skt ports on brd
                if brd_comp.name.lower()==brd_skt_comp_name.lower(): 
                    for brd_pin in brd_comp.pos_pins:                
                        for pkg_port in pkg_ports:
                            for pkg_comp in pkg_port.comps:
                                if pkg_comp.name.lower()==pkg_skt_comp_name.lower():
                                    for pkg_pin in pkg_comp.pos_pins:
                                        brd_pin_name=brd_pin.split('!!')[1]
                                        pkg_pin_name=pkg_pin.split('!!')[1]                                
                                        if(brd_pin_name==pkg_pin_name):                                    
                                            skt_conn_pos.append([brd_port.name,
                                            pkg_port.name])
        
                    for brd_pin in brd_comp.neg_pins:                
                        for pkg_port in pkg_ports:
                            for pkg_comp in pkg_port.comps:
                                if pkg_comp.name.lower()==pkg_skt_comp_name.lower():
                                    for pkg_pin in pkg_comp.neg_pins:
                                        brd_pin_name=brd_pin.split('!!')[1]
                                        pkg_pin_name=pkg_pin.split('!!')[1]                                
                                        if(brd_pin_name==pkg_pin_name):                                    
                                            skt_conn_neg.append([brd_port.name,
                                            pkg_port.name])                                            

        #count connections
        skt_conn_summary=[]

        if not skt_conn_pos or not skt_conn_neg:
            EventLogger.raise_value_error('Psi components don\'t share pins. connection map cannot be created.')

        #init the array
        con=skt_conn_pos[0]
        skt_conn_summary.append([con[0],con[1],0,0])
        
        for con in skt_conn_pos:
            found=False
            for i in range(len(skt_conn_summary)):
                conn_summ=skt_conn_summary[i]        
                if(con[0]==conn_summ[0] and con[1]==conn_summ[1]):
                    found=True
                    skt_conn_summary[i]=[conn_summ[0],conn_summ[1],
                    conn_summ[2]+1,conn_summ[3]]
                    break            
            if found==False:
                skt_conn_summary.append([con[0],con[1],1,0])
        
        
        for con in skt_conn_neg:
            found=False
            for i in range(len(skt_conn_summary)):
                conn_summ=skt_conn_summary[i]        
                if(con[0]==conn_summ[0] and con[1]==conn_summ[1]):
                    found=True
                    skt_conn_summary[i]=[conn_summ[0],conn_summ[1],
                    conn_summ[2],conn_summ[3]+1]
                    break            
            if found==False:
                skt_conn_summary.append([con[0],con[1],0,1])        
        return skt_conn_summary

    
    def load_cap_models(self,cap_model_path):
        
        #read capacitor model
        cap_models={}
        with open(cap_model_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                cap_models[row[0]]=row[1]

        self.attd_cap_models=cap_models
        return cap_models
    
    def load_psi_model(self,db_path=None,idem_model_path=None,tstone_path=None,model_folder=None,conn_side='top'):        
        """Load a new spd model

        :param model_name: User defined model name. e.g: brd
        :type model_name: str
        :param db_path: path to the SPD file
        :type db_path: str
        :param inc_path: idem model path 
        :type inc_path: str        
        """       

        

        mod=ModPsi()            

        mod.load_data(db_path,idem_model_path,tstone_path,model_folder,conn_side)
        model_name=mod.name
        
        self.psi_models[model_name]=mod
        return model_name               

    def create_psi_model_instance(self,model_name,instance_name):
        """Create a PSI model istance

        :param model_name: Model name. must exit in the psi_models dictionary
        :type model_name: str
        :param instance_name: User defined instance name
        :type instance_name: string
        :return: PSI istance object
        :rtype: Psi_model_instance
        """
        mod=self.psi_models[model_name]
        ins=InsPsi()
        ins.model=mod
        ins.name=instance_name
        ins.init_instance_port_names()
        return ins
         
    def replace_text_in_brd_instance_ports(self,old_text,new_text):
        """replace text in the board instance ports

        :param old_text: old text
        :type old_text: string
        :param new_text: new text
        :type new_text: string
        """
        self.brd_instance.replace_text_in_ports(old_text,new_text)
    
    def replace_text_in_pkg_instance_ports(self,old_text,new_text,
        pkg_instance='pkg'):    
        """Replace text in the package instance ports

        :param old_text: old text
        :type old_text: string
        :param new_text: new text
        :type new_text: string
        :param pkg_instance: 
        :type pkg_instance:
        """
        self.pkg_instance.replace_text_in_ports(old_text,new_text)
        
    def load_brd(self,db_path=None,idem_mod_path=None,tstone_path=None,
        ins_name='brd',model_folder=None):
        """Create the board instance.

        :param db_path: path to the board .spd file, defaults to None
        :type db_path: str, optional
        :param idem_mod_path: path to the IdEM macromodel file (.cir), defaults \
            to None
        :type idem_mod_path: str, optional
        :param tstone_path: path to the touchstone file (.snp), defaults to None
        :type tstone_path: str, optional
        :param ins_name: board instance name, defaults to 'brd'
        :type ins_name: str, optional
        :param model_folder: Folder containing the board model files. If this \
            parameter is provided, then the different files (.snp, .cir and \
                .snp) will be loaded automatically, defaults to None
        :type model_folder: str, optional
        """
        EventLogger.msg('Creating BRD instance...')
        if not db_path and not idem_mod_path and not tstone_path and not model_folder:
            model_folder=self.brd_mod_folder
            EventLogger.info('Not model files provided. Attemping to load models from default folder: '+ model_folder)
            mod_name=self.load_psi_model(model_folder=model_folder,conn_side='top')
        else:
            mod_name=self.load_psi_model(db_path,idem_mod_path,tstone_path,model_folder,conn_side='top')

        
        
        self.psi_models[mod_name].tstone_mod_name='s_'+ins_name
        self.brd_instance=self.create_psi_model_instance(mod_name,ins_name)
        EventLogger.msg('Done')
        
    def load_pkg(self,db_path=None,idem_mod_path=None,tstone_path=None,
        ins_name='pkg',model_folder=None):
        """Create the package instance.

        :param db_path: path to the package .spd file, defaults to None
        :type db_path: str, optional
        :param idem_mod_path: path to the IdEM macromodel file (.cir), defaults\
             to None
        :type idem_mod_path: str, optional
        :param tstone_path: path to the touchstone file (.snp), defaults to None
        :type tstone_path: str, optional
        :param ins_name: board instance name, defaults to 'brd'
        :type ins_name: str, optional
        :param model_folder: Folder containing the board model files. If this \
            parameter is provided, then the different files (.snp, .cir and \
                .snp) will be loaded automatically, defaults to None
        :type model_folder: str, optional
        """ 
        EventLogger.msg('Creating PKG instance...')
        if not db_path and not idem_mod_path and not tstone_path and not model_folder:
            model_folder=self.pkg_mod_folder
            EventLogger.info('Not model files provided. Attemping to load models from default folder: '+ model_folder)
            mod_name=self.load_psi_model(model_folder=model_folder,conn_side='bottom')
        else:
            mod_name=self.load_psi_model(db_path,idem_mod_path,tstone_path,model_folder,conn_side='bottom')
        
        self.psi_models[mod_name].tstone_mod_name='s_'+ins_name
        self.pkg_instance=self.create_psi_model_instance(mod_name,ins_name)
        EventLogger.msg('Done')   

        
    def load_pkg_patch(self,db_path=None,idem_mod_path=None,tstone_path=None,
        ins_name='pkg_patch',model_folder=None):
        """Create the package patch instance.

        :param db_path: path to the package .spd file, defaults to None
        :type db_path: str, optional
        :param idem_mod_path: path to the IdEM macromodel file (.cir), defaults\
             to None
        :type idem_mod_path: str, optional
        :param tstone_path: path to the touchstone file (.snp), defaults to None
        :type tstone_path: str, optional
        :param ins_name: board instance name, defaults to 'brd'
        :type ins_name: str, optional
        :param model_folder: Folder containing the board model files. If this \
            parameter is provided, then the different files (.snp, .cir and \
                .snp) will be loaded automatically, defaults to None
        :type model_folder: str, optional
        """     
        EventLogger.msg('Creating PKG patch instance...')
        if not db_path and not idem_mod_path and not tstone_path and not model_folder:
            model_folder=self.pkg_patch_mod_folder
            EventLogger.info('Not model files provided. Attemping to load models from default folder: '+ model_folder)
            mod_name=self.load_psi_model(model_folder=model_folder,conn_side='bottom')
        else:
            mod_name=self.load_psi_model(db_path,idem_mod_path,tstone_path,model_folder,conn_side='bottom')
        
        self.psi_models[mod_name].tstone_mod_name='s_'+ins_name
        self.pkg_patch_instance=self.create_psi_model_instance(mod_name,ins_name)
        EventLogger.msg('Done')   
    
    def load_pkg_int(self,db_path=None,idem_mod_path=None,tstone_path=None,
        ins_name='pkg_int',model_folder=None):
        """Create the package patch instance.

        :param db_path: path to the package .spd file, defaults to None
        :type db_path: str, optional
        :param idem_mod_path: path to the IdEM macromodel file (.cir), defaults\
             to None
        :type idem_mod_path: str, optional
        :param tstone_path: path to the touchstone file (.snp), defaults to None
        :type tstone_path: str, optional
        :param ins_name: board instance name, defaults to 'brd'
        :type ins_name: str, optional
        :param model_folder: Folder containing the board model files. If this \
            parameter is provided, then the different files (.snp, .cir and \
                .snp) will be loaded automatically, defaults to None
        :type model_folder: str, optional
        """     
        EventLogger.msg('Creating PKG Interposer instance...')
        if not db_path and not idem_mod_path and not tstone_path and not model_folder:
            model_folder=self.pkg_patch_mod_folder
            EventLogger.info('Not model files provided. Attemping to load models from default folder: '+ model_folder)
            mod_name=self.load_psi_model(model_folder=model_folder,conn_side='bottom')
        else:
            mod_name=self.load_psi_model(db_path,idem_mod_path,tstone_path,model_folder,conn_side='bottom')
        
        self.psi_models[mod_name].tstone_mod_name='s_'+ins_name
        self.pkg_int_instance=self.create_psi_model_instance(mod_name,ins_name)
        EventLogger.msg('Done')  
    
    def load_spice_models_from_folder(self, folder_path,recursive=False):        
        """load models from a given folder

        :param folder_path: path to the folder containing the models
        :type folder_path: string
        """
        folder_path=os.path.abspath(folder_path)+'/'
        EventLogger.msg('Loading models from: '+folder_path)
        files=Io.find_in_folder(folder_path,['*.inc','*.cir','*.sp'],recursive)
        if not files:
            EventLogger.raise_value_error('0 files found')
        for f in files:
            self.load_spice_model(f)   
        
        EventLogger.msg('Done')
             
    def load_attd_caps_models(self,path=None,recursive=True):
        """Load attd cap models from a specified path

        :param path: ath to the folder containing the models. If not provided,\
        the default path will be used., defaults to None
        :type path: str, optional
        :param recursive: Whether to search for models in subfolders of the \
        specified path, defaults to True
        :type recursive: bool, optional
        """
        EventLogger.msg('loading attd cap models...')
        if path==None:
            path=self.cap_mod_folder
            EventLogger.info('path not provided, attempting loading from default path:'+path)                
        files=Io.find_in_folder(path,['*.inc','*.cir','*.sp'],recursive)
        if not files:
            EventLogger.raise_value_error('0 files found')
        for f in files:
            print(f)
            self.load_spice_model(f)   
        EventLogger.msg('Done')

    def connect_1a_ac_dis(self,ports):
        """Connect 1A AC to a list of ports.

        :param ports: List or single port name to be connected to 1A AC
        :type ports: List[str] or str
        """
        if isinstance(ports,str):
            ports=[ports]

        self.ac_1a_ports+=ports
        self.probe_v_ac(ports,'1A AC distributed')

    def probe_v_tran(self,ports,category='probes'):
        """Probe a list of ports for transient voltage.

        :param ports: List or single port name to be probed.
        :type ports: List[str] or str
        :param category: Category of the probes, defaults to 'probes'
        :type category: str, optional
        """
        if isinstance(ports,str):
            ports=[ports]

        if category not in self.probe_v_tran_ports.keys():            
            self.probe_v_tran_ports[category]=[]   

        probe_ports=self.probe_v_tran_ports[category]
        probe_ports+=ports            
    
    def probe_v_ac(self,ports,category='probes'):
        """Probe a list of ports for AC voltage.

        :param ports: List or single port name to be probed
        :type ports: List[str] or str
        :param category: Category of the probe, defaults to 'probes'
        :type category: str, optional
        """
        if isinstance(ports,str):
            ports=[ports]

        if category not in self.probe_v_ac_ports.keys():            
            self.probe_v_ac_ports[category]=[]   

        probe_ports=self.probe_v_ac_ports[category]
        probe_ports+=ports        

    def connect_lin_port(self,ports):
        """Connect linear ports to a list of ports for linear analysis (LIN)

        :param ports: List or single port name to be connected to LIN ports
        :type ports: List[str] or str
        """
        if isinstance(ports,str):
            ports=[ports]
        self.lin_ports+=ports

    def get_spice_model_by_filename(self,filename):   
        """Get a spice model by its filename

        :param filename: Filename of the spice model
        :type filename: str
        :return: The spice model object with the specified filename
        :rtype: Object
        """
        for mod in self.spice_models:            
            if filename==self.spice_models[mod].filename:                
                return self.spice_models[mod]

    def connect_attd_cap_by_model(self,name,model,port_from,port_to,count,category='caps'):
        
        if category not in self.attd_cap_groups.keys():
            self.attd_cap_groups[category]=InsGroup()
                    
        attdgroup=self.attd_cap_groups[category]      

        ins=SubcktInstance()
        ins.name=name
        ins.model=model
        ins.ports=[port_from,port_to]
        ins.params['NCAPS']=count
        attdgroup.instances[ins.name]=ins
            

    def connect_attd_caps_by_model(self,model,ports,count,category='caps'):                
        for port in    ports:
            name=port+'_'+model.name
            self.connect_attd_cap_by_model(name,model,port,'0',count,category)
            

    def connect_attd_caps_by_model_filename(self,ports,filename,count=1,category='caps'):
        cap_mod=self.get_spice_model_by_filename(filename)
        self.connect_attd_caps_by_model(cap_mod,ports,count,category)        
                
    def connect_attd_caps_to_psi_instance_by_comp_model(self,psi_ins, map,category='caps'):
        cap_map={}
        for row in map:
            #Check if desc table has file name or model name
            root, ext = os.path.splitext(row[1])
            if ext:    
                #filename                
                cap_map[row[0]]=self.get_spice_model_by_filename(row[1])
            else:
                #model name
                cap_map[row[0]]=self.spice_models[row[1].lower()]

        caps_in_ports=psi_ins.find_comp_models_in_ports()       
        for i,cap_in_port in enumerate(caps_in_ports):
            port_name=cap_in_port[0]
            cap_desc=cap_in_port[1]
            if cap_desc in cap_map:
                cap_mod=cap_map[cap_desc]
                count=cap_in_port[2]                        
                self.connect_attd_cap_by_model(f'{port_name}_{i}',cap_mod,
                port_name,'0',count,category)
            else:
                EventLogger.info("Capacitor model not provided for: "+cap_desc)

    def connect_attd_caps_to_psi_instance_by_port(self,psi_ins, 
        map,category='caps'):                
        for i,row in enumerate(map):
            count=1
            a=InsPsi()                
            port_name= psi_ins.get_instance_port_name(row[0])
            cap=row[1]
            if not cap:
                continue                
            if len(row)>2:
                count=row[2]
                if not count:
                    count=1
            
            #Check if desc table has file name or model name
            root, ext = os.path.splitext(cap)                
            if ext:    
                #file name                
                cap_mod=self.get_spice_model_by_filename(cap)
            else:
                try:
                    #model name
                    cap_mod=self.spice_models[cap.lower()]                
                except:
                    cap_mod = 'port_open'
            self.connect_attd_cap_by_model(f'{port_name}_{i}',cap_mod,
            port_name,'0',count,category)

    def connect_attd_caps_to_psi_instance(self,psi_ins, 
        cap_desc_path,category='caps',delimiter=','):        
        with open(cap_desc_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=delimiter)
            headers = next(csv_reader, None)
            map=list(csv_reader)
            if headers[0]==self.header_for_cap_map_by_comp_model[0]:
                self.connect_attd_caps_to_psi_instance_by_comp_model(psi_ins,
                map,category)
            elif headers[0]==self.header_for_cap_map_by_port[0]:
                self.connect_attd_caps_to_psi_instance_by_port(psi_ins,
                map,category)
            else:
                EventLogger.raise_value_error(f'Incorrect header in cap map. \
                valid headers are {self.header_for_cap_map_by_comp_model} or \
                {self.header_for_cap_map_by_port}' )
                #read this as a comp map

    def save_cap_map_example(self,psi_mod,fpath1='example_cap_map_by_comp.csv',
        fpath2='example_cap_map_by_port.csv'):
        """Save a capacitor map example file

        :param fpath: file path
        :type fpath: str
        """
        fpath1=os.path.abspath(fpath1)
        
        data=psi_mod.get_comp_model_names('c*')

        rows=[] 
        rows.append(self.header_for_cap_map_by_comp_model)
        for i,row in enumerate(data):
            if i==0:
                rows.append([row,'attd_cap_file_name.sp'])
            if i==0:
                rows.append([row,'attd_cap_model_name'])
            else:
                rows.append([row])
        Io.create_csv_file(fpath1,rows)
            
        if not fpath2:
            return

        fpath2=os.path.abspath(fpath2)
        data=psi_mod.db_ports

        rows=[] 
        rows.append(self.header_for_cap_map_by_port)        
        for i,row in enumerate(data):
            if i==0:
                rows.append([row,'attd_cap_file_name.sp',3])
            if i==0:
                rows.append([row,'attd_cap_model_name',2])
            else:
                rows.append([row])
        Io.create_csv_file(fpath2,rows) 
        

                
    def save_die_map_example(self,psi_mod,fpath='example_die_map.csv'):                  
        """Save the a die map example file

        :param data_path: file path
        :type data_path: str
        """
        rows=[]
        rows.append(self.header_for_die_map)
        for i,port in enumerate(psi_mod.db_ports):
            if i==0:
                rows.append([port.name,'die_port_1'])
            elif i==1:
                rows.append([port.name,'die_port_2'])
            elif i==2:
               rows.append([port.name,'','die_port_1'])
            elif i==3:
                rows.append([port.name,'','die_port_2'])
            else:
                rows.append([port.name])        
        Io.create_csv_file(fpath,rows)


    def save_psi_rl_conn_map_file(self,psi_ins_from,psi_ins_to,
                                  from_refdes,to_refdes,
                                  fpath='example_skt_map.csv',
                                  pin_r='30m',pin_l='3n'):
        """Save a skt map

        :param fpath: file path
        :type fpath: str
        """
        if psi_ins_from is None or psi_ins_to is None:
            EventLogger.EventLogger.raise_warning('connection map cannot be created')
            return
        
        fpath=os.path.abspath(fpath)
        
        
        rows=[]         
        rows.append(self.header_for_skt_map)
        
        brd_port_info=psi_ins_from.model.db_ports
        pkg_port_info=psi_ins_to.model.db_ports
        
        conn_map=self.create_psi_conn_map(brd_port_info, 
                                              from_refdes, pkg_port_info,
                                              to_refdes)
        for row in conn_map:
            if row[2]==0 or row[3]==0:
                continue
            rows.append([row[0],row[1],row[2],row[3],pin_r,pin_l])
                
        Io.create_csv_file(fpath,rows) 

    def save_mli_map_file(self,fpath='example_mli_map.csv',pin_r='30m',pin_l='3n'):
        try:
            if self.pkg_int_instance and self.pkg_patch_instance:
                self.save_psi_rl_conn_map_file(self.pkg_int_instance,
                                               self.pkg_patch_instance,
                                               self.pkg_int_instance.model.db_conn_refdes_top,
                                               self.pkg_patch_instance.model.db_conn_refdes_bot,fpath)
        except:
            EventLogger.raise_warning("Cannot create MLI map")
    def save_skt_map_file(self,fpath='example_skt_map.csv',pin_r='30m',pin_l='3n'):
        """Save a skt map

        :param fpath: file path
        :type fpath: str
        """
        if self.brd_instance and self.pkg_instance:
            self.save_psi_rl_conn_map_file(self.brd_instance,self.pkg_instance,
                                           self.brd_instance.model.db_conn_refdes_top,
                                           self.pkg_instance.model.db_conn_refdes_bot,
                                           fpath,pin_r,pin_l)
        elif self.brd_instance and self.pkg_int_instance:
            self.save_psi_rl_conn_map_file(self.brd_instance,self.pkg_int_instance,
                                           self.brd_instance.model.db_conn_refdes_top,
                                           self.pkg_int_instance.model.db_conn_refdes_bot,
                                           fpath,pin_r,pin_l)
        else:
            EventLogger.raise_warning("Cannot create skt map")

        #if self.pkg_instance is None or self.brd_instance is None:
        #    EventLogger.EventLogger.raise_warning('Skt map cannot be created')
        #    return
        #fpath=os.path.abspath(fpath)
        #
        #
        #rows=[]         
        #rows.append(self.header_for_skt_map)
        #
        #brd_port_info=self.brd_instance.model.db_ports
        #pkg_port_info=self.pkg_instance.model.db_ports
        #
        #try:
        #    brd_skt_name=self.brd_instance.model.db_skt_name
        #    pkg_skt_name=self.pkg_instance.model.db_skt_name
#
        #    skt_conn_map=self.create_psi_conn_map(brd_port_info, 
        #    brd_skt_name, pkg_port_info, pkg_skt_name)
        #except:
        #    EventLogger.raise_warning('Skt map cannot be created')
        #    return
        #for row in skt_conn_map:
        #    if row[2]==0 or row[3]==0:
        #        continue
        #    rows.append([row[0],row[1],row[2],row[3],pin_r,pin_l])
        #        
        #Io.create_csv_file(fpath,rows)                     
            
        
       
    def clone_lf_icct_folder_template(self):
        """Copy the LF icct folder template into the deck folder.
        This folder includes premade common icct profiles including pulse, and 'chair' profiles.
        """
        src_folder = self.icct_folder_template

        dst_folder=self.icct_folder
        
        shutil.copytree(src_folder, dst_folder,dirs_exist_ok=True)
    
    def init_deck_folder(self,die_map_path='./maps/example_die_map.csv',
        pkg_cap_map_path_by_comp='./maps/example_pkg_cap_map_by_comp.csv',
        pkg_cap_map_path_by_port='./maps/example_pkg_cap_map_by_port.csv',
        brd_cap_map_path_by_comp='./maps/example_brd_cap_map_by_comp.csv',
        brd_cap_map_path_by_port='./maps/example_brd_cap_map_by_port.csv',
        pkg_int_cap_map_path_by_comp='./maps/example_pkg_int_cap_map_by_comp.csv',
        pkg_int_cap_map_path_by_port='./maps/example_pkg_int_cap_map_by_port.csv',
        pkg_patch_cap_map_path_by_comp='./maps/example_pkg_patch_cap_map_by_comp.csv',
        pkg_patch_cap_map_path_by_port='./maps/example_pkg_patch_cap_map_by_port.csv',
        skt_map='./maps/example_skt_map.csv',
        mli_map='./maps/example_mli_map.csv'):        

        """Create the required folders and files to start a fesh new deck.
        """
        self.clone_lf_icct_folder_template()

        #maps
        if self.pkg_instance:
            self.save_die_map_example(self.pkg_instance.model,die_map_path)
        elif self.pkg_patch_instance:
            self.save_die_map_example(self.pkg_patch_instance.model,die_map_path)

        if self.pkg_instance:
            self.save_cap_map_example(self.pkg_instance.model,
            pkg_cap_map_path_by_comp,pkg_cap_map_path_by_port)
        
        if self.pkg_int_instance:
            self.save_cap_map_example(self.pkg_int_instance.model,
            pkg_int_cap_map_path_by_comp,pkg_int_cap_map_path_by_port)
        
        if self.pkg_patch_instance:
            self.save_cap_map_example(self.pkg_patch_instance.model,
            pkg_patch_cap_map_path_by_comp,pkg_patch_cap_map_path_by_port)

        self.save_cap_map_example(self.brd_instance.model,
        brd_cap_map_path_by_comp,brd_cap_map_path_by_port)    
        
        self.save_mli_map_file(mli_map)
        self.save_skt_map_file(skt_map)



    def connect_attd_caps_to_brd(self,cap_map_fpath,category='brd caps'):
        """Connect capacitors to the board using a mapping file. The file\
        should be a CSV and there are two different formats that could be used:
        Component model format: In this format, the capacitor model name (as \
        shown in PowerSI) is in the first column and the equivalent spice \
        filename or model name is in the 2nd column.
        Port Map format: In this format, the database ports(as shown in PowerSI)\
        are in the first column, the equivalent spice \
        filename or model name is in the 2nd column, and the number of caps (NCAP)\
        is in the third column.

        :param cap_map_fpath: cap mapping file path 
        :type cap_map_fpath: str
        :param category: Capacitors category, defaults to 'brd caps'
        :type category: str, optional        
        """
        EventLogger.msg('Connecting brd caps...')
        cap_map_fpath=os.path.abspath(cap_map_fpath)
        self.connect_attd_caps_to_psi_instance(self.brd_instance,cap_map_fpath,
        category)
        EventLogger.msg('Done')
        

    def connect_attd_caps_to_pkg(self,cap_desc_path,category='pkg caps'):
        """Connect capacitors to the package using a mapping file. The file\
        should be a CSV and there are two different formats that could be used:
        Component model format: In this format, the capacitor model name (as \
        shown in PowerSI) is in the first column and the equivalent spice \
        filename or model name is in the 2nd column.
        Port Map format: In this format, the database ports(as shown in PowerSI)\
        are in the first column, the equivalent spice \
        filename or model name is in the 2nd column, and the number of caps (NCAP)\
        is in the third column.

        :param cap_desc_path: cap mapping file path 
        :type cap_desc_path: str
        :param category: Capacitors category, defaults to 'pkg caps'
        :type category: str, optional        
        """
        EventLogger.msg('Connecting pkg caps...')  
        cap_desc_path=os.path.abspath(cap_desc_path)              
        self.connect_attd_caps_to_psi_instance(self.pkg_instance,cap_desc_path,
        category)
        EventLogger.msg('Done')         
    
    def connect_attd_caps_to_pkg_patch(self,cap_desc_path,category='pkg caps'):
        """Connect capacitors to the package patch using a mapping file. The file\
        should be a CSV and there are two different formats that could be used:
        Component model format: In this format, the capacitor model name (as \
        shown in PowerSI) is in the first column and the equivalent spice \
        filename or model name is in the 2nd column.
        Port Map format: In this format, the database ports(as shown in PowerSI)\
        are in the first column, the equivalent spice \
        filename or model name is in the 2nd column, and the number of caps (NCAP)\
        is in the third column.

        :param cap_desc_path: cap mapping file path 
        :type cap_desc_path: str
        :param category: Capacitors category, defaults to 'pkg caps'
        :type category: str, optional        
        """
        EventLogger.msg('Connecting pkg patch caps...')  
        cap_desc_path=os.path.abspath(cap_desc_path)              
        self.connect_attd_caps_to_psi_instance(self.pkg_patch_instance,cap_desc_path,
        category)
        EventLogger.msg('Done')  
    
    def connect_attd_caps_to_pkg_int(self,cap_desc_path,category='pkg caps'):
        """Connect capacitors to the package interposer using a mapping file. The file\
        should be a CSV and there are two different formats that could be used:
        Component model format: In this format, the capacitor model name (as \
        shown in PowerSI) is in the first column and the equivalent spice \
        filename or model name is in the 2nd column.
        Port Map format: In this format, the database ports(as shown in PowerSI)\
        are in the first column, the equivalent spice \
        filename or model name is in the 2nd column, and the number of caps (NCAP)\
        is in the third column.

        :param cap_desc_path: cap mapping file path 
        :type cap_desc_path: str
        :param category: Capacitors category, defaults to 'pkg caps'
        :type category: str, optional        
        """
        EventLogger.msg('Connecting pkg interposer caps...')  
        cap_desc_path=os.path.abspath(cap_desc_path)              
        self.connect_attd_caps_to_psi_instance(self.pkg_int_instance,cap_desc_path,
        category)
        EventLogger.msg('Done')  

    def connect_psi_ins_rl(self,psi_ins_from,psi_ins_to,conn_groups,pin_r='skt_pin_r',
                            pin_l='skt_pin_l',category='skt',
                            from_refdes=None,to_refdes=None,):
        """Connect two PSI instances using an RL connector model

        psi_ins_bot,psi_ins2
        :param psi_ins_from: PSI model to connect from
        :type psi_ins_from: PSI instance
        :param psi_ins_to: PSI model to connect to
        :type psi_ins_to: PSI instance
        :param pin_r: socket pin resistance, defaults to 'skt_pin_r'
        :type pin_r: str, optional
        :param pin_l: socket pin inductance, defaults to 'skt_pin_l'
        :type pin_l: str, optional
        :param category: sockect category that will be presented as a comment in the spice deck on top of the socket connection instances, defaults to 'skt'
        :type category: str, optional
        :param brd_skt_name: Name of the socket circuit as shown in PowerSI board database, defaults to None
        :type brd_skt_name: str, optional
        :param pkg_skt_name: Name of the socket circuit as shown in PowerSI package database, defaults to None
        :type pkg_skt_name: _type_, optional
        """
        EventLogger.msg('Connecting PSI models...')
        from_port_info=psi_ins_from.model.db_ports
        to_port_info=psi_ins_to.model.db_ports
        if not from_refdes:
            from_refdes=psi_ins_from.model.db_conn_refdes_top
            EventLogger.info(f'connector not defined by user, {from_refdes} will be used!')

        if not to_refdes:            
            to_refdes=psi_ins_to.model.db_conn_refdes_bot
            EventLogger.info(f'connector not defined by user, {to_refdes} will be used!')
        EventLogger.msg(f'connecting from {from_refdes} to {to_refdes}')
        skt_conn_map=self.create_psi_conn_map(from_port_info, 
        from_refdes, to_port_info, to_refdes)

        skt_conn_map_2=[]
        for row in skt_conn_map:
            skt_conn_map_2.append([row[0],row[1],row[2],row[3],pin_r,pin_l])

        conn_group=self.create_connector_instance(psi_ins_from,psi_ins_to,
        skt_conn_map_2,category=category)        
        
        conn_groups[category]=conn_group
        
        EventLogger.msg(f'{len(conn_group.instances)} socket ports connected')
    
    def connect_mli(self,pin_r='skt_pin_r',pin_l='skt_pin_l',category='mli',
        int_mli_name=None,patch_mli_name=None):
        """Connect the MLI model between a Interposer and patch.

        :param pin_r: socket pin resistance, defaults to 'skt_pin_r'
        :type pin_r: str, optional
        :param pin_l: socket pin inductance, defaults to 'skt_pin_l'
        :type pin_l: str, optional
        :param category: sockect category that will be presented as a comment in the spice deck on top of the socket connection instances, defaults to 'skt'
        :type category: str, optional
        :param int_mli_name: interposer MLI refdes, defaults to None
        :type int_mli_name: str, optional
        :param patch_mli_name: patch MLI refdef, defaults to None
        :type patch_mli_name: str, optional
        """
        self.connect_psi_ins_rl(self.pkg_int_instance,self.pkg_patch_instance,self.mli_groups,
                                pin_r,pin_l,category,int_mli_name,patch_mli_name)

    def connect_skt(self,pin_r='skt_pin_r',pin_l='skt_pin_l',category='skt',
        brd_skt_name=None,pkg_skt_name=None):
        """Connect the socket model between a board and package.

        :param pin_r: socket pin resistance, defaults to 'skt_pin_r'
        :type pin_r: str, optional
        :param pin_l: socket pin inductance, defaults to 'skt_pin_l'
        :type pin_l: str, optional
        :param category: sockect category that will be presented as a comment in the spice deck on top of the socket connection instances, defaults to 'skt'
        :type category: str, optional
        :param brd_skt_name: Name of the socket circuit as shown in PowerSI board database, defaults to None
        :type brd_skt_name: str, optional
        :param pkg_skt_name: Name of the socket circuit as shown in PowerSI package database, defaults to None
        :type pkg_skt_name: _type_, optional
        """
        if self.brd_instance and self.pkg_instance:
            self.connect_psi_ins_rl(self.brd_instance,self.pkg_instance,self.skt_groups,
                                    pin_r,pin_l,'skt',brd_skt_name,pkg_skt_name)
        elif self.brd_instance and self.pkg_int_instance:
            self.connect_psi_ins_rl(self.brd_instance,self.pkg_int_instance,self.skt_groups,
                                    pin_r,pin_l,'skt',brd_skt_name,pkg_skt_name)
        

        #EventLogger.msg('Connecting socket...')
        #brd_port_info=self.brd_instance.model.db_ports
        #pkg_port_info=self.pkg_instance.model.db_ports
        #if not brd_skt_name:
        #    brd_skt_name=self.brd_instance.model.db_skt_name
        #    EventLogger.info(f'brd skt not defined by user, {brd_skt_name} will be used!')
#
        #if not pkg_skt_name:            
        #    pkg_skt_name=self.pkg_instance.model.db_skt_name
        #    EventLogger.info(f'pkg skt not defined by user, {pkg_skt_name} will be used!')
        #EventLogger.msg(f'BRD SKT:{brd_skt_name}, PKG SKT:{pkg_skt_name}')
        #skt_conn_map=self.create_psi_conn_map(brd_port_info, 
        #brd_skt_name, pkg_port_info, pkg_skt_name)
#
        #skt_conn_map_2=[]
        #for row in skt_conn_map:
        #    skt_conn_map_2.append([row[0],row[1],row[2],row[3],pin_r,pin_l])
#
#
        #conn_group=self.create_connector_instance(self.brd_instance,self.pkg_instance,
        #skt_conn_map_2,category='skt')        
        #
        #self.skt_groups[category]=conn_group
        #
        #EventLogger.msg(f'{len(conn_group.instances)} socket ports connected')
  

    def connect_psi_ins_by_map(self,map_fpath,psi_ins_from,psi_ins_to,conn_groups,
                           category='skt',delimiter=','):
        """Connect the socket model between a board and package.

        :param map_fpath: path to the socket map
        :type brd_skt_name: str, optional
        :param psi_ins_from: PSI model to connect from
        :type psi_ins_from: PSI instance
        :param psi_ins_to: PSI model to connect to
        :type psi_ins_to: PSI instance
        :param pin_r: socket pin resistance, defaults to 'skt_pin_r'
        :type pin_r: str, optional
        :param pin_l: socket pin inductance, defaults to 'skt_pin_l'
        :type pin_l: str, optional
        :param category: sockect category that will be presented as a comment in the spice deck on top of the socket connection instances, defaults to 'skt'
        :type category: str, optional
        
        """
        with open(map_fpath) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=delimiter)
            headers = next(csv_reader, None)
            skt_conn_map=list(csv_reader)
            #TODO: Parse header           

        EventLogger.msg('Connecting psi models using map...')               
        conn_group=self.create_connector_instance(psi_ins_from,psi_ins_to,
        skt_conn_map,category=category)
        
        #self.skt_groups[category]=conn_group
        conn_groups[category]=conn_group
        
        EventLogger.msg(f'{len(conn_group.instances)} ports connected')

    def connect_mli_by_map(self,map_fpath,
                           category='mli',delimiter=','):
        """Connect the socket model between a board and package.

        :param map_fpath: path to the socket map
        :type brd_skt_name: str, optional
        :param psi_ins_from: PSI model to connect from
        :type psi_ins_from: PSI instance
        :param psi_ins_to: PSI model to connect to
        :type psi_ins_to: PSI instance
        :param pin_r: socket pin resistance, defaults to 'skt_pin_r'
        :type pin_r: str, optional
        :param pin_l: socket pin inductance, defaults to 'skt_pin_l'
        :type pin_l: str, optional
        :param category: sockect category that will be presented as a comment in the spice deck on top of the socket connection instances, defaults to 'mli'
        :type category: str, optional
        
        """
        self.connect_psi_ins_by_map(map_fpath,self.pkg_int_instance,
                                    self.pkg_patch_instance,self.mli_groups,category)
    
    def connect_skt_by_map(self,map_fpath,
                           category='skt',delimiter=','):
        """Connect the socket model between a board and package.

        :param map_fpath: path to the socket map
        :type brd_skt_name: str, optional
        :param pin_r: socket pin resistance, defaults to 'skt_pin_r'
        :type pin_r: str, optional
        :param pin_l: socket pin inductance, defaults to 'skt_pin_l'
        :type pin_l: str, optional
        :param category: sockect category that will be presented as a comment in the spice deck on top of the socket connection instances, defaults to 'skt'
        :type category: str, optional
        
        """
        if self.brd_instance and self.pkg_instance:
            self.connect_psi_ins_by_map(map_fpath,self.brd_instance,
                                        self.pkg_instance,self.skt_groups,category)
        
        elif self.brd_instance and self.pkg_int_instance:
            self.connect_psi_ins_by_map(map_fpath,self.brd_instance,
                                        self.pkg_int_instance,self.skt_groups,category)
        #with open(map_fpath) as csv_file:
        #    csv_reader = csv.reader(csv_file, delimiter=delimiter)
        #    headers = next(csv_reader, None)
        #    skt_conn_map=list(csv_reader)
        #    #TODO: Parse header           
#
        #EventLogger.msg('Connecting socket using map...')               
        #conn_group=self.create_connector_instance(self.brd_instance,self.pkg_instance,
        #skt_conn_map,category=category)
        #
        #self.skt_groups[category]=conn_group
        #
        #EventLogger.msg(f'{len(conn_group.instances)} ports connected')
  
    def instantiate_tstone(self,name,fpath,ports_fpath):
        mod=Tstone()
        mod.load_data(name,fpath,ports_fpath)        
        self.tstones.append(mod)
        ins=TstoneInstance()
        ins.model=mod
        ins.name=name
        ins.ports=mod.ports
        self.tstone_ins.append(ins)

    def instantiate_spice_model(self, model_name, instance_name,ref_ports='vss*'):
        
        mod=self.spice_models[model_name]
        ins=SubcktInstance()
        ins.model=mod
        ins.name=instance_name
        ins.init_instance_port_names(ref_ports)
        return ins

    def load_spice_model(self,mod_path):
        mod=Subckt()
        mod.load_data(mod_path)
        self.spice_models[mod.name]=mod
        EventLogger.msg(f'spice model loaded: {mod.name}. path: {mod_path}')
        return mod.name


    def instantiate_die(self,ins_name,mod_path,ref_ports='vss*'):
        mod_name=self.load_spice_model(mod_path)
        self.die_instances[ins_name]=self.instantiate_spice_model(mod_name,
        ins_name,ref_ports)
        return self.die_instances[ins_name]
        


    def connect_die_using_mapfile(self,mod_path,die_conn_map,pin_r='c4_pin_r',
        pin_l='c4_pin_l',ref_ports=['vss*','gnd*','ref*','nvss*']):
        """Connect dies to a package using a connection map file.

        :param mod_path: Path to the die model
        :type mod_path: str
        :param die_conn_map: Path to the connection map file. \
        The file should be a CSV with the package port names in the first \
        column and die port names in the subsequent columns. The first row \
        should contain the names of the dies.
        :type die_conn_map: str
        :param pin_r: C4 ball resistance, defaults to 'c4_pin_r'
        :type pin_r: str, optional
        :param pin_l: C4 ball inductance, defaults to 'c4_pin_l'
        :type pin_l: str, optional
        :param ref_ports: List of port names that should be used as reference \
        ports for the die, defaults to ['vss*','gnd*','ref*','nvss*']
        :type ref_ports: list, optional
        """
        pkg=None
        if self.pkg_instance:
            pkg=self.pkg_instance
        elif self.pkg_patch_instance:
            pkg=self.pkg_patch_instance
        EventLogger.msg('Connecting dies...')
        #Read conn map        
        die_conn_maps={}
        extra_params={}
        with open(die_conn_map) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            headers = next(csv_reader, None)            
            die_names=headers[1:len(headers)]
            #init dies maps
            for die_name in die_names:
                die_conn_maps[die_name]=[]
                extra_params[die_name]=[]

            #create connection dict for each die                
            for row in csv_reader:
                pkg_port_name=row[0].replace(" ", "")
                die_ports_name=row[1:len(row)]
                if pkg_port_name:
                    for i,die_name in enumerate(die_names):
                        die_conn_map=die_conn_maps[die_name]                                        
                        die_port_name=die_ports_name[i].replace(" ", "").lower()
                        if die_port_name:
                            pins=pkg.model.get_db_port_pin_count(pkg_port_name)                        
                            die_conn_map.append([pkg_port_name,die_port_name,pins[0],
                                                 pins[1],pin_r,pin_l])
                else:
                    for i,die_name in enumerate(die_names):
                        extra_param=extra_params[die_name]
                        die_param=die_ports_name[i].replace(" ", "").lower()
                        if die_param:
                            extra_param.append(die_param)

        #Instantiate dies and C4
        for die_name in die_names:
            die_ins=self.instantiate_die(die_name,mod_path,ref_ports) 
            conn_group=self.create_connector_instance(pkg,die_ins,
            die_conn_maps[die_name],die_name)
            count = len(extra_params[die_name])
            for i, die_mod_param in enumerate(die_ins.model.params):
                for die_map_param in enumerate(extra_params[die_name]):
                    if die_mod_param[0] == die_map_param.split('=')[0]:
                        die_mod_param[1] = die_map_param.split('=')[1]
                    else:
                        print(f"Die Model Parameter Mismatch between {die_mod_param[0]} in die file and {extra_params[die_name].split('=')[0]} in csv file")
            self.die_instances[die_name]=die_ins
            self.c4_groups[die_name]=conn_group
        
        EventLogger.msg('Done')
        

    def create_connector_instance(self,instance_from,Instance_to,
        conn_map,category='skt'):        
        #TODO: check if model is already created before creating it again
        conn_mod_path=self.rl_conn_mod_file
        self.save_rl_conn_mod(conn_mod_path)

        mod_mod_name=self.load_spice_model(conn_mod_path)
                         
        conn_group=InsGroup()
        from_ports=[]
        to_ports=[]
        for row in conn_map:
            from_model_port = row[0]
            to_model_port = row[1]   
            from_port=instance_from.get_instance_port_name(from_model_port)
            to_port=Instance_to.get_instance_port_name(to_model_port)    
            if not from_port:
                EventLogger.raise_value_error(f'Port map error: model port {from_model_port} was not found in model {instance_from.model.name}. Model ports:{Instance_to.model.ports}')
            
            if not to_port:
                EventLogger.raise_value_error(f'Port map error: model port {to_model_port} was not found in model {Instance_to.model.name}. Model ports:{Instance_to.model.ports}')

            p_count = row[2]
            n_count = row[3]
            pin_r = row[4]
            pin_l = row[5]
            if p_count==0 or n_count==0:
                EventLogger.raise_warning(f"Connector port mismatch!. From: {from_model_port} and To: {to_model_port}. Connection ignored!")
                continue        
            ins_name=f'conn_from_{from_port}_to_{to_port}'            
            ins=self.instantiate_spice_model(mod_mod_name,
            ins_name)
            ins.ports=[from_port,to_port]
            ins.params['p_count']=p_count
            ins.params['n_count']=n_count            
            ins.params['pin_r']=pin_r
            ins.params['pin_l']=pin_l            
            conn_group.instances[ins_name]=ins

            from_ports.append(from_port)
            to_ports.append(to_port)
        conn_group.name=category

        self.probe_v_tran(from_ports,category)
        self.probe_v_tran(to_ports,category)        
        return conn_group

    def save_die_instances(self,file_path):
        
        folder_file = os.path.split(file_path)
        self.create_folder(folder_file[0])

        lines=[]
        for ins_name in self.die_instances:
            die_ins=self.die_instances[ins_name]                                             
            lines+=self.text_for_circuit_instance(die_ins.name,
            die_ins.model.name,die_ins.ports)
            if die_ins.model.params:
                for i in range(len(die_ins.model.params)):
                    lines.append(f"+{die_ins.model.params[i][0]} = {die_ins.model.params[i][1]}\n")
                lines.append("\n\n")
            else:
                lines.append("\n\n")
        self.create_text_file(file_path,lines) 
        
    def save_c4_instances(self,file_path):          
        lines=[]
        lines+=self.text_for_insgroups_iprobed(self.c4_groups,'itot_c4')                
        self.create_text_file(file_path,lines)        
    
    
    def save_psi_idem_ins(self,psi_ins,file_path):
        folder_file = os.path.split(file_path)
        self.create_folder(folder_file[0])        
        
        lines=[]
        a=ModPsi()        
        lines+=self.text_for_circuit_instance(psi_ins.name,
        psi_ins.model.macro.name,psi_ins.ports)

        self.create_text_file(file_path,lines)     

    def save_psi_tstone_ins(self,psi_ins,file_path):
        
        folder_file = os.path.split(file_path)
        self.create_folder(folder_file[0])        
        
        lines=[]
        
        lines+=self.text_for_tstone_instance(psi_ins.name,
        psi_ins.model.tstone_mod_name,psi_ins.ports)
        self.create_text_file(file_path,lines)  

    def save_skt_instances(self,file_path):        
        lines=[]
        lines+=self.text_for_insgroups_iprobed(self.skt_groups,'itot_skt')                        
        self.create_text_file(file_path,lines)     
    
    def save_mli_instances(self,file_path):        
        lines=[]
        lines+=self.text_for_insgroups_iprobed(self.mli_groups,'itot_mli')                        
        self.create_text_file(file_path,lines)

    def save_cap_ins(self,file_path):

        lines=[]
        lines+=self.text_for_attd_cap_instances()  
        
        self.create_text_file(file_path,lines)
    
    def save_1a_dis(self,file_path):
        
        lines=[]
        lines+=self.text_for_1a_ac_ports()            
        self.create_text_file(file_path,lines) 
    
    def save_lf_icct_instances(self,file_path):
                
        lines=[]
        lines+=self.text_for_insgroups_iprobed(self.lf_icct_groups,'itot_applied')        
        self.create_text_file(file_path,lines)
    
    def save_hf_icct_instances(self,file_path):        
        
        lines=[]
        lines+=self.text_for_insgroups_iprobed(self.hf_icct_groups,'itot_applied')        
        self.create_text_file(file_path,lines)

    def save_probe_tran_v_file(self,file_path):        
        lines=[]
        lines+=self.text_for_probe_tran_v_ports()            
        self.create_text_file(file_path,lines) 
    
    def save_probe_ac_v_file(self,file_path):
        folder_file = os.path.split(file_path)
        self.create_folder(folder_file[0])


        lines=[]
        lines+=self.text_for_probe_ac_ports()            
        self.create_text_file(file_path,lines) 
    
    def save_rl_conn_mod(self,file_path):   
        lines=[]
        lines.append(f'.subckt rl_conn term_a term_b\n')
        lines.append(f'+pin_r=1m pin_l=1n\n')
        lines.append(f'+p_count=1 n_count=1\n')
        lines.append(f'r term_a mid \'pin_r/p_count+pin_r/n_count\'\n')
        lines.append(f'l mid term_b \'pin_l/p_count+pin_l/n_count\'\n')
        lines.append(f'.ends\n')
        self.create_text_file(file_path,lines)
    
    def text_for_cap_1leg(self):   
        lines=[]
        lines.append(f'.subckt cap_1leg term_a term_b\n')
        lines.append(f'+C=1u R=1u L=1f NCAPS=1\n')        
        lines.append(f'C term_a mid1 \'C*NCAPS\'\n')
        lines.append(f'R mid1 mid2 \'R/NCAPS\'\n')
        lines.append(f'L mid2 term_b \'L/NCAPS\'\n')
        lines.append(f'.ends\n')
        return lines     
        
    def save_vrstavggen(self,file_path,ph_count,r1,r2,r3,c1,c2,c3,lout,avp,rout,vid):

        folder_file = os.path.split(file_path)
        self.create_folder(folder_file[0])
                        
        lines=[]
        lines.append("******************************************************************")
        lines.append(f"*Generalized VR State Average Model {ph_count} phases\n")
        lines.append("*Created by E. J. Pole II\n")
        lines.append("*Updated to handle single or dual-ended modeling - 08/22/2008\n")
        lines.append("*******************************************************************\n")
        lines.append("\n")
        lines.append("* Compensation components for numbering reference\n")
        lines.append("\n")
        lines.append("* +---------+   +----+   +--+   +--+   +--+   +--+\n")
        lines.append("* | vsensep |---|+   |-+-|r3|---|c3|-+-|r2|---|c2|-+\n")
        lines.append("* +---------+   |    | | +--+   +--+ | +--+   +--+ |\n")
        lines.append("*               |diff| |diff         |             |\n")
        lines.append("\n")
        lines.append("* +---------+   |    | |    +--+     |    +--+     |\n")
        lines.append("* | vsensen |---|-   | +----|r1|-----+----|c1|-----+\n")
        lines.append("* +---------+   +----+      +--+     |    +--+     |\n")
        lines.append("*                                    |fb           |\n")
        lines.append("*                                    | +-------+   |\n")
        lines.append("*                                    +-| error |---+comp\n")
        lines.append("*                                      +-------+\n")
        lines.append("\n")
        lines.append("* Set parhier option to 'local'\n")
        lines.append("* localizing all parameters in subcircuit\n")
        lines.append("* preventing interference between parameters in other files\n")
        lines.append("* allowing override of values on subcircuit calls\n")
        lines.append("* and use of '.alter' to run multiple cases at a time\n")
        lines.append("\n")
        lines.append(".option parhier=local\n")
        lines.append("\n")
        lines.append("*****************************************************\n")
        lines.append("* State Average Model  \n")
        lines.append("*****************************************************\n")
        lines.append(".option acout=1 \n")
        lines.append("\n")
        phs=''
        for i in range(1,ph_count+1,1):
            phs+=f'p{i} '
        lines.append(f".subckt vrstavggen sensep sensen g0 {phs} \n")
        lines.append("*Connect 'sensep' to positive differential feedback sense point\n")
        lines.append("*Connect 'sensen' to negative differential feedback sense point\n")
        lines.append("*Connect 'g0' to '0' for single-ended model or a reasonable VR ground connection node for a dual-ended model. This should be at or near the ground node equivalent to the phase node(s)\n")
        lines.append("*Connect 'px' to the phase inductor(s) output nodes\n")
        lines.append("* Parameters used in the model\n")
        lines.append(".param\n")
        lines.append(f"+ r1 = '{r1}'\n")
        lines.append(f"+ r2 = '{r2}'\n")
        lines.append(f"+ r3 = '{r3}'\n")
        lines.append(f"+ c1 = '{c1}'\n")
        lines.append(f"+ c2 = '{c2}'\n")
        lines.append(f"+ c3 = '{c3}'\n")
        lines.append("+ duty = '75' * Maximum duty cycle in percentage\n")
        lines.append("+ egain = '4000' * Gain of error amp\n")
        lines.append(f"+ lout = '{lout}' * The per phase inductor value in Henries\n")
        lines.append(f"+ avp = '{avp}' * Adaptive Voltage Positioning setting in ohms\n")
        lines.append(f"+ rout = '{rout}' * dcr resistance of output inductor per phase value in ohms\n")
        lines.append(f"+ vid = '{vid}' * Output setpoint in volts\n")
        lines.append("+ vin = '12' * Input voltage. Usually 12V\n")
        lines.append("+ vramp = '1.5' * peak ramp voltage in volts\n")
        lines.append("+ np = 3 * number of phases. Can be 1, 2, 3, 4, 5, 6, 7 ,8 ,9 or 10.\n")
        lines.append("* Parameters NOT used in the model\n")
        lines.append("+ fs = 300000 * per phase switching frequency\n")
        lines.append("+ bode = 0\n")
        lines.append("\n")
        lines.append("* Compensation network\n")
        lines.append("\n")
        lines.append("r1 compin fb 'r1'\n")
        lines.append("r2 fb r2c2 'r2'\n")
        lines.append("r3 compin r3c3 'r3'\n")
        lines.append("c1 fb comp 'c1'\n")
        lines.append("c2 r2c2 comp 'c2'\n")
        lines.append("c3 r3c3 fb 'c3'\n")
        lines.append("\n")
        lines.append(".if (bode==1)\n")
        lines.append("Vfdbk compin diff dc 0 ac 1m\n")
        lines.append("*Pre 2013 Statements\n")
        lines.append("*.probe ac vdbplant= par('20*log10(vm(diff,g0)/vm(comp,g0))')     vpplant= par('vp(diff,g0)-vp(comp,g0)')\n")
        lines.append("*.probe ac vdbsys  = par('20*log10(vm(diff,g0)/vm(compin,g0))')   vpsys  = par('vp(diff,g0)-vp(compin,g0)')\n")
        lines.append("*.probe ac\n")
        lines.append("*+ vdb(diff,compin),vp(diff,compin)  ** closed loop\n")
        lines.append("*+ vdb(diff,comp),vp(diff,comp)      **plant\n")
        lines.append("*+ vdb(comp,compin),vp(comp,compin)\n")
        lines.append("*Post 2013 Statements\n")
        lines.append(".probe ac vdbsys=par('20*log10(vm(diff,0)/vm(compin,0))')\n")
        lines.append(".probe ac vpsys=par('vp(diff,0) - vp(compin,0)')\n")
        lines.append(".probe ac vdbplant=par('20*log10(vm(diff,0)/vm(comp,0))')\n")
        lines.append(".probe ac vplant=par('vp(diff,0) - vp(comp,0)')\n")
        lines.append(".probe ac vdbcomp=par('20*log10(vm(comp,0)/vm(compin,0))')\n")
        lines.append(".probe ac vpcomp=par('vp(comp,0) - vp(compin,0)')\n")
        #lines.append(".MEASURE AC PG FIND vdb(diff,comp) AT='UGB'\n")
        #lines.append(".MEASURE AC PP FIND vp(diff,comp) AT='UGB'\n")
        #lines.append(".MEASURE AC SG FIND vdb(diff,compin) AT='UGB'\n")
        #lines.append(".MEASURE AC SP FIND vp(diff,compin) AT='UGB'\n")
        #lines.append(".MEASURE AC BW WHEN vdb(diff,compin)=0\n")
        #lines.append(".MEASURE AC PM FIND vp(diff,compin) AT='BW'\n")
        lines.append(".elseif (bode==0)\n")
        lines.append("    .connect compin diff\n")
        lines.append(".endif\n")
        lines.append("\n")
        lines.append("* Error 'amp'\n")
        lines.append("\n")
        lines.append("vvid vid g0 'vid'\n")
        lines.append("ecomp comp g0 vcvs vid fb 'egain' max='vramp'\n")
        lines.append("\n")
        lines.append("* Differential sense input calculation\n")
        lines.append("\n")
        lines.append("ediff diff g0 vol='v(sensep,g0)-v(sensen,g0)'\n")
        lines.append("\n")
        lines.append(".if (avp!=0)\n")
        #lines.append("gdroop fb g0 vol='i(eout)*avp/r1'\n")
        lines.append("gdroop fb g0 cur='i(eout)*avp/r1'\n")
        lines.append(".endif\n")
        lines.append("\n")
        lines.append("* Output\n")
        lines.append("\n")
        lines.append("eout swn g0 vol='vin*v(comp,g0)/vramp' max='vin*duty/100' min=0 \n")
        lines.append("\n")
        for i in range(1,ph_count+1,1):
            lines.append(f"lp{i} swn lp{i}rp{i} 'lout'\n")
            lines.append(f"rp{i} lp{i}rp{i} p{i} 'rout'\n")        
            lines.append(f".probe ac v(p{i})        * dummy probe remove after model is complete\n")
            lines.append("\n")

        lines.append(".ends\n")

        
        self.create_text_file(file_path,lines) 

    def save_tlvrstavggen(self,file_path,ph_count,r1,r2,r3,c1,c2,c3,vid,avp,
        l_transformer='100n',lc_filter='70n',rdc_Lc='0.125m',rout_p='0.145m',
        rout_s='0.6m',k_par='0.89'):

        folder_file = os.path.split(file_path)
        self.create_folder(folder_file[0])
                        
        lines=[]
        lines.append("******************************************************************")
        lines.append(f"*Generalized TLVR State Average Model {ph_count} phases\n")
        lines.append("*Created by E. J. Pole II\n")
        lines.append("*Updated to handle single or dual-ended modeling - 08/22/2008\n")
        lines.append("*Updated to use bode option and setting eout min=0, to fix overshoot issue -10/17/2017 by Franco\n")
        lines.append("*Updated to represetn TLVR\n")
        lines.append("*******************************************************************\n")
        lines.append("\n")
        lines.append("* Compensation components for numbering reference\n")
        lines.append("\n")
        lines.append("* +---------+   +----+   +--+   +--+   +--+   +--+\n")
        lines.append("* | vsensep |---|+   |-+-|r3|---|c3|-+-|r2|---|c2|-+\n")
        lines.append("* +---------+   |    | | +--+   +--+ | +--+   +--+ |\n")
        lines.append("*               |diff| |diff         |             |\n")
        lines.append("\n")
        lines.append("* +---------+   |    | |    +--+     |    +--+     |\n")
        lines.append("* | vsensen |---|-   | +----|r1|-----+----|c1|-----+\n")
        lines.append("* +---------+   +----+      +--+     |    +--+     |\n")
        lines.append("*                                    |fb           |\n")
        lines.append("*                                    | +-------+   |\n")
        lines.append("*                                    +-| error |---+comp\n")
        lines.append("*                                      +-------+\n")
        lines.append("\n")
        lines.append("* Set parhier option to 'local'\n")
        lines.append("* localizing all parameters in subcircuit\n")
        lines.append("* preventing interference between parameters in other files\n")
        lines.append("* allowing override of values on subcircuit calls\n")
        lines.append("* and use of '.alter' to run multiple cases at a time\n")
        lines.append("\n")
        lines.append(".option parhier=local\n")
        lines.append("\n")
        lines.append("*****************************************************\n")
        lines.append("* State Average Model  \n")
        lines.append("*****************************************************\n")
        lines.append(".option acout=1 \n")
        lines.append("\n")
        phs=''
        for i in range(1,ph_count+1,1):
            phs+=f'p{i} '
        lines.append(f".subckt vrstavggen sensep sensen g0 {phs} \n")
        lines.append("*Connect 'sensep' to positive differential feedback sense point\n")
        lines.append("*Connect 'sensen' to negative differential feedback sense point\n")
        lines.append("*Connect 'g0' to '0' for single-ended model or a reasonable VR ground connection node for a dual-ended model. This should be at or near the ground node equivalent to the phase node(s)\n")
        lines.append("*Connect 'px' to the phase inductor(s) output nodes\n")
        lines.append("* Parameters used in the model\n")
        lines.append(".param\n")
        lines.append(f"+ r1 = '{r1}'\n")
        lines.append(f"+ r2 = '{r2}'\n")
        lines.append(f"+ r3 = '{r3}'\n")
        lines.append(f"+ c1 = '{c1}'\n")
        lines.append(f"+ c2 = '{c2}'\n")
        lines.append(f"+ c3 = '{c3}'\n")
        lines.append(f"+ l_transformer = '{l_transformer}' * The per phase inductor value in Henries\n")
        lines.append(f"+ lc_filter = '{lc_filter}' \n")
        lines.append(f"+ rdc_Lc = '{rdc_Lc}' \n")
        lines.append(f"+ rout_p = '{rout_p}' \n")
        lines.append(f"+ rout_s = '{rout_s}' \n")
        lines.append(f"+ k_par = '{k_par}' \n")
        lines.append("+ duty = '75' * Maximum duty cycle in percentage\n")
        lines.append("+ egain = '4000' * Gain of error amp\n")    
        lines.append(f"+ avp = '{avp}' * Adaptive Voltage Positioning setting in ohms\n")        
        lines.append(f"+ vid = '{vid}' * Output setpoint in volts\n")
        lines.append("+ vin = '12' * Input voltage. Usually 12V\n")
        lines.append("+ vramp = '1.5' * peak ramp voltage in volts\n")
        lines.append("+ np = 3 * number of phases. Can be 1, 2, 3, 4, 5, 6, 7 ,8 ,9 or 10.\n")
        lines.append("* Parameters NOT used in the model\n")
        lines.append("+ fs = 300000 * per phase switching frequency\n")
        lines.append("+ bode = 0\n")
        lines.append("\n")
        lines.append("* Compensation network\n")
        lines.append("\n")
        lines.append("r1 compin fb 'r1'\n")
        lines.append("r2 fb r2c2 'r2'\n")
        lines.append("r3 compin r3c3 'r3'\n")
        lines.append("c1 fb comp 'c1'\n")
        lines.append("c2 r2c2 comp 'c2'\n")
        lines.append("c3 r3c3 fb 'c3'\n")
        lines.append("\n")
        lines.append(".if (bode==1)\n")
        lines.append("Vfdbk compin diff dc 0 ac 1m\n")
        lines.append("*Pre 2013 Statements\n")
        lines.append("*.probe ac vdbplant= par('20*log10(vm(diff,g0)/vm(comp,g0))')     vpplant= par('vp(diff,g0)-vp(comp,g0)')\n")
        lines.append("*.probe ac vdbsys  = par('20*log10(vm(diff,g0)/vm(compin,g0))')   vpsys  = par('vp(diff,g0)-vp(compin,g0)')\n")
        lines.append("*.probe ac\n")
        lines.append("*+ vdb(diff,compin),vp(diff,compin)  ** closed loop\n")
        lines.append("*+ vdb(diff,comp),vp(diff,comp)      **plant\n")
        lines.append("*+ vdb(comp,compin),vp(comp,compin)\n")
        lines.append("*Post 2013 Statements\n")
        lines.append(".probe ac vdbsys=par('20*log10(vm(diff,0)/vm(compin,0))')\n")
        lines.append(".probe ac vpsys=par('vp(diff,0) - vp(compin,0)')\n")
        lines.append(".probe ac vdbplant=par('20*log10(vm(diff,0)/vm(comp,0))')\n")
        lines.append(".probe ac vplant=par('vp(diff,0) - vp(comp,0)')\n")
        lines.append(".probe ac vdbcomp=par('20*log10(vm(comp,0)/vm(compin,0))')\n")
        lines.append(".probe ac vpcomp=par('vp(comp,0) - vp(compin,0)')\n")
        #lines.append(".MEASURE AC PG FIND vdb(diff,comp) AT='UGB'\n")
        #lines.append(".MEASURE AC PP FIND vp(diff,comp) AT='UGB'\n")
        #lines.append(".MEASURE AC SG FIND vdb(diff,compin) AT='UGB'\n")
        #lines.append(".MEASURE AC SP FIND vp(diff,compin) AT='UGB'\n")
        #lines.append(".MEASURE AC BW WHEN vdb(diff,compin)=0\n")
        #lines.append(".MEASURE AC PM FIND vp(diff,compin) AT='BW'\n")
        lines.append(".elseif (bode==0)\n")
        lines.append("    .connect compin diff\n")
        lines.append(".endif\n")
        lines.append("\n")
        lines.append("* Error 'amp'\n")
        lines.append("\n")
        lines.append("vvid vid g0 'vid'\n")
        lines.append("ecomp comp g0 vcvs vid fb 'egain' max='vramp'\n")                
        lines.append("\n")
        lines.append("* Differential sense input calculation\n")
        lines.append("\n")
        lines.append("ediff diff g0 vol='v(sensep,g0)-v(sensen,g0)'\n")        
        lines.append("\n")
        lines.append(".if (avp!=0)\n")        
        lines.append("gdroop fb g0 cur='i(eout)*avp/r1'\n")
        lines.append(".endif\n")
        lines.append("\n")
        lines.append("* Output\n")
        lines.append("\n")
        lines.append("eout swn g0 vol='vin*v(comp,g0)/vramp' max='vin*duty/100' min=0 \n")
        lines.append("\n")
        for i in range(1,ph_count+1,1):
            lines.append(f"lp{i} swn lp{i}rp{i} 'l_transformer'\n")
            lines.append(f"rp{i} lp{i}rp{i} p{i} 'rout_p'\n")                    
            lines.append("\n")

        lines.append("\n")
        for i in range(1,ph_count+1,1):
            if i==1:
                lines.append(f"lp{i}s 0 ls{i}rp{i} 'l_transformer'\n")
            else:
                lines.append(f"lp{i}s p{i-1}s ls{i}rp{i} 'l_transformer'\n")

            if i<ph_count:
                lines.append(f"rp{i}s ls{i}rp{i} p{i}s 'rout_s'\n")                    
            else:
                lines.append(f"rp{i}s ls{i}rp{i} lc1 'rout_s'\n")                                    
            lines.append("\n")

        lines.append("lc1 lc1 lc1r 'lc_filter'\n")
        lines.append("rlc1	lc1r 0 'rdc_Lc'\n")

        for i in range(1,ph_count+1,1):            
            lines.append(f"K{i} 	lp{i} 	lp{i}s 	'k_par'\n")
        
        line=".probe tran total_VR = par('"
        for i in range(1,ph_count+1,1):                      
            line+=f"i(rp{i})"
            if i<=ph_count:
                line+="+"
        line+="')"          

        lines.append(".probe tran i(lc1)\n")
        
        lines.append(".ends\n")

        
        self.create_text_file(file_path,lines) 
    
    def set_global_param(self,param='my_param',value='1',category='User parameters',desc=[]):
        if category not in self.glob_params.keys():            
            self.glob_params[category]={}        
        
        cat=self.glob_params[category]
        cat[param]=[value,desc]
    
    def find_die_instances_ports_by_name(self,port_wildcards='*cmd*',Instance_wildcards='*'):
        """Find ports in the die instances that match the given wildcards.

        :param port_wildcards: Wildcard or list of wildcards that should be \
        used to match the port names, defaults to '*cmd*'
        :type port_wildcards: str, optional
        :param Instance_wildcards: LWildcard or list of wildcards that should \
        be used to match the die instance names, defaults to '*'
        :type Instance_wildcards: str, optional
        :return: List of ports that match the wildcard
        :rtype: List[str]
        """
        ports=[]
        for die_name in self.die_instances:
            if TextProcessor.match(die_name,Instance_wildcards):
                for port_name in self.die_instances[die_name].ports:
                    if TextProcessor.match(port_name,port_wildcards):
                        ports.append(port_name)
        return ports
    
    def find_pkg_vr_sense_port(self,wildcard=['*sp*','*sense*']):        
        sense_port=self.pkg_instance.find_ports_by_name(wildcard)
        if len(sense_port)>0:
            sense_port=sense_port[0]
        return sense_port
    

    def find_brd_vr_ph_ports(self,wildcard=None):
        ph_ports=[]
        if wildcard:
            ph_ports=self.brd_instance.find_ports_by_name(wildcard)
        else:
            ph_ports=self.brd_instance.find_ports_by_comp_name('L*')
        return ph_ports

    def connect_vrstavggen(self,ph_ports=None,sense_port=None,vid='vid',avp='avp',lout='lout',
        rout='rout',bode='bode',r1='r1',r2='r2',r3='r3',c1='c1',c2='c2',c3='c3'):
        """Connects the  state average Voltage Regulator (VR) model with Type III\
        compensator

        :param ph_ports: List of phase ports, defaults to None
        :type ph_ports: List or None, optional
        :param sense_port: Sense point port, defaults to None
        :type sense_port: str or None, optional
        :param vid: VR nominal voltage , defaults to 'vid'
        :type vid: str, optional
        :param avp: VR AVP, defaults to 'avp'
        :type avp: str, optional
        :param lout: VR output Inductance per phase, defaults to 'lout'
        :type lout: str, optional
        :param rout: VR output Resistance per phase, defaults to 'rout'
        :type rout: str, optional
        :param bode: Enable the Bode mode in the VR model, defaults to 'bode'
        :type bode: str, optional
        :param r1: compensator r1, defaults to 'r1'
        :type r1: str, optional
        :param r2: compensator r2, defaults to 'r2'
        :type r2: str, optional
        :param r3: compensator r3, defaults to 'r3'
        :type r3: str, optional
        :param c1: compensator c1, defaults to 'c1'
        :type c1: str, optional
        :param c2: compensator c2, defaults to 'c2'
        :type c2: str, optional
        :param c3: compensator c3, defaults to 'c3'
        :type c3: str, optional
        """
        EventLogger.msg('Creating and connecting VR...')

        if not ph_ports:
            EventLogger.info('Phase ports not provided. attepting to find ports automatically...')
            ph_ports=self.find_brd_vr_ph_ports()
            if ph_ports:
                EventLogger.info(f'Phase ports identified: {ph_ports}')
            else:
                EventLogger.raise_value_error('Phase ports not available, VR cannot be connected!')
        
        if not sense_port:
            EventLogger.info('Sense point not provided. attepting to find port automatically...')
            sense_port=self.find_pkg_vr_sense_port()
            if sense_port:                
                EventLogger.info('Sense point identified: ' + sense_port)            
            else:
                EventLogger.raise_value_error('Sense ports not available, VR cannot be connected!')

        elif isinstance(sense_port,list):
            if len(sense_port)>1:
                EventLogger.raise_value_error('More that one sense point provided, VR cannot be connected!')
            else:
                sense_port=sense_port[0]
        
        self.ph_count=len(ph_ports)
        self.save_vrstavggen(self.vr_mod_file,self.ph_count,r1,r2,r3,c1,c2,c3,
        lout,avp,rout,vid)

        mod_name=self.load_spice_model(self.vr_mod_file)

        self.vr_instance=self.instantiate_spice_model(mod_name,
        'VR')
        self.vr_instance.ports=[sense_port,'0','0']+ph_ports

                        
        self.vr_instance.params['vid']=vid
        self.vr_instance.params['avp']=avp
        self.vr_instance.params['lout']=lout
        self.vr_instance.params['rout']=rout
        self.vr_instance.params['bode']=bode
        self.vr_instance.params['r1']=r1
        self.vr_instance.params['r2']=r2
        self.vr_instance.params['r3']=r3
        self.vr_instance.params['c1']=c1
        self.vr_instance.params['c2']=c2
        self.vr_instance.params['c3']=c3
        

        #Add probes
        self.probe_v_tran(sense_port,'vr')        
        self.probe_v_tran(ph_ports,'vr')        

        self.probe_v_ac(sense_port,'vr')        
        self.probe_v_ac(ph_ports,'vr')        
         
        EventLogger.msg('Done')
    
    def connect_tlvrstavggen(self,ph_ports=None,sense_port=None,vid='vid',avp='avp',
        bode='bode',r1='r1',r2='r2',r3='r3',c1='c1',c2='c2',c3='c3',
        l_transformer='l_transformer',lc_filter='lc_filter',rdc_lc='rdc_lc',
        rout_p='rout_p',rout_s='rout_s',k_par='k_par'):
        """Connects the  state average Voltage Regulator (VR) model with Type III\
        compensator

        :param ph_ports: List of phase ports, defaults to None
        :type ph_ports: List or None, optional
        :param sense_port: Sense point port, defaults to None
        :type sense_port: str or None, optional
        :param vid: VR nominal voltage , defaults to 'vid'
        :type vid: str, optional
        :param avp: VR AVP, defaults to 'avp'
        :type avp: str, optional        
        :param bode: Enable the Bode mode in the VR model, defaults to 'bode'
        :type bode: str, optional
        :param r1: compensator r1, defaults to 'r1'
        :type r1: str, optional
        :param r2: compensator r2, defaults to 'r2'
        :type r2: str, optional
        :param r3: compensator r3, defaults to 'r3'
        :type r3: str, optional
        :param c1: compensator c1, defaults to 'c1'
        :type c1: str, optional
        :param c2: compensator c2, defaults to 'c2'
        :type c2: str, optional
        :param c3: compensator c3, defaults to 'c3'
        :type c3: str, optional
        """
        EventLogger.msg('Creating and connecting VR...')

        if not ph_ports:
            EventLogger.info('Phase ports not provided. attepting to find ports automatically...')
            ph_ports=self.brd_instance.find_ports_by_comp_name('L*')
            if ph_ports:
                EventLogger.info(f'Phase ports identified: {ph_ports}')
            else:
                EventLogger.raise_value_error('Phase ports not available, VR cannot be connected!')
        
        if not sense_port:
            EventLogger.info('Sense point not provided. attepting to find port automatically...')
            sense_ports=self.pkg_instance.find_ports_by_name(['*sp*','*sense*'])
            if len(sense_ports)==1:
                sense_port=sense_ports[0]
                EventLogger.info('Sense point identified: ' + sense_port)
            elif len(sense_ports)==0:
                EventLogger.raise_value_error('Sense ports not available, VR cannot be connected!')
            else:
                EventLogger.raise_value_error('More that one sense point identified, VR cannot be connected!')
        elif isinstance(sense_port,list):
            if len(sense_port)>1:
                EventLogger.raise_value_error('More that one sense point provided, VR cannot be connected!')
            else:
                sense_port=sense_port[0]
        
        self.ph_count=len(ph_ports)
        self.save_tlvrstavggen(self.tlvr_mod_file,self.ph_count,r1,r2,r3,c1,c2,
        c3,vid,avp,l_transformer,lc_filter,rdc_lc,rout_p,rout_s,k_par)        

        mod_name=self.load_spice_model(self.tlvr_mod_file)

        self.vr_instance=self.instantiate_spice_model(mod_name,
        'VR')
        self.vr_instance.ports=[sense_port,'0','0']+ph_ports
        
        self.vr_instance.params['vid']=vid
        self.vr_instance.params['avp']=avp

        self.vr_instance.params['l_transformer']=l_transformer
        self.vr_instance.params['lc_filter']=lc_filter
        self.vr_instance.params['rdc_lc']=rdc_lc
        self.vr_instance.params['rout_p']=rout_p
        self.vr_instance.params['rout_s']=rout_s
        self.vr_instance.params['k_par']=k_par

        self.vr_instance.params['bode']=bode
        self.vr_instance.params['r1']=r1
        self.vr_instance.params['r2']=r2
        self.vr_instance.params['r3']=r3
        self.vr_instance.params['c1']=c1
        self.vr_instance.params['c2']=c2
        self.vr_instance.params['c3']=c3
        

        #Add probes
        self.probe_v_tran(sense_port,'vr')        
        self.probe_v_tran(ph_ports,'vr')        

        self.probe_v_ac(sense_port,'vr')        
        self.probe_v_ac(ph_ports,'vr')        
         
        EventLogger.msg('Done')
            
    def connect_lf_icct_by_model_filename(self,ports,mod_path,groupname='icct',
        params=None):
        
        EventLogger.msg('connecting LF icct...')        
        mod_name=self.load_spice_model(mod_path)
        mod=self.spice_models[mod_name]
        
        icct_group=InsGroup()
        
        for p in ports:
            ins_name=p
            ins=self.instantiate_spice_model(mod.name,
            ins_name)            
            if params:
                ins.params=params
            ins.ports=[p,'0']          
            icct_group.instances[ins_name]=ins
            icct_group.name=groupname
            self.lf_icct_groups[groupname]=icct_group
        
        self.probe_v_tran(ports,'LF')

        EventLogger.msg('Done')

    def clear_hf_icct_instances(self):
        self.hf_icct_groups={}
    def connect_hf_icct_by_model_filename(self,ports,mod_path,groupname='icct',params=None):


        EventLogger.msg('connecting HF icct...')

        mod_name=self.load_spice_model(mod_path)
        mod=self.spice_models[mod_name]
        
        icct_group=InsGroup()
        
        for p in ports:
            ins_name=p
            ins=self.instantiate_spice_model(mod.name,
            ins_name)            
            if params:
                ins.params=params
            ins.ports=[p,'0']          
            icct_group.instances[ins_name]=ins
            icct_group.name=groupname
            self.hf_icct_groups[groupname]=icct_group
        
        self.probe_v_tran(ports,'HF')

        EventLogger.msg('Done')
                
    
    def text_for_if(self,condition):
        lines=[]
        lines.append(f'.if ({condition})\n')
        return lines
    def text_for_elseif(self,condition):
        lines=[]
        lines.append(f'.elseif ({condition})\n')
        return lines
    def text_for_else(self):
        lines=[]
        lines.append('.else\n')
        return lines
    def text_for_endif(self):
        lines=[]
        lines.append(f'.endif\n')
        return lines
    def save_lin_port_list(self):
        fpath=Io.update_file_extension(self.main_lin_file,'.txt')        
        fpath=Io.custom_file_path(fpath,'_ports') 
        Io.create_text_file(fpath,self.lin_ports)               
    
    

    def save_deck_dependencies(self): 

        EventLogger.msg('Saving instances...')
        
        if self.die_instances:
            self.save_die_instances(self.die_ins_file)
        
        if self.c4_groups:
            self.save_c4_instances(self.c4_ins_file)        
        
        if self.pkg_instance:
            self.save_psi_idem_ins(self.pkg_instance,self.pkg_ins_file)                            
            self.save_psi_tstone_ins(self.pkg_instance,self.pkg_tstone_ins_file)
        if self.pkg_patch_instance:
            self.save_psi_idem_ins(self.pkg_patch_instance,self.pkg_patch_ins_file)                            
            self.save_psi_tstone_ins(self.pkg_patch_instance,self.pkg_patch_tstone_ins_file)
        if self.pkg_int_instance:
            self.save_psi_idem_ins(self.pkg_int_instance,self.pkg_int_ins_file)                            
            self.save_psi_tstone_ins(self.pkg_int_instance,self.pkg_int_tstone_ins_file)
        if self.brd_instance:                        
            self.save_psi_idem_ins(self.brd_instance,self.brd_ins_file)            
            self.save_psi_tstone_ins(self.brd_instance,self.brd_tstone_ins_file)
        
        if self.mli_groups:
            self.save_mli_instances(self.mli_ins_file)        

        if self.skt_groups:
            self.save_skt_instances(self.skt_ins_file)        
        if self.attd_cap_groups:
            self.save_cap_ins(self.cap_ins_file)    
        
        if self.lf_icct_groups:
            self.save_lf_icct_instances(self.lf_icct_ins_file)   

        if self.hf_icct_groups:
            self.save_hf_icct_instances(self.hf_icct_ins_file)             
        if self.ac_1a_ports:
            self.save_1a_dis(self.onea_ac_file)

        if self.probe_v_tran_ports:
            self.save_probe_tran_v_file(self.tran_vprobe_file)        
        if self.probe_v_ac_ports:
            self.save_probe_ac_v_file(self.ac_vprobe_file)
        
        if self.lin_ports:
            self.save_lin_port_list()

        EventLogger.msg('Done')
            

    def text_indent(self,lines):        
        new_lines=[]
        for line in lines:            
            new_line='   '+line
            new_lines.append(new_line)        
        return new_lines
    
    def text_comment(self,lines):        
        new_lines=[]
        for line in lines:            
            new_line='*'+line
            new_lines.append(new_line)        
        return new_lines
    
    def text_for_psi_external_instance(self,sel_param,model,
        tstone_ins_path,cir_ins_path,start):
                
        tstone_mod_name=model.tstone_mod_name
        tstone_path=model.tstone_path
        
        cir_path=model.macro.fpath               
        
        lines=[]
        lines+=self.text_for_if(f'{sel_param} == {PsiModelType.TSTONE.value}')
        if tstone_path:
            lines+=self.text_indent(self.text_for_tstonefile_include(tstone_mod_name,tstone_path,start))        
            lines+=self.text_indent(self.text_for_include(tstone_ins_path,start))
        else:
            tstone_path='./placeholder.snp'
            lines+=self.text_indent(self.text_for_comment('Include sparameter model here'))
            lines+=self.text_indent(self.text_comment(self.text_for_tstonefile_include(tstone_mod_name,tstone_path,start)))        
            lines+=self.text_indent(self.text_for_include(tstone_ins_path,start))
            
        lines+=self.text_for_elseif(f'{sel_param} == {PsiModelType.MACRO1.value}')
        lines+=self.text_indent(self.text_for_include(cir_path,start))          
        lines+=self.text_indent(self.text_for_include(cir_ins_path,start))        

        lines+=self.text_for_endif()
        return lines
    
    def text_for_tstone_instances(self,start):
        lines=[]
        if self.tstone_ins:
            lines+=self.text_for_comment('Tstone_instances')
            for ins in self.tstone_ins:
                lines+=self.text_for_tstonefile_include(ins.name,ins.model.fpath,start)
                lines+=self.text_for_tstone_instance(ins.name,
                ins.name,ins.ports)
        return lines
                


    def set_analysis_type(self,analysis_type=AnalysisType.ZF):
        desc=f'The integer parameter \'{self.analysis_type}\' ' \
        'determines the type of analysis.\n'\
        '1 for Bode analysis, 2 for to Z(F), '\
        '3 for low-frequency analysis, '\
        'and 4 for high-frequency analysis.'
        self.set_global_param(self.analysis_type,analysis_type.value,'Analysis type',desc)

    def set_pkg_model_type(self,pkg_model=PsiModelType.MACRO1):
        
        desc='The integer param \'{self.pkg_id}\' specifies which model to use '\
        'in the simulation.\n0 for S-parameters, '\
        '1 for the IDEM macromodel #1.\n'\
        'Additional values of 2, 3, etc. can be used if multiple '\
        'macromodels are available.'
        self.set_global_param(self.pkg_id,pkg_model.value,'PSI models control',desc)

    def set_brd_model_type(self,brd_model=PsiModelType.MACRO1):
        desc=f'The integer param \'{self.brd_id}\' specifies which model to use '\
        'in the simulation.\n0 for S-parameters, '\
        '1 for the IDEM macromodel #1.\n'\
        'Additional values of 2, 3, etc. can be used if multiple '\
        'macromodels are available.'
        self.set_global_param(self.brd_id,brd_model.value,'PSI models control',desc)

        
    def load_vr_comp_from_file(self):
        data=self.vr_info.load_comp_file(self.vr_tune_compfile)
        for par in data:
            self.update_user_data_param(par,data[par])
        self.update_user_data_param('avp',self.vr_info.avp)
        self.update_user_data_param('vid',self.vr_info.vid)
        self.update_user_data_param('lout',self.vr_info.lout)
        self.update_user_data_param('rout',self.vr_info.rout)
        #TLVR
        self.update_user_data_param('l_transformer',self.vr_info.l_transformer)
        self.update_user_data_param('lc_filter',self.vr_info.lc_filter)
        self.update_user_data_param('rdc_lc',self.vr_info.rdc_lc)
        self.update_user_data_param('rout_p',self.vr_info.rout_p)
        self.update_user_data_param('rout_s',self.vr_info.rout_s)
        self.update_user_data_param('k_par',self.vr_info.k_par)
        
        

    def text_for_vr_tune_conns(self):        
        lines=[]
        lines+=self.text_for_comment('vr tuning setup')
        lines+=self.text_indent(self.ac_analysis_line)    

        if not self.vr_info.tlvr_enabled:
            lines.append(f'.param lout=\'{self.vr_info.lout}\'\n')
            lines.append(f'.param rout=\'{self.vr_info.rout}\'\n')
            for i in range(len(self.vr_info.phs)):                
                lines.append(f'lp{i} swn lp{i}rp{i} \'lout\'\n')
                lines.append(f'rp{i} lp{i}rp{i} {self.vr_info.phs[i]} \'rout\'\n')
        else:
            ph_count=len(self.vr_info.phs)
            
            lines.append(f'.param l_transformer=\'{self.vr_info.l_transformer}\'\n')            
            lines.append(f'.param lc_filter=\'{self.vr_info.lc_filter}\'\n')            
            lines.append(f'.param rdc_lc=\'{self.vr_info.rdc_lc}\'\n')            
            lines.append(f'.param rout_p=\'{self.vr_info.rout_p}\'\n')            
            lines.append(f'.param rout_s=\'{self.vr_info.rout_s}\'\n')            
            lines.append(f'.param k_par=\'{self.vr_info.k_par}\'\n')            

            for i in range(1,ph_count+1,1):
                lines.append(f"lp{i} swn lp{i}rp{i} 'l_transformer'\n")
                lines.append(f"rp{i} lp{i}rp{i} {self.vr_info.phs[i-1]} 'rout_p'\n")                    
                lines.append("\n")

            lines.append("\n")
            for i in range(1,ph_count+1,1):
                if i==1:
                    lines.append(f"lp{i}s 0 ls{i}rp{i} 'l_transformer'\n")
                else:
                    lines.append(f"lp{i}s p{i-1}s ls{i}rp{i} 'l_transformer'\n")

                if i<ph_count:
                    lines.append(f"rp{i}s ls{i}rp{i} p{i}s 'rout_s'\n")                    
                else:
                    lines.append(f"rp{i}s ls{i}rp{i} lc1 'rout_s'\n")                                    
                lines.append("\n")

            lines.append("lc1 lc1 lc1r 'lc_filter'\n")
            lines.append("rlc1	lc1r 0 'rdc_Lc'\n")

            for i in range(1,ph_count+1,1):            
                lines.append(f"K{i} 	lp{i} 	lp{i}s 	'k_par'\n")

        
        
        lin=self.lin_ports
        self.lin_ports=[]
        self.lin_ports.append('swn')
        self.lin_ports.append(self.vr_info.sense[0])
        snp_fpath=Io.update_file_extension(self.vr_tune_file_s2p,'')        
        lines+=self.text_for_lin_ports(snp_fpath,None)
        self.lin_ports=lin
        return lines

    def save_deck_main(self,analysis_type=AnalysisType.ZF,pkg_model=PsiModelType.MACRO1,
        brd_model=PsiModelType.MACRO1,file_path=None):
        
        EventLogger.msg('Saving main file...')

        if isinstance(analysis_type, int):
            analysis_type=AnalysisType(analysis_type)
        if isinstance(pkg_model, int):
            pkg_model=PsiModelType(pkg_model)
        if isinstance(brd_model, int):
            brd_model=PsiModelType(brd_model)

        if not file_path:
            if analysis_type==AnalysisType.BODE:
                file_path=self.main_bode_file
            elif analysis_type==AnalysisType.ZF:
                if brd_model== PsiModelType.MACRO1 and pkg_model== PsiModelType.MACRO1:                    
                    file_path=self.main_zf_file
                elif brd_model== PsiModelType.TSTONE and pkg_model== PsiModelType.TSTONE:                    
                    file_path=self.main_s_s_zf_file
                elif brd_model== PsiModelType.MACRO1 and pkg_model== PsiModelType.TSTONE:                    
                    file_path=self.main_m_s_zf_file
                elif brd_model== PsiModelType.TSTONE and pkg_model== PsiModelType.MACRO1:                    
                    file_path=self.main_s_m_zf_file

            elif analysis_type==AnalysisType.LF:
                file_path=self.main_tran_lf_file
            elif analysis_type==AnalysisType.HF:
                file_path=self.main_tran_hf_file
            elif analysis_type==AnalysisType.LIN:                
                if brd_model== PsiModelType.MACRO1 and pkg_model== PsiModelType.MACRO1:                    
                    file_path=self.main_lin_file
                elif brd_model== PsiModelType.TSTONE and pkg_model== PsiModelType.TSTONE:                    
                    file_path=self.main_s_s_lin_file
                elif brd_model== PsiModelType.MACRO1 and pkg_model== PsiModelType.TSTONE:                    
                    file_path=self.main_m_s_lin_file
                elif brd_model== PsiModelType.TSTONE and pkg_model== PsiModelType.MACRO1:                    
                    file_path=self.main_s_m_zf_file

            elif analysis_type==AnalysisType.TUNE_VR:                                
                    file_path=self.main_vr_tune_file


        file_path=os.path.abspath(file_path)
        folder_file = os.path.split(file_path)
        
        self.set_analysis_type(analysis_type)
        self.set_pkg_model_type(pkg_model)
        self.set_brd_model_type(brd_model)

        self.include_lines=[]
    
        lines=[]                

        lines+=self.text_for_header()        
        lines+=self.text_for_sim_options()
        lines+=self.text_for_newline()
        lines+=self.text_for_global_params()
        lines+=self.text_for_newline()
        if self.user_data:
            lines+=self.text_for_commented_tittle('User Data')
            if isinstance(self.user_data,str):
                lines.append(self.user_data)
            else:
                for user_data_line in self.user_data:
                    lines.append(user_data_line+'\n')
        
        lines+=self.text_for_analysis()
        lines+=self.text_for_newline()
        lines+=self.text_for_bode_variable()
        lines+=self.text_for_newline()
        lines+=self.text_for_loading_conditions(folder_file[0])
        lines+=self.text_for_newline()
        
        lines+=self.text_for_commented_tittle('PDN')
        lines+=self.text_for_rl_connector_model(folder_file[0])
        lines+=self.text_for_newline()
        if self.die_instances:
            lines+=self.text_for_comment('dies')
            for line in self.die_params:            
                lines.append(line+'\n')
                
            for ins_name in self.die_instances:
                die_ins=self.die_instances[ins_name]     
                lines+=self.text_for_include(die_ins.model.fpath,folder_file[0])                            
            lines+=self.text_for_include(self.die_ins_file,folder_file[0])        
            lines+=self.text_for_newline()

        if self.c4_groups:
            lines+=self.text_for_insgroup_models(self.c4_groups,'c4 Bump models',folder_file[0])            
            lines+=self.text_for_comment('C4 Bump instances')
            lines+=self.text_for_include(self.c4_ins_file,folder_file[0])                      
            lines+=self.text_for_newline()                            
        
        if self.pkg_instance:
            lines+=self.text_for_comment('pkg')   
            lines+=self.text_for_psi_external_instance(self.pkg_id,
            self.pkg_instance.model,self.pkg_tstone_ins_file,
            self.pkg_ins_file,
            folder_file[0])                                                              
            lines+=self.text_for_newline()                 
        
        if self.pkg_patch_instance:
            lines+=self.text_for_comment('pkg patch')   
            lines+=self.text_for_psi_external_instance(self.pkg_id,
            self.pkg_patch_instance.model,self.pkg_patch_tstone_ins_file,
            self.pkg_patch_ins_file,
            folder_file[0])                                                              
            lines+=self.text_for_newline()    
        
        if self.pkg_int_instance:
            lines+=self.text_for_comment('pkg int')   
            lines+=self.text_for_psi_external_instance(self.pkg_id,
            self.pkg_int_instance.model,self.pkg_int_tstone_ins_file,
            self.pkg_int_ins_file,
            folder_file[0])                                                              
            lines+=self.text_for_newline()  

        if self.mli_groups:
            lines+=self.text_for_insgroup_models(self.mli_groups,'MLI Models',folder_file[0])            
            lines+=self.text_for_comment('MLI Instances')
            lines+=self.text_for_include(self.mli_ins_file,
            folder_file[0])        
            lines+=self.text_for_newline()

        if self.skt_groups:
            lines+=self.text_for_insgroup_models(self.skt_groups,'Socket Models',folder_file[0])            
            lines+=self.text_for_comment('Socket Instances')
            lines+=self.text_for_include(self.skt_ins_file,
            folder_file[0])        
            lines+=self.text_for_newline()

        if self.brd_instance:
            lines+=self.text_for_comment('brd')     
            lines+=self.text_for_psi_external_instance(self.brd_id,
            self.brd_instance.model,self.brd_tstone_ins_file,
            self.brd_ins_file,
            folder_file[0])         
            lines+=self.text_for_newline()                        

        if self.attd_cap_groups:
            lines+=self.text_for_insgroup_models(self.attd_cap_groups,
            'Capacitor models',folder_file[0])
            lines+=self.text_for_newline()         
            lines+=self.text_for_comment('Capacitor instances')
            lines+=self.text_for_include(self.cap_ins_file,
            folder_file[0])
            lines+=self.text_for_newline()      
        
        #VR
        if analysis_type != analysis_type.LIN and analysis_type!=analysis_type.TUNE_VR:
            lines+=self.text_for_commented_tittle('Voltage source')        
            if self.vr_instance:            
                lines+=self.text_for_comment('VR')                
                if not self.vr_info.tlvr_enabled:
                    lines+=self.text_for_include(self.vr_mod_file,
                    folder_file[0])
                else:
                    lines+=self.text_for_include(self.tlvr_mod_file,
                    folder_file[0])

                    
                lines+=self.text_for_vr_ins()
            else:
                EventLogger.raise_warning(f"No VR instance!")
        
        
        #shorts
        lines+=self.text_for_short_ports()

        #tstone        
        lines+=self.text_for_tstone_instances(folder_file[0])

        #VR_TUNE        
        if analysis_type == analysis_type.TUNE_VR: 
            lines+=self.text_for_vr_tune_conns()                         

        #LIN
        if analysis_type == analysis_type.LIN: 
            snp_fpath=Io.update_file_extension(file_path,'')
            lines+=self.text_for_lin_ports(snp_fpath,folder_file[0])

        
        #probes        
        lines+=self.text_for_newline()
        lines+=self.text_for_comment('Probes') 
        if self.probe_v_ac_ports:                
            lines+=self.text_for_include(self.ac_vprobe_file,
            folder_file[0])
        if self.probe_v_tran_ports:
            lines+=self.text_for_include(self.tran_vprobe_file,
            folder_file[0])                                   
            
        
        lines+=self.text_for_end_file()   
        
        self.main_files.append(file_path)
        self.create_text_file(file_path,lines) 

        EventLogger.info('main file saved:'+ file_path)

    def save_deck(self,bode=False,zf=False,lf=False,hf=False,lin=False,
        zf_s_s=False,ZF_M_S=False,ZF_S_M=False,LIN_S_S=False,LIN_M_S=False,LIN_S_M=False,tune_vr=False):
        """Save the Hspice deck files in the deck folder. 
        Note that all the main files similar, except for the global \
        parameters that determine the type of analysis and models to use.

        :param Bode: Save Bode main file, defaults to False
        :type Bode: bool, optional
        :param ZF: Save ZF main file, defaults to False
        :type ZF: bool, optional
        :param LF: Save LF main file, defaults to False
        :type LF: bool, optional
        :param HF: Save HF main file, defaults to False
        :type HF: bool, optional
        :param LIN: Save Lin main file, defaults to False
        :type LIN: bool, optional
        :param ZF_S_S: Save ZF with Board Sparams and PKG Sparam, defaults to False
        :type ZF_S_S: bool, optional
        :param ZF_M_S: Save ZF with board macromodel and PKG Sparameters, \
        defaults to False
        :type ZF_M_S: bool, optional
        :param ZF_S_M: Save ZF with Board Sparams and PKG macromodel, defaults \
        to False
        :type ZF_S_M: bool, optional
        :param LIN_S_S: Save Lin main with board Sparams and PKG Sparam, \
        defaults to False
        :type LIN_S_S: bool, optional
        :param LIN_M_S: Save Lin main with board macromodel and package \
        Sparams, defaults to False
        :type LIN_M_S: bool, optional
        :param LIN_S_M: Save Lin main with board sparams and package macromodel\
        , defaults to False
        :type LIN_S_M: bool, optional
        """                           
        self.save_deck_dependencies()
        
        
        if bode:
            self.save_deck_main(analysis_type=AnalysisType.BODE,
            pkg_model=PsiModelType.MACRO1,brd_model=PsiModelType.MACRO1,
            file_path=None)
        
        if zf:
            self.save_deck_main(analysis_type=AnalysisType.ZF,
            pkg_model=PsiModelType.MACRO1,brd_model=PsiModelType.MACRO1,
            file_path=None)
        
        if lf:
            self.save_deck_main(analysis_type=AnalysisType.LF,
            pkg_model=PsiModelType.MACRO1,brd_model=PsiModelType.MACRO1,
            file_path=None)

        if hf:
            self.save_deck_main(analysis_type=AnalysisType.HF,
            pkg_model=PsiModelType.MACRO1,brd_model=PsiModelType.MACRO1,
            file_path=None)

        if lin:
            self.save_deck_main(analysis_type=AnalysisType.LIN,
            pkg_model=PsiModelType.MACRO1,brd_model=PsiModelType.MACRO1,
            file_path=None)

        if zf_s_s:
            self.save_deck_main(analysis_type=AnalysisType.ZF,
            pkg_model=PsiModelType.TSTONE,brd_model=PsiModelType.TSTONE,
            file_path=None)
        
        if ZF_M_S:
            self.save_deck_main(analysis_type=AnalysisType.ZF,
            pkg_model=PsiModelType.TSTONE,brd_model=PsiModelType.MACRO1,
            file_path=None)
        
        if ZF_S_M:
            self.save_deck_main(analysis_type=AnalysisType.ZF,
            pkg_model=PsiModelType.MACRO1,brd_model=PsiModelType.TSTONE,
            file_path=None)

        if LIN_S_S:
            self.save_deck_main(analysis_type=AnalysisType.LIN,
            pkg_model=PsiModelType.TSTONE,brd_model=PsiModelType.TSTONE,
            file_path=None)
        
        if LIN_M_S:
            self.save_deck_main(analysis_type=AnalysisType.LIN,
            pkg_model=PsiModelType.MACRO1,brd_model=PsiModelType.TSTONE,
            file_path=None)
        
        if LIN_S_M:
            self.save_deck_main(analysis_type=AnalysisType.LIN,
            pkg_model=PsiModelType.TSTONE,brd_model=PsiModelType.MACRO1,
            file_path=None)
        
        if tune_vr:       
            #save the tuning file                          
            self.vr_info.save_matlab_tuning(self.vr_tuning_script,
            self.vr_tune_file_s2p,self.vr_tune_compfile)            
            #save the main file
            self.save_deck_main(analysis_type=AnalysisType.TUNE_VR,
            pkg_model=PsiModelType.MACRO1,brd_model=PsiModelType.MACRO1,
            file_path=None)
    
    def connect_1a_ac_to_die_ports(self,port_wildcard='*',
                                   instance_wildcard='*',
                                   port_exclude_wildecard=['*vss*','*ref*','0']):
    
        a=self.find_die_instances_ports_by_name(port_wildcard,instance_wildcard)
        
        #ports
        ports=[]                        
        for port in self.find_die_instances_ports_by_name(port_wildcard,
                                                          instance_wildcard):            
            if not TextProcessor.match(port,port_exclude_wildecard):
                ports.append(port)
        
        self.connect_1a_ac_dis(ports)
          
    def connect_icct_pulse_to_die_ports(self,imin='1', imax='2', freq='1e3',
                                        delay='1u', rise='1n',
                                        port_wildcard='*',instance_wildcard='*',
                                        port_exclude_wildecard=['*vss*','*ref*','0']):
    
        #ports
        ports=[]                
        for port in self.find_die_instances_ports_by_name(port_wildcard,
                                                          instance_wildcard):
            if not TextProcessor.match(port,port_exclude_wildecard):
                ports.append(port)        

        self.user_data+=\
"""
*LF icct
.param        
+imin_lf = '1'
+imax_lf = '2'                
+freq_lf = '2e3'
+tdelay_lf = '200u'
+trise_lf = '0.285n'
+ton_lf = '0.5/freq_lf'
+tperiod_lf = '1/freq_lf'
+iprobe_lf = '0'
+gpoly_lf = '1'

"""
        
        #ports=self.find_die_instances_ports_by_name(ports)
        mod_path='./icct/lf/current_pulse.inc'
        params=f"imin = 'imin_lf/{len(ports)}' imax = 'imax_lf/{len(ports)}' \
        tdelay = 'tdelay_lf' \
        trise = 'trise_lf' ton = 'ton_lf' tperiod = 'tperiod_lf' vid = 'vid' \
        iprobe = 'iprobe_lf' gpoly = 'gpoly_lf'"

        self.connect_lf_icct_by_model_filename(ports,mod_path,'icct',params)          

class DeckBuildState(Enum):
    """Enumeration class for representing the different states of the deck building process

    NOT_STARTED: The deck building process has not started yet
    TUNE_BUILD: The deck building process is currently building the tuning deck
    TUNE_SPICERUN: The deck building process is currently running the tuning deck with SPICE
    TUNE_MATLABRUN: The deck building process is currently running the tuning deck with Matlab
    MAIN_BUILD: The deck building process is currently building the main deck
    MAIN_RUN: The deck building process is currently running the main deck
    """
        
    NOT_STARTED=0    
    TUNE_BUILD=1    
    TUNE_SPICERUN=2    
    TUNE_MATLABRUN=3    
    MAIN_BUILD=4    
    MAIN_RUN=5

class DeckFactory:
    """Buil, tune and run multiple Hspice decks.
    """
    def __init__(self):      
        self.tuning_main_files_to_run=[]  
        self.tuning_scripts=[]  
        self.main_files_to_run=[]        
        self.state=DeckBuildState.NOT_STARTED
        
        self.deck_template_rel_path='templates/deck_template.xlsx'
        
        self.built_cases=[]

        self.subproc_batch_size=4
        self.hspice_mt=1
    
    def clone_template(self,dst_folder =os.curdir):
        """This function create the template excel file to build the decks 

        :param dst_folder: target folder
        :type dst_folder: str
        """        
        template = os.path.join(os.path.dirname(__file__), self.deck_template_rel_path)        
        dst_path=os.path.abspath(os.path.join(dst_folder,'deck_template.xlsx'))
        
        shutil.copy(template, dst_path)
        
    def override_deck_table(self,table1, table2):
        """This function takes two tables and creates a new table by taking the 
        values from the second table if it's not empty, otherwise it takes 
        the values from the first table.

        :param table1: The first table.
        :type table1: List[List[]]
        :param table2: The second table.
        :type table2: List[List[]]
        :return: The merged table.
        :rtype: List[List[]]
        """
        # Initialize the new table
        merged_table = []

        # Iterate over the rows in the tables
        for row1, row2 in zip(table1, table2):
            # Initialize the merged row
            merged_row = []

            # Iterate over the values in the rows
            for val1, val2 in zip(row1, row2):
                # Use the value from the second table if it is not empty, 
                # otherwise use the value from the first table
                merged_val = val2 if val2 else val1
                merged_row.append(merged_val)

            # Add the merged row to the new table
            merged_table.append(merged_row)

        return merged_table

    def parse_deck_table(self,case_table, row_offset=0):
        """Reads an table and creates a data structure that containts the deck information.        
        :param row_offset: The number of rows to skip before reading the data, defaults to 3
        :type row_offset: int, optional
        :param case_column: The column index of the data to read, defaults to 2
        :type case_column: int, optional
        :return: A dictionary containing the data from the table, structured as follows:
        {
            'section1': {
                'parameter1': 'value1',
                'parameter2': 'value2',
                ...
            },
            'section2': {
                'parameter1': 'value1',
                'parameter2': 'value2',
                ...
            },
            ...
        }
        :rtype: dict
        """       
        deck_data={}         
        section_counts = {}
        previous_section = None
        section_start_index=0
        for i, row in enumerate(case_table):
            if i < row_offset:
                continue
            section = row[0].lower()
            parameter = row[1].lower()
            value = row[2].lower()
            if section:
                section_start_index=i                
                if section in section_counts:
                    section_counts[section] += 1
                    section += f' ({section_counts[section]})'
                previous_section = section
            else:
                section = previous_section

            if not section:
                continue            
            else:
                section_counts[section] = 1

            if section not in deck_data:
                deck_data[section] = {}
            if parameter:
                deck_data[section][parameter] = value
            else:
                if 'unnamed' not in deck_data[section]:
                    deck_data[section]['unnamed']=[]
                unnamed_local_index=i-section_start_index
                if unnamed_local_index<len(deck_data[section]['unnamed']):                    
                    deck_data[section]['unnamed'][unnamed_local_index]=value
                else:
                    deck_data[section]['unnamed'].append(value)
        return deck_data

    
    def parse_ports(self,deck,ports_desc):
        """This function takes a deck and a description of ports and returns a
         list of ports in the deck that match the description.
        

        :param deck: The deck containing the ports
        :type deck: object
        :param ports_desc: A string describing the ports to find in the format 
        of "pkg.port_name,brd.port_name,dies.port_name"

        :type ports_desc: str
        :return: A list of ports that match the description
        :rtype: List
        """
        ports_desc=ports_desc.split(',')
        
        ports=[]
        for port_desc in ports_desc:
            port_parts=port_desc.split('.')      
            
            if TextProcessor.match(port_parts[0],'pkg'):
                ports+=deck.pkg_instance.find_ports_by_name(port_parts[1])            
            elif TextProcessor.match(port_parts[0],'patch'):
                ports+=deck.pkg_patch_instance.find_ports_by_name(port_parts[1])
            elif TextProcessor.match(port_parts[0],'brd'):
                ports+=deck.brd_instance.find_ports_by_name(port_parts[1]) 
            elif  TextProcessor.match(port_parts[0],'dies'):
                ports+=deck.find_die_instances_ports_by_name(port_parts[1]) 
            else:
                #TODO error
                pass            
        return ports
    
    def build_deck(self,deck_data):
        """build the Hspice deck (folders and files). based on a description table
        containing all the deck parameters.

        :param deck_data: deck description table
        :type deck_data: dic
        """
        sec=TextProcessor.find_dict_key(deck_data,'case')       
        par=TextProcessor.find_dict_key(deck_data[sec],['name'])
        case=deck_data[sec][par]
        par=TextProcessor.find_dict_key(deck_data[sec],['execute'])
        exec=deck_data[sec][par]
        exec=TextProcessor.match(exec,['yes','true'])

        if case in self.built_cases:
            print(f'Duplicated case ignored!: {case}')
            return
        self.built_cases.append(case)

        if not exec:
            return

        
        
        deck=HspiceDeck(case)

        #analysis
        sec=TextProcessor.find_dict_key(deck_data,'analysis')        
        par=TextProcessor.find_dict_key(deck_data[sec],'option*')
        par_val=deck_data[sec][par]     
        deck.sim_option_line=[par_val+'\n']

        par=TextProcessor.find_dict_key(deck_data[sec],'ac*')
        par_val=deck_data[sec][par]     
        deck.ac_analysis_line=[par_val+'\n']

        par=TextProcessor.find_dict_key(deck_data[sec],'lf*')
        par_val=deck_data[sec][par]                
        deck.lf_analysis_line=[par_val+'\n']
        
        par=TextProcessor.find_dict_key(deck_data[sec],'hf*')
        par_val=deck_data[sec][par]                
        deck.hf_analysis_line=[par_val+'\n']


        

        #user data
        sec=TextProcessor.find_dict_key(deck_data,'user data')        
        par=TextProcessor.find_dict_key(deck_data[sec],'unnamed')
        par_val=deck_data[sec][par]                
        deck.user_data=par_val
        
        
        #Caps
        sec=TextProcessor.find_dict_key(deck_data,'caps*')        
        par=TextProcessor.find_dict_key(deck_data[sec],'folder')
        par_val=deck_data[sec][par]        
        deck.load_attd_caps_models(par_val)            
                
        #PKG-mono
        sec=TextProcessor.find_dict_key(deck_data,'pkg')

        par=TextProcessor.find_dict_key(deck_data[sec],'folder')
        folder=deck_data[sec][par]

        par=TextProcessor.find_dict_key(deck_data[sec],'cap map')
        map_file=deck_data[sec][par]

        if folder:
            deck.load_pkg(model_folder=folder)
            deck.connect_attd_caps_to_pkg(map_file)


        #PKG Patch
        sec=TextProcessor.find_dict_key(deck_data,'pkg patch')
        
        par=TextProcessor.find_dict_key(deck_data[sec],'folder')
        folder=deck_data[sec][par]     

        par=TextProcessor.find_dict_key(deck_data[sec],'cap map')
        map_file=deck_data[sec][par]       
        if folder:
            deck.load_pkg_patch(model_folder=folder)
            deck.connect_attd_caps_to_pkg_patch(map_file)

        #PKG Int
        sec=TextProcessor.find_dict_key(deck_data,'pkg int')
        
        par=TextProcessor.find_dict_key(deck_data[sec],'folder')
        folder=deck_data[sec][par]  

        par=TextProcessor.find_dict_key(deck_data[sec],'cap map')
        map_file=deck_data[sec][par]    
        if folder:
            deck.load_pkg_int(model_folder=folder)
            deck.connect_attd_caps_to_pkg_int(map_file)
        
        #BRD
        sec=TextProcessor.find_dict_key(deck_data,'brd')        

        par=TextProcessor.find_dict_key(deck_data[sec],'folder')
        folder=deck_data[sec][par]

        par=TextProcessor.find_dict_key(deck_data[sec],'cap map')
        map_file=deck_data[sec][par]

        deck.load_brd(model_folder=folder)
        deck.connect_attd_caps_to_brd(map_file)
        
        #mli
        sec=TextProcessor.find_dict_key(deck_data,'mli')

        par=TextProcessor.find_dict_key(deck_data[sec],'int refdes')
        int_refdes=deck_data[sec][par]

        par=TextProcessor.find_dict_key(deck_data[sec],'patch refdes')
        patch_refdes=deck_data[sec][par]

        par=TextProcessor.find_dict_key(deck_data[sec],'mli map')
        mli_map=deck_data[sec][par]
        
        if mli_map:
            deck.connect_mli_by_map(map_fpath=mli_map,category='mli')
        else:
            deck.connect_mli(int_mli_name=int_refdes,patch_mli_name=patch_refdes) 
        
        #skt
        sec=TextProcessor.find_dict_key(deck_data,['skt','socket'])        

        par=TextProcessor.find_dict_key(deck_data[sec],'brd refdes')
        brd_refdes=deck_data[sec][par]

        par=TextProcessor.find_dict_key(deck_data[sec],'pkg refdes')
        pkg_refdes=deck_data[sec][par]

        par=TextProcessor.find_dict_key(deck_data[sec],'skt map')
        skt_map=deck_data[sec][par]
        
        if skt_map:
            deck.connect_skt_by_map(skt_map)
        else:
            deck.connect_skt(brd_skt_name=brd_refdes,pkg_skt_name=pkg_refdes)        

        #die
        secs=TextProcessor.find_dict_key(deck_data,'die*',True)
        for sec in secs:
            par=TextProcessor.find_dict_key(deck_data[sec],'model file')
            model_file=deck_data[sec][par]
            par=TextProcessor.find_dict_key(deck_data[sec],'die port map')
            map_file=deck_data[sec][par]
            deck.connect_die_using_mapfile(model_file,map_file)
        
        #VR
        sec=TextProcessor.find_dict_key(deck_data,'vr*')        

        par=TextProcessor.find_dict_key(deck_data[sec],['sp','sense'])        
        sp=deck_data[sec][par]
        sp=self.parse_ports(deck,sp)          
        
        par=TextProcessor.find_dict_key(deck_data[sec],['ph','phs','phases'])        
        phs=deck_data[sec][par]        
        phs=self.parse_ports(deck,phs)                 

        
        par=TextProcessor.find_dict_key(deck_data[sec],'vid*')        
        vid=deck_data[sec][par]

        par=TextProcessor.find_dict_key(deck_data[sec],'avp*')        
        avp=deck_data[sec][par]

        par=TextProcessor.find_dict_key(deck_data[sec],['f0*','ugb*'])        
        f0=deck_data[sec][par]

        par=TextProcessor.find_dict_key(deck_data[sec],'pm*')        
        pm=deck_data[sec][par]

        par=TextProcessor.find_dict_key(deck_data[sec],'lout*')        
        lout=deck_data[sec][par]

        par=TextProcessor.find_dict_key(deck_data[sec],'rout*')        
        rout=deck_data[sec][par]

        
        par=TextProcessor.find_dict_key(deck_data[sec],'tlvr_enabled*')        
        tlvr_enabled=deck_data[sec][par]
        tlvr_enabled=TextProcessor.match(tlvr_enabled,['yes','true'])

        par=TextProcessor.find_dict_key(deck_data[sec],'l_transformer*')        
        l_transformer=deck_data[sec][par]

        par=TextProcessor.find_dict_key(deck_data[sec],'lc_filter*')        
        lc_filter=deck_data[sec][par]

        par=TextProcessor.find_dict_key(deck_data[sec],'rdc_lc*')        
        rdc_lc=deck_data[sec][par]

        par=TextProcessor.find_dict_key(deck_data[sec],'rout_p*')        
        rout_p=deck_data[sec][par]

        par=TextProcessor.find_dict_key(deck_data[sec],'rout_s*')        
        rout_s=deck_data[sec][par]

        par=TextProcessor.find_dict_key(deck_data[sec],'k_par*')        
        k_par=deck_data[sec][par]
        

        
        
        #VR tuning
        deck.vr_info=VRInfo()
        deck.vr_info.sense=sp        
        deck.vr_info.phs=phs
        deck.vr_info.vid=vid
        deck.vr_info.avp=avp
        deck.vr_info.f0=f0
        deck.vr_info.pm=pm
        deck.vr_info.vin='12'
        deck.vr_info.vramp='1.5'
        deck.vr_info.lout=lout
        deck.vr_info.rout=rout
        
        #LRVR
        deck.vr_info.tlvr_enabled=tlvr_enabled
        deck.vr_info.l_transformer=l_transformer
        deck.vr_info.lc_filter=lc_filter
        deck.vr_info.rdc_lc=rdc_lc
        deck.vr_info.rout_p=rout_p
        deck.vr_info.rout_s=rout_s
        deck.vr_info.k_par=k_par

        
        #connect the VR     
        if not tlvr_enabled:
            deck.connect_vrstavggen(phs,sp)
        else:
            deck.connect_tlvrstavggen(phs,sp)


        


        #ZF
        sec=TextProcessor.find_dict_key(deck_data,'zf') 

        par=TextProcessor.find_dict_key(deck_data[sec],['ports'])   
          
        ports=deck_data[sec][par]
        if ports:
            ports=self.parse_ports(deck,ports)
            deck.connect_1a_ac_dis(ports)
        #LF icct
        secs=TextProcessor.find_dict_key(deck_data,'lf icc*',True)
        for sec in secs:
            
            par=TextProcessor.find_dict_key(deck_data[sec],'name')
            name=deck_data[sec][par]

            if not name:
                continue

            par=TextProcessor.find_dict_key(deck_data[sec],'ports')
            ports=deck_data[sec][par]
            if not ports:
                EventLogger.raise_value_error(f'Incorrect icct def. in case: {case}')

            par=TextProcessor.find_dict_key(deck_data[sec],'model file')
            mode_file=deck_data[sec][par]
            if not mode_file:
                EventLogger.raise_value_error(f'Incorrect icct def. in case: {case}')
            
            par=TextProcessor.find_dict_key(deck_data[sec],'params')
            params=deck_data[sec][par]   

            ports=self.parse_ports(deck,ports)                
            deck.connect_lf_icct_by_model_filename(ports=ports, mod_path=mode_file,
            params=params,groupname= name)

        #HF icct
        secs=TextProcessor.find_dict_key(deck_data,'hf icc*',True)
        for sec in secs:
            
            par=TextProcessor.find_dict_key(deck_data[sec],'name')
            name=deck_data[sec][par]
            if not name:
                continue

            par=TextProcessor.find_dict_key(deck_data[sec],'ports')
            ports=deck_data[sec][par]
            if not ports:
                EventLogger.raise_value_error(f'Incorrect icct def. in case: {case}')

            par=TextProcessor.find_dict_key(deck_data[sec],'model file')
            mode_file=deck_data[sec][par]
            if not mode_file:
                EventLogger.raise_value_error(f'Incorrect icct def. in case: {case}')
            
            par=TextProcessor.find_dict_key(deck_data[sec],'params')
            params=deck_data[sec][par]   

            ports=self.parse_ports(deck,ports)                
            deck.connect_hf_icct_by_model_filename(ports=ports, mod_path=mode_file,
            params=params,groupname= name)
        
        #LIN ports
        secs=TextProcessor.find_dict_key(deck_data,'lin',True)
        for sec in secs:
            
            par=TextProcessor.find_dict_key(deck_data[sec],'ports')
            ports=deck_data[sec][par]

            ports=self.parse_ports(deck,ports)                            
            deck.connect_lin_port(ports)
        
        #Probe ports
        secs=TextProcessor.find_dict_key(deck_data,'probe',True)
        for sec in secs:
            
            par=TextProcessor.find_dict_key(deck_data[sec],'v_ac*')            
            ports=deck_data[sec][par]
            if ports:
                ports=self.parse_ports(deck,ports)                            
                deck.probe_v_ac(ports)
            
            par=TextProcessor.find_dict_key(deck_data[sec],'v_tran*')            
            ports=deck_data[sec][par]
            if ports:
                ports=self.parse_ports(deck,ports)                            
                deck.probe_v_tran(ports)
        
        #save
        sec=TextProcessor.find_dict_key(deck_data,'main')        
        
        bode=False
        par=TextProcessor.find_dict_key(deck_data[sec],['bode'])                                
        if par:            
            bode=deck_data[sec][par]
            bode=TextProcessor.match(bode,['yes','true'])        

        zf=False
        par=TextProcessor.find_dict_key(deck_data[sec],['zf'])        
        if par:            
            zf=deck_data[sec][par]
            zf=TextProcessor.match(zf,['yes','true'])

        lf=False
        par=TextProcessor.find_dict_key(deck_data[sec],['lf'])        
        if par:            
            lf=deck_data[sec][par]
            lf=TextProcessor.match(lf,['yes','true'])

        hf=False
        par=TextProcessor.find_dict_key(deck_data[sec],['hf'])        
        if par:            
            hf=deck_data[sec][par]
            hf=TextProcessor.match(hf,['yes','true'])

        lin=False
        par=TextProcessor.find_dict_key(deck_data[sec],['lin'])        
        if par:            
            lin=deck_data[sec][par]
            lin=TextProcessor.match(lin,['yes','true'])
        
        zf_s_s=False
        par=TextProcessor.find_dict_key(deck_data[sec],['zf_s_s'])        
        if par:            
            zf_s_s=deck_data[sec][par]
            zf_s_s=TextProcessor.match(zf_s_s,['yes','true'])

        #Simulate
        sec=TextProcessor.find_dict_key(deck_data,'simulation')    

        par=TextProcessor.find_dict_key(deck_data[sec],['vr_tune'])
        vr_tune=deck_data[sec][par]
        vr_tune=TextProcessor.match(vr_tune,['yes','true'])

        par=TextProcessor.find_dict_key(deck_data[sec],['run'])
        run=deck_data[sec][par]
        run=TextProcessor.match(run,['yes','true'])                        
        
        #build the deck
        if self.state==DeckBuildState.TUNE_BUILD:
            if vr_tune:            
                deck.save_deck(tune_vr=True)  
                self.tuning_main_files_to_run+=deck.main_files
                self.tuning_scripts.append(deck.vr_tuning_script)

        elif self.state==DeckBuildState.MAIN_BUILD:            
            if vr_tune:
                deck.load_vr_comp_from_file()
            deck.save_deck(bode=bode,zf=zf,lf=lf,hf=hf,lin=lin,zf_s_s=zf_s_s)

            if run:                
                self.main_files_to_run+=deck.main_files            

    def build_decks(self,fpath,sheet='1',col_offset=2):
        """Buld multiple decks based on an Excel file containing the description
        of each deck.

        :param fpath: path to the Excel file containing the deck description
        :type fpath: str
        :param sheet: name of the sheet to parse, defaults to '1'
        :type sheet: str, optional
        :param col_offset: Column offset to start reading the deck parameters. defaults to 2
        :type col_offset: int, optional
        """
        table = pd.read_excel(fpath, sheet_name=sheet, na_filter=False,dtype=str)
        col_count=len(table.columns)        
        
        base_deck_table=[]
        deck_table=[]
        deck_data={}

        self.built_cases=[]
        
        for i in range(col_offset,col_count):
            case_column=i
            deck_table = table.iloc[:, [0, 1, case_column]].values.tolist()
                                
            if not base_deck_table:
                base_deck_table=deck_table                                
            else:
                deck_table=self.override_deck_table(base_deck_table,deck_table)
            
            deck_data=self.parse_deck_table(deck_table)   
            
            self.build_deck(deck_data)
        

    def run_main_files(self,tool_path,main_files_to_run):
        """Runs multiple Spice main files in bach mode.

        :param tool_path: Hspice.exe path
        :type tool_folder: str
        :param main_files_to_run: list of files to run
        :type main_files_to_run: list[str]
        """
        pm=ProcessManager()                
        for fname in main_files_to_run:            
            command=Cmds.run_hspice_cmd(tool_path,fname,self.hspice_mt)        
            pm.schedule_subprocess(command)
        pm.start(self.subproc_batch_size)
    
    def run_tuning_scripts(self):
        """Runs the Matlab tuning scripts in batch mode
        """
        pm=ProcessManager()   
        
        for fpath in self.tuning_scripts:
            folder, filename = os.path.split(fpath)
            cmd=Cmds.run_matlab_cmd(Io.update_file_extension(filename,'') )            
            pm.schedule_subprocess(cmd,folder)
        pm.start(self.subproc_batch_size)


    def build_and_run(self,fpath,Hspice_path=r'C:\synopsys\Hspice_P-2019.06-SP2-3\WIN64\hspice.exe'):
        """Build, tune and run multiple Hspice decks.

        :param fpath: path to the Excel file containing the deck description.
        :type fpath: str
        :param Hspice_path: Hscpie.exe path, defaults to 'C:\\synopsys\\Hspice_P-2019.06-SP2-3\\WIN64\\hspice.exe'
        :type Hspice_path: str, optional
        """
        self.main_files_to_run=[]
        self.tuning_main_files_to_run=[]
        self.tuning_scripts=[]                
        self.state= DeckBuildState.TUNE_BUILD       
        self.build_decks(fpath)
        self.state= DeckBuildState.TUNE_SPICERUN       
        self.run_main_files(Hspice_path,self.tuning_main_files_to_run)
        self.state= DeckBuildState.TUNE_MATLABRUN               
        self.run_tuning_scripts()
        self.state= DeckBuildState.MAIN_BUILD               
        self.build_decks(fpath)
        self.state= DeckBuildState.MAIN_RUN
        self.run_main_files(Hspice_path,self.main_files_to_run)