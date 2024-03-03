# ------------- Introduction -------------
'''
This is an optional DC analysis where DC gradients are calculated
within a pre-defined cells on the surface layer of the package.
User is able to define multiple net names with multiple cell sizes.

An Excel file is saved with these results.
'''

# ------------- User defined parameters -------------

r'''
# Inputs
# ------
DATABASE_NAME = r'..\thinkpi_test_db\DMR\dmr_ap_ucc1_pwr_vccddr_hv_dcm_mlc_23ww43p3_odb_v2_cut_core_vccr_proc_POR_PDC.spd'
XML_DATA = r'..\thinkpi_test_db\DMR\dmr_ap_ucc1_pwr_vccddr_hv_dcm_mlc_23ww43p3_odb_v2_cut_core_vccr_proc_POR_PDC_SimulationResult.xml'
CELL_SIZES = [(1e-3, 1e-3), (1e-3, 3e-3)] # (dx, dy) in Meters. Add as many as required.
PWR_NET_NAMES = ['VCCR_C*', 'VCCR_C*'] # Can also use wildcards

# Outputs
# -------
REPORT_NAME = r'..\thinkpi_test_db\DMR\dc_gradient.xlsx'
'''

r'''
# Inputs
# ------
DATABASE_NAME = r'..\thinkpi_test_db\SRF\SRF_CFC_W_22ww32p5_Rev1_vccin_inf_cuts_pdc21.spd'
XML_DATA = r'..\thinkpi_test_db\SRF\SRF_CFC_W_22ww32p5_Rev1_vccin_inf_cuts_pdc21_SimulationResult.xml'
CELL_SIZES = [(1e-3, 1e-3), (1e-3, 3e-3)] # (dx, dy) in Meters. Add as many as required.
PWR_NET_NAMES = 'VCCCFC_W_CDIE09' # Can also use wildcards

# Outputs
# -------
REPORT_NAME = r'..\thinkpi_test_db\SRF\srf_cfc_compute_dc_gradient.xlsx'
'''

r"""
# Inputs
# ------
DATABASE_NAME = r'..\thinkpi_test_db\OKS\inf_brd_ww43_brd_ww45_merged_sink_vr_setup_clean.spd'
XML_DATA = r'..\thinkpi_test_db\OKS\inf_brd_ww43_brd_ww45_merged_sink_vr_setup_clean_SimulationResult.xml'
CELL_SIZES = [(1e-3, 1e-3), (1e-3, 3e-3),(3e-3, 1e-3)] # (dx, dy) in Meters. Add as many as required.
PWR_NET_NAMES = 'VCCINF' # Can also use wildcards

# Outputs
# -------
REPORT_NAME = r'..\thinkpi_test_db\OKS\dc_gradient.xlsx'
"""

r"""
# Inputs
# ------
DATABASE_NAME = r'..\thinkpi_test_db\GNR\gnr_ap_sp_vcccore_4ph_coax1p0_rev1_thermal.spd'
XML_DATA = r'..\thinkpi_test_db\GNR\gnr_ap_sp_vcccore_4ph_coax1p0_rev1_thermal_SimulationResult.xml'
CELL_SIZES = [(1e-3, 1e-3), (1e-3, 3e-3), (3e-3, 1e-3)] # (dx, dy) in Meters. Add as many as required.
PWR_NET_NAMES = 'VCCINF' # Can also use wildcards

# Outputs
# -------
REPORT_NAME = r'dc_gradient.xlsx'
"""

r"""
# Inputs
# ------
DATABASE_NAME = r'..\thinkpi_test_db\DMR\dmr_ap_ucc1_fivr_imh_23ww46p3_odb_proc_vrms.spd'
XML_DATA = r'..\thinkpi_test_db\DMR\dmr_ap_ucc1_fivr_imh_23ww46p3_odb_proc_vrms_SimulationResult.xml'
CELL_SIZES = [(1e-3, 1e-3), (1e-3, 3e-3)] # (dx, dy) in Meters. Add as many as required.
PWR_NET_NAMES = 'VCCCFCIO*' # Can also use wildcards

# If True generates report for only the top layer,
# otherwise for all layers.
TOP_LAYER_ONLY = True

# Outputs
# -------
REPORT_NAME = r'..\thinkpi_test_db\DMR\dc_gradient.xlsx'
"""
# Inputs
# ------
DATABASE_NAME = r'..\thinkpi_test_db\DMR\dmr_ap_ucc1_fivr_imh_23ww46p3_odb_proc_vrms_cut_thinkpi_sinks.spd'
XML_DATA = r'..\thinkpi_test_db\DMR\dmr_ap_ucc1_fivr_imh_23ww46p3_odb_proc_vrms_cut_thinkpi_sinks_SimulationResult.xml'
CELL_SIZES = [(1e-3, 1e-3), (1e-3, 3e-3)] # (dx, dy) in Meters. Add as many as required.
PWR_NET_NAMES = 'VCCCFCIO_2' # Can also use wildcards

# If True generates report for only the top layer,
# otherwise for all layers.
TOP_LAYER_ONLY = False

# Outputs
# -------
REPORT_NAME = r'..\thinkpi_test_db\DMR\dc_gradient.xlsx'



# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks
from thinkpi.operations import speed as spd

if __name__ == '__main__':
    
    
    db = spd.Database(DATABASE_NAME)
    db.load_flags['plots'] = False
    db.load_data()

    brd_pkg = tasks.PdcTask(db)

    brd_pkg.dc_gradient(XML_DATA, PWR_NET_NAMES,
                        CELL_SIZES, REPORT_NAME,
                        TOP_LAYER_ONLY)
