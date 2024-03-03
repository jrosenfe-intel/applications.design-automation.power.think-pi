from thinkpi.operations import speed as spd
from thinkpi.flows.tcl import Tcl


if __name__ == '__main__':
    db = spd.Database(r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\derrick\gnr_x1_pwr_odb_2022_1_19_10_11_prepared.spd")
    t = Tcl(db)
    all_cmds = [t.open(r"N:\EPS2\USERS\jrosenfe\Derrick\gnr_x1_pwr_odb_2022_1_19_10_11_prepared.spd"),
                t.setup_padstack(r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\derrick\gnr_x1_pwr_odb_2022_1_19_10_11_prepared_padstack.csv"),
                t.close()]
    t.create_tcl(('PowerSI', 'extraction'),
                 r'N:\EPS2\USERS\jrosenfe\Derrick\set_stackup.tcl', *all_cmds)

    #t.json_to_tcl(r'N:\EPS2\USERS\jrosenfe\Derrick', 'assign_pwr_tcl_cmds.json',
    #                'assign_pwr_test.tcl')