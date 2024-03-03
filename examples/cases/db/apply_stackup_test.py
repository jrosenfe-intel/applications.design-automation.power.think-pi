from thinkpi.flows import tasks
from thinkpi.operations import speed as spd


if __name__ == '__main__':
    db = spd.Database(r"D:\jrosenfe\thinkpi_env\spd_files\brd_DPS_pk187_080421.spd")
    db.load_flags['plots'] = False
    db.load_data()

    pkg = tasks.PsiTask(db)
    pkg.apply_stackup(r"D:\jrosenfe\thinkpi_env\spd_files\yoni_test_stackup.csv",
                      r"D:\jrosenfe\thinkpi_env\material\Materials_WW25'23.txt")
    tcl_fname = pkg.create_tcl(('PowerSI', 'extraction'))
    pkg.run_tcl(tcl_fname, pkg.exec_paths['sigrity'][0])