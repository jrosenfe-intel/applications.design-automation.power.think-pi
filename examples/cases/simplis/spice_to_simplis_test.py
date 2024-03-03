from thinkpi.operations import spice_ops as sp

if __name__ == '__main__':
    
    hspice = sp.Spice(root_spice_file=r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\HSPICE\TRAN_MAIN_20ww36\TRAN_ANR_20ww28_DIG.sp",
                    root_spice_deck=r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\HSPICE")
    hspice.convert(r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\HSPICE\flat.sp")


    r"""
    hspice = sp.Spice(root_spice_file=r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\HSPICE1\TRAN_MAIN_20ww24\TRAN_ANR_20ww24.sp",
                    root_spice_deck=r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\HSPICE1")
    hspice.convert(r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\HSPICE1\flat.sp")
    """
    

    

    





    