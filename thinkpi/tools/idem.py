import os
import subprocess


class idem:
    
    def __init__(self):
        
        self.idemmp_fitting_path = ''
        self.idemmp_passivity_path = ''
        self.idemmp_export_path	= ''
		
    def set_idemmp_path(self,idemmp_path):
		
        self.idemmp_fitting_path	=	idemmp_path + r'\idemmp_fitting.exe'
        self.idemmp_passivity_path	=	idemmp_path + r'\idemmp_passivity.exe'
        self.idemmp_export_path		=	idemmp_path + r'\idemmp_export.exe'
		
		#example of expected paths after concatenation:
		#self.idemmp_fitting_path=r'C:/"Program Files (x86)"/"CST Studio Suite 2020"/AMD64/idemmp_fitting.exe'
        #self.idemmp_passivity_path=r'C:/"Program Files (x86)"/"CST Studio Suite 2020"/AMD64/idemmp_passivity.exe'
        #self.idemmp_export_path=r'C:/"Program Files (x86)"/"CST Studio Suite 2020"/AMD64/idemmp_export.exe'
		
    def idemmp_fitting(self,inFile,out_mod_file, orderMin=4, orderStep=2, orderMax=10, bandwidth=2e9, DC=1, tol=0.001,xml=None):    
        inFile=os.path.abspath(inFile)
        out_mod_file=os.path.abspath(out_mod_file)
        xml=os.path.abspath(xml)
        
        inFile_no_ext=os.path.splitext(inFile)[0]
        mod_no_ext=os.path.splitext(out_mod_file)[0]       
        bat_filename=out_mod_file+".fitting.bat"        
        with open(bat_filename, 'w') as f:
            bat_file_line= f'"{self.idemmp_fitting_path}"  -its  "{inFile}"  -o   "{out_mod_file}"  -orderMin  {orderMin}   -orderStep  {orderStep}  -orderMax  {orderMax}  -bandwidth  {bandwidth}  -DC  {DC}  -tol  {tol}'
            if(xml!=None):
                bat_file_line+=f' -xml {xml}'
            f.write(bat_file_line)        
           
        subprocess.call(bat_filename)        
        
    def idemmp_passivity(self, inFile,out_mod_file, DC=1,xml=None):
        inFile=os.path.abspath(inFile)
        out_mod_file=os.path.abspath(out_mod_file)
        xml=os.path.abspath(xml)
        
        inFile_no_ext=os.path.splitext(inFile)[0]
        mod_no_ext=os.path.splitext(out_mod_file)[0]        
        bat_filename=out_mod_file+".passivity.bat"        
        with open(bat_filename, 'w') as f:
            bat_file_line= f'"{self.idemmp_passivity_path}" -ih5  "{inFile}" -o  "{out_mod_file}" -DC {DC}'
            cmd = [f'"{self.idemmp_passivity_path}"', '-ih5', f'"{inFile}"',
                   '-o', f'"{out_mod_file}"', '-DC', f'{DC}']
            if(xml!=None):
                bat_file_line+=f' -xml {xml}'
                cmd += ['-xml', f'{xml}']
            f.write(bat_file_line)
        
        #subprocess.call(bat_filename)
        """
        proc = subprocess.Popen(bat_filename, stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE, shell=True)
        try:
            outs, errs = proc.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            print('=== Killing IdEM passivity process due to time limit ===')
            proc.kill()
            return False
        """
        try:
            res = subprocess.run([bat_filename], shell=True,
                                 timeout=300)
        except subprocess.TimeoutExpired as exc:
            print(f"Process timed out.\n{exc}")
            subprocess.run(['taskkill', r'/f', r'/im', 'idemmp_passivity.exe',
                            r'/t'],
                           shell=True)
            return False
        return True
        
    def idemmp_passivity_check(self, mod_file):
        #inFile=os.path.abspath(inFile)
        mod_file=os.path.abspath(mod_file)
        
        
        #inFile_no_ext=os.path.splitext(inFile)[0]
        mod_no_ext=os.path.splitext(mod_file)[0]        
        bat_filename=mod_file+".passivity_check.bat"        
        with open(bat_filename, 'w') as f:
            bat_file_line= f'"{self.idemmp_passivity_path}" -ih5  "{mod_file}" -onlyCheck 2'
            
            f.write(bat_file_line)
        
        output=subprocess.run(bat_filename,capture_output=True)        
        print(str(output.stdout))
        
        if('Passive: NO' in str(output.stdout)):
            return False
        return True
        
    #Common formats
    #1 or ASCII exports state-space matrices of a macromodel to a standard ASCII text file. The extension .mod.txt is used for this files. The format of these files is self-explanatory. 
    #2 or Touchstone exports macromodel to a standard Touchstone file. 
    #3 or SPICE generates the equivalent circuit in standard SPICE language. 
    #4 or ASTAP generates the equivalent circuit in ASTAP (PowerSpice) language. 
    #5 or SPECTRE-netlist generates the equivalent circuit in Cadence Spectre® language using a circuit-based realization. 
    #6 or SPECTRE-ZP generates the equivalent circuit in Cadence Spectre® language using a pole-zero representation. 
    #7 or HSPICE-netlist generates the equivalent circuit in standard Synopsys®HPICE® language using a circuit-based realization. 
    #8 or HSPICE-LAPLACE generates the equivalent circuit in standard Synopsys® HPICE® language using a Lapalce realization. The Laplace element provides a particularly efficient way for using IdEM models in HSPICE® transient simulations. The model is synthesized in pole/reside form (also known as Foster canonical form), and HPICE® uses this format in an efficient way by using a recursive convolution method. 
    #9 or HSPICE-POLE generates the equivalent circuit in standard Synopsys® HPICE® language using a pole-zero representation. 
    #10 or VERILOGA generates the equivalent circuit in Verilog-A language. 
    #11 or VHDL-AMS generates the equivalent circuit in VHDL-AMS language. 
    #12 or ADS generates the equivalent circuit in Agilent's ADS bbn language. 
    #13 or APLAC generates the equivalent circuit in APLAC language. 
    #14 or RFM-HSPICE generates the equivalent circuit in Synopsys® HPICE® language using rational function matrix (RFM). The resulting .rfm file can be read by HSPICE® using the proper syntax. A wrapper netlist is also generated, it will allow to launch the .rfm file directly. Such format will enable faster circuit simulation and is currently supported by circuit solvers for Scattering and Admittance representations only. 
    #15 or RFM-SPECTRE 
    def idemmp_export(self, inFile,out_mod_file, output_formats):
        inFile=os.path.abspath(inFile)
        out_mod_file=os.path.abspath(out_mod_file)
        
        inFile_no_ext=os.path.splitext(inFile)[0]
        mod_no_ext=os.path.splitext(out_mod_file)[0]        
        bat_filename=out_mod_file+".export.bat"        
        with open(bat_filename, 'w') as f:
            for output_format in output_formats:
                f.write(f'"{self.idemmp_export_path}" -ih5 "{inFile}" -o  '
                        f'"{out_mod_file}" -type {output_format} -gnd 2\n')
            
        subprocess.call(bat_filename)
        
    def create_idem_model(self, sparamfile, cirfile,orderMin=4,
                          orderStep=2, orderMax=10, bandwidth=2e9,
                          DC=1, tol=0.001,
                          output_formats=["Touchstone","HSPICE-LAPLACE"],
                          fitting_xml=None, passivity_xml=None):
        sparamfile=os.path.abspath(sparamfile)
        cirfile=os.path.abspath(cirfile)
        
        cirFile_no_ext=os.path.splitext(cirfile)[0]
          
        midmod=cirFile_no_ext+".mod.h5"
        try:
            self.idemmp_fitting(sparamfile,midmod,orderMin=orderMin,
                                orderStep=orderStep, orderMax=orderMax,
                                bandwidth=bandwidth, DC=DC,
                                tol=tol,xml=fitting_xml)
            success = self.idemmp_passivity(midmod,midmod,xml=passivity_xml)
            if not success:
                return success
            if self.idemmp_passivity_check(midmod): #Only export Passive models
                self.idemmp_export(midmod, cirfile, output_formats)              
            #self.idemmp_export(midmod,cirfile,8)
            return success
        except:
            print("Error: Model creation failed")
            return False