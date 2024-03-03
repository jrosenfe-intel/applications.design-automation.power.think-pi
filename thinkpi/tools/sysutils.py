import threading
import subprocess
import time
import os
import re
import glob
import csv

import warnings
import traceback
from datetime import datetime


class TextProcessor:
    """Utility class for matching text against wildcards."""
    
    @staticmethod
    def match(text,wildcards=['cap','*Cap*']):
        """Match the given text against the specified wildcards.

        :param text: The text to be matched against the wildcards.
        :type text: str
        :param wildcards: The wildcards to use for matching. Can be a single \
        string or a list of strings.
        :type wildcards: str or list
        :return: True if the text matches any of the wildcards, False otherwise.
        :rtype: bool
        """
        if isinstance(wildcards, str):
            wildcards = [wildcards]
        for wildcard in wildcards:
            match = re.compile(f"^({wildcard.lower().replace('*', '.*').replace('?', '.?')})$")            
            if re.search(match, text.lower()):                     
                return True        
        return False
    
    @staticmethod
    def match_raw(text,wildcards=['cap','*Cap*']):
        """Match the given text against the specified wildcards.

        :param text: The text to be matched against the wildcards.
        :type text: str
        :param wildcards: The wildcards to use for matching. Can be a single \
        string or a list of strings.
        :type wildcards: str or list
        :return: True if the text matches any of the wildcards, False otherwise.
        :rtype: bool
        """
        if isinstance(wildcards, str):
            wildcards = [wildcards]
        for wildcard in wildcards:
            match = re.compile(wildcard)            
            if re.search(match, text):                     
                return True        
        return False
    
    @staticmethod
    def find_dict_key(dic,wildcards='',all_entries=False):
        if all_entries:
            result=[]
        else:
            result=None
        for key in dic:
            if TextProcessor.match(key,wildcards):
                if not all_entries:
                    return key
                result.append(key)
        return result
    
    @staticmethod
    def eng_to_float(eng_string):
        """
        Convert a string in engineering, scientific, or decimal notation to a float
        :param eng_string: Engineering, scientific, or decimal notation string (e.g. "3.4k", "2.2e-9", "3400")
        :return: float representation of the notation string
        """
        # Regular expression to match engineering notation
        eng_match = re.match(r"([\d.]+)([fpnumkMGT]?)", eng_string)
        if eng_match:
            value, unit = eng_match.groups()
            value = float(value)

            # Dictionary to convert the engineering notation unit to a multiplier
            eng_dict = {'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'm': 1e-3, 'k': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12}

            # If the unit is not found in the dictionary, it defaults to 1 (no multiplication)
            return value * eng_dict.get(unit, 1)
        else:
            # Regular expression to match scientific notation
            #r'^\d+(?:\.\d*)?[pfunmM]?'
            sci_match = re.match(r"([\d.]+)e([+-]\d+)", eng_string)
            if sci_match:
                value, exponent = sci_match.groups()
                return float(value) * 10 ** int(exponent)
            else:
                # Check if the string can be parsed as a decimal
                try:
                    return float(eng_string)
                except ValueError:
                    raise ValueError(f"{eng_string} is not in a valid notation")
    
    @staticmethod
    def isnumeric(eng_string):
        """
        Return True if the strings contains a valid Number.
        :param eng_string: Engineering, scientific, or decimal notation string (e.g. "3.4k", "2.2e-9", "3400")
        :return: float representation of the notation string
        """
        # Regular expression to match engineering notation
        #r'^\d+(?:\.\d*)?[pfunmM]?'
        eng_match = re.match(r"^([\d.]+)([fpnumkMGT]?)$", eng_string)
        if eng_match:            
            # If the unit is not found in the dictionary, it defaults to 1 (no multiplication)
            return True
        else:
            # Regular expression to match scientific notation
            sci_match = re.match(r"([\d.]+)e([+-]\d+)", eng_string)
            if sci_match:                
                return True
            else:
                # Check if the string can be parsed as a decimal
                try:
                    float(eng_string)
                    return True
                except ValueError:
                    return False
    @staticmethod
    def isCapacitance(string):
        """
        Returns True if the strings contains a valid Capacitance unit
        :param eng_string: Engineering, scientific, or decimal notation string (e.g. "3.4k", "2.2e-9", "3400")
        :return: float representation of the notation string
        """
        # Regular expression to match engineering notation
        if len(string)<2:       
            return False
        if string[-1]==('F'):
            string=string[:-1]
            if TextProcessor.isnumeric(string):
                return True        
            else:
                return False        
        else:
            return False
            
            



class Io:
    """Utility class for handling files and folders.
    
    This class provides methods for finding files and folders, creating files and \
    folders, editing file names, and more.
    """
    @staticmethod    
    def find_in_folder(path,wildcards,recursive=False):
        """Find files in a folder matching given wildcards.

        :param path: The path of the folder to search.
        :type path: str
        :param wildcards: One or more wildcard patterns to match against the 
        names of files in the folder.
        :type wildcards: str or list of str
        :param recursive: Whether to search subfolders recursively. Defaults 
        to False.
        :type recursive: bool, optional
        :return: A list of file paths that match the given wildcards.
        :rtype: list of str
        """
        match=[]

        if not path.endswith(os.sep):
            path = path + os.sep

        if isinstance(wildcards, str):
            wildcards = [wildcards]
        for wildcard in wildcards:
            if recursive:
                tmp_path=path+'/**/'+wildcard                
            else:                
                tmp_path=path+wildcard                        
            match+=glob.glob(tmp_path, recursive=recursive)            
        return match
    
    @staticmethod
    def custom_file_path(base_file_path,name_appendix):
        """Generate a custom file path based on the base file path and an \
        appendix to be added to the file name.

        :param base_file_path: The base file path.
        :type base_file_path: str
        :param name_appendix: The appendix to be added to the file name.
        :type name_appendix: str
        :return: The custom file path
        :rtype: str
        """
        root_ext=os.path.splitext(base_file_path)
        return f'{root_ext[0]}{name_appendix}{root_ext[1]}'
    @staticmethod
    def update_file_extension(base_file_path,new_ext):
        root_ext = os.path.splitext(base_file_path)
        return root_ext[0]+new_ext

    @staticmethod
    def create_folder(path):
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def create_text_file(file_path,lines):        
        """Save the deck file

        :param out_deck_filename: target filename
        :type out_deck_filename: str
        :param lines: text to be added in the file
        :type lines: list
        """
        folder_file = os.path.split(file_path)
        Io.create_folder(folder_file[0])

        with open(file_path, 'w') as f:
            for line in lines:        
                f.write(line)
    
    def create_csv_file(fpath,rows):
        folder_file = os.path.split(fpath)
        Io.create_folder(folder_file[0])
        
        with open(fpath, 'w',newline='') as f:            
            writer = csv.writer(f)
            for row in rows:
                writer.writerow(row)


class EventLogger:
    """Class for logging events and printing messages.

    This class provides static methods for logging events, printing messages, 
    and raising warnings or errors. 
    It also has a `log_path` attribute that specifies the path of the log file,
    and a `traceback_limit` attribute that determines the number of traceback 
    frames to include in the log file when an error occurs.
    """
    log_path=None
    traceback_limit=5    
        
    @staticmethod
    def int_log(log_folder=os.curdir):
        """Initialize the log file.

        :param log_folder: The folder to create the log file in. 
        Defaults to the current working directory.
        :type log_folder: str, optional
        """
        now = datetime.now()   
        EventLogger.log_path=log_folder+'/'+now.strftime("%d_%m_%Y_%H_%M_%S.log")
    
    @staticmethod
    def log_event(type,msg):
        """Log an event to the log file.

        :param type: The type of event to log.
        :type type: str
        :param msg: The message to include in the log entry.
        :type msg: str
        """
        folder_file = os.path.split(EventLogger.log_path)
        if not os.path.exists(folder_file[0]):
                os.makedirs(folder_file[0])
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")    

        with open(EventLogger.log_path, 'a') as f:                   
                f.write(dt_string+': ' +type+': '+msg+ '\n')
                
                if EventLogger.traceback_limit>0:
                    f.write('Traceback:\n')
                    traceback.print_stack(file=f,limit=EventLogger.traceback_limit)
    @staticmethod
    def msg(msg):
        """Print a message to the console and log it.

        :param msg: The message to print.
        :type msg: str
        """          
        print(msg)
        EventLogger.log_event('MSG',msg)
    
    @staticmethod
    def info(msg):
        """Print an informational message to the console and log it.

        :param msg: The message to print and log.
        :type msg: str
        """
        #std ANSI Escape color 
        if(EventLogger.traceback_limit>0):
            traceback.print_stack(limit=EventLogger.traceback_limit)
        print(f"\n\033[1;37;40mINFO:{msg} \033[0;0m")
        EventLogger.log_event('INFO',msg)
    
    @staticmethod
    def raise_warning(msg):
        """Raise a warning and log it.

        :param msg: The message to include in the warning and log.
        :type msg: str
        """    
        #std ANSI Escape color 
        if(EventLogger.traceback_limit>0):
            traceback.print_stack(limit=EventLogger.traceback_limit)
        EventLogger.log_event('WARNING',msg)
        warnings.warn(f"\n\033[2;31;43mWARNING!:{msg} \033[0;0m")        
    
    @staticmethod 
    def raise_value_error(msg):  
        """Raise an Error and log it.

        :param msg: The message to include in the warning and log.
        :type msg: str 
        """         
        EventLogger.log_event('ERROR',msg)
        raise ValueError(f"\n\033[2;37;41mError!:{msg} \033[0;0m")

class Cmds:
    """A class containing methods to create batch mode commands
    """
    @staticmethod
    def run_matlab_cmd(cmd):
        """Run a Matlab command in batch mode

        :param cmd: The Matlab command to run
        :type cmd: str
        :return: The command to run the Matlab command in batch mode
        :rtype: str
        """
        return f'matlab -batch {cmd}'

    @staticmethod
    def run_hspice_cmd(tool_path,fpath,mt=1):
        """Run a Hspice simulation command in batch mode

        :param fpath: the Hspice file to run with extension .sp
        :type fpath: str
        :return: The command to a run a Hspice simulationin in bach mode
        :rtype: str
        """
        fpath=os.path.abspath(fpath)
        inFile_no_ext=os.path.splitext(fpath)[0]        
        if mt>1:            
            return f'{tool_path} -mt {mt} -hpp  -i  {fpath}  -o   {inFile_no_ext}.lis'
        else:
            return f'{tool_path}  -i  {fpath}  -o   {inFile_no_ext}.lis'
    @staticmethod
    def run_psi_tcl(tool_path,fpath):
        """Run a PowerSI TCL file in bach mode

        :param tool_path: Path to the PowerSI .exe
        :type tool_path: str
        :param fpath: path to the TCL file
        :type fpath: str
        :return: The command to a run the PowerSI TCL file in bach mode
        :rtype: str
        """
        return f'{tool_path}  -b -tcl {fpath}'

    @staticmethod
    def idemmp_fitting(idemmp_fitting_path,
        sparam_fpath,mod_h5_fpath, orderMin=4, orderStep=2, 
        orderMax=10, bandwidth=2e9, DC=1, tol=0.001,xml=None):

        sparam_fpath=os.path.abspath(sparam_fpath)
        if not mod_h5_fpath:
            mod_h5_fpath=Io.update_file_extension(sparam_fpath,'.mod.h5')

        mod_h5_fpath=os.path.abspath(mod_h5_fpath)

        cmd= f'{idemmp_fitting_path}  -its  {sparam_fpath}  -o   {mod_h5_fpath}  \
        -orderMin  {orderMin}   -orderStep  {orderStep}  -orderMax  {orderMax} \
        -bandwidth  {bandwidth}  -DC  {DC}  -tol  {tol}'
        if(xml!=None):
            cmd+=f' -xml {os.path.abspath(xml)}'
        return cmd
    
    @staticmethod
    def idemmp_passivity(idemmp_passivity_path,in_mod_h5_fpath,
        out_mod_h5_fpath, DC=1, xml=None):

        in_mod_h5_fpath=os.path.abspath(in_mod_h5_fpath)
        out_mod_h5_fpath=os.path.abspath(out_mod_h5_fpath)

        cmd= f'{idemmp_passivity_path} -ih5  {in_mod_h5_fpath} -o  \
            {out_mod_h5_fpath} -DC {DC}'

        if(xml!=None):
            cmd+=f' -xml {os.path.abspath(xml)}'
        return cmd

    @staticmethod
    def idemmp_export(idemmp_export_path, in_mod_h5_fpath,out_mod_fpath, 
        type="HSPICE-LAPLACE"):
        
        in_mod_h5_fpath=os.path.abspath(in_mod_h5_fpath)
        out_mod_fpath=os.path.abspath(out_mod_fpath)
        cmd= f'{idemmp_export_path} -ih5 {in_mod_h5_fpath} -o  {out_mod_fpath} \
        -type {type} -gnd 2'        
        return cmd


class SubProc:
    """A class for running subprocesses
    """
    def __init__(self):
        """Initialize the subprocess with default values
        """
        self.commands=None
        self.id=None
        self.subprocess=None  
        self.cwd=None
        self.start_time=None
        self.timeout=None
        self.was_terminated=False
        
    def start(self):
        """
        This function starts the subprocess by running the command passed to it 
        """
        print(f"starting subprocess {self.id}")       
        command=self.commands[0]  #only supports one command
        print('cmd: '+command)
        self.subprocess = subprocess.Popen(command, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,shell=True,cwd=self.cwd)    
        self.start_time=time.time()            
        return self.subprocess

    def terminate(self):
        self.subprocess.terminate()
        self.was_terminated=True
        
class ProcessManager:
    def __init__(self):
        self.subprocesses_queue = []        
        self.id_counter = 0        
        self.running = False        
        self.console_lock = threading.Lock()

    def __del__(self):
        # Kill all subprocesses
        for process in self.subprocesses_queue:
            if process.subprocess:
                process.subprocess.terminate()
    
    def clear_queue(self):
        if self.running:
            return
        self.subprocesses_queue = []     
        self.id_counter=0   
    def schedule_subprocess(self, commands,cwd=None,timeout=None):
        
        if isinstance(commands,str):
            commands=[commands]
        self.id_counter += 1
        
        sub=SubProc()
        sub.commands=commands
        sub.id=self.id_counter
        sub.cwd=cwd
        sub.timeout=timeout
        self.subprocesses_queue.append(sub)
                
        return self.id_counter
    
    def check_status(self, process_id):
        for process in self.subprocesses_queue:
            if process.id == process_id:
                process.poll()
                if process.returncode is None:
                    return "running"
                else:
                    return "completed"
        return "invalid id"

    def run(self, batch_size=float("inf")):        
        while self.running:                    
            #process that started
            started_procs=[]
            pending_procs=[]
            for proc in self.subprocesses_queue:
                if proc.subprocess:
                    started_procs.append(proc)
                else:
                    pending_procs.append(proc)            
            #from the started process, check which one is completed
            completed_procs=[]
            running_procs=[]            
            timout_procs=[] 
            for proc in started_procs:
                proc.subprocess.poll()                
                if proc.subprocess.returncode is None:                       
                    if proc.timeout:
                        #kill process that timeout
                        elapsed_time =time.time()-proc.start_time
                        if elapsed_time>proc.timeout:
                            proc.terminate()
                            timout_procs.append(proc)
                    else:
                        running_procs.append(proc)
                else:
                    completed_procs.append(proc) 

                
                               
            for i in range(batch_size-len(running_procs)):                
                if i<len(pending_procs):
                    pending_procs[i].start()
                    time.sleep(0.1)                
            #print completed
            for proc in completed_procs:
                if proc.was_terminated:
                    continue
                output = proc.subprocess.stdout.read()                
                if output:
                    print(f"Subprocess {proc.id} has completed with output:")
                    print(f"")
                    print(output.decode('utf-8'))
                    self.print_progress(running_procs,pending_procs,completed_procs)
            #print timout
            for proc in timout_procs:                                
                print(f"Subprocess {proc.id} has been terminated with timeout = {proc.timeout} s\n")
                self.print_progress(running_procs,pending_procs,completed_procs)
                    
            

            if len(completed_procs)==len(self.subprocesses_queue):
                print(f'Done')
                self.running=False                                                                     
            time.sleep(2)
    def print_progress(self,running_procs,pending_procs,completed_procs):
        print(f'Running: {len(running_procs)}')
        print(f'Pending: {len(pending_procs)}')
        print(f'Completed: {len(completed_procs)}')

    def start(self, batch_size=4):
        if self.running:            
            return        
        print(f'Launching {len(self.subprocesses_queue)} subprocesses...')        
        print('')        
        self.running = True
        self.run(batch_size)
            