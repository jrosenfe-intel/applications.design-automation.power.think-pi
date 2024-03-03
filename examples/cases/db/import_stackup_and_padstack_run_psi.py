from thinkpi.operations import speed as spd
from thinkpi.flows.tcl import Tcl
from thinkpi.flows.tasks import Tasks

from thinkpi.tools import psi


task = Tasks(r'k30643-001_r01_odb_2.spd')
task.select_nets(['VCCDDRD_GPIO', 'VCCDDQ_SXP'], 'VSS')
#task.preprocess(r"stackup.csv",
#                r"padstack.csv",0,r"k30643-001_r01_odb_2_proc.spd")
task.preprocess(r"stackup.csv",
                r"padstack.csv",
                cut_margin=0,
                db_fname=r"yk30643_001_r01_odb_2_proc.spd")

#task.setup_psi(100)
task.create_tcl(r"import_stackup_padstack.tcl")

psi=psi.psi()
psi.set_psi_path(r'C:/"Cadence"/"Sigrity2021.1"/"tools"/"bin"')
psi.psi_run_tcl(r'import_stackup_padstack.tcl')

