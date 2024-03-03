import os
import subprocess


class hspice:
    def __init__(self):
        self.hspice_path	= ''
        
    def set_hspice_path(self,idemmp_path):
		
        self.hspice_path	=	idemmp_path + r'/hspice.com'
		
    def hspice_run(self,inFile):
        inFile=os.path.abspath(inFile)
        inFile_no_ext=os.path.splitext(inFile)[0]
        bat_filename=f'{inFile_no_ext}.bat'
        with open(bat_filename, 'w') as f:
            bat_file_line= f'{self.hspice_path}  -i  "{inFile}"  -o   "{inFile_no_ext}.lis"'
            f.write(bat_file_line)     
            
        subprocess.call(bat_filename)