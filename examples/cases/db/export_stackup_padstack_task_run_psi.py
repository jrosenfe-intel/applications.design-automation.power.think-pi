from thinkpi.flows.tasks import Tasks
from thinkpi.tools import psi


if __name__ == '__main__':
    
    task = Tasks(r'k30643-001_r01_odb_2.spd')
    task.export_stackup_padstack(r'export_stackup.tcl','stackup.csv','padstack.csv')
    
    psi=psi.psi()
    psi.set_psi_path(r'C:/"Cadence"/"Sigrity2021.1"/"tools"/"bin"')
    psi.psi_run_tcl(r'export_stackup.tcl')