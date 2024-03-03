# ------------- Introduction -------------
'''
The user is expected to modify the sink and vrm .csv file
that will be used in this phase.

This task will perform the following:
- import sink and vrm parameters after user modifications
- merge nets

After completion of this phase inspect the modified database and run simulation.
After completion of the simulation, move to the next phase where results are aggregated.
'''

# ------------- User defined parameters -------------

r'''
# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\SRF\fivr_dc\srf_ap_zcc_res_ext_2023_01_19_08_49_proc_vload_t_sense_23ww4p2.spd"

SINK_SETUP_FILE = r"..\thinkpi_test_db\SRF\fivr_dc\SRF_sinksetup.xlsx"
VRM_SETUP_FILE = r"..\thinkpi_test_db\SRF\fivr_dc\SRF_vrmsetup.xlsx"

# You can also use wildcards
NETS_TO_MERGE = ['VXBR_CFC_E_*_CDIE09']

# Outputs
# -------
MERGED_DATABASE_NAME = r"..\thinkpi_test_db\SRF\fivr_dc\srf_ap_zcc_res_ext_2023_01_19_08_49_proc_vload_t_sense_23ww4p2_merged.spd"

'''

# Inputs
# ------
DATABASE_PATH_NAME = r"..\thinkpi_test_db\GNR\gnr_hcc_fullstack_pwr_100_2023_08_25_16_26_processed.spd"

SINK_SETUP_FILE = r"..\thinkpi_test_db\GNR\gnr_hcc_iodie_sinksetup.csv"
VRM_SETUP_FILE = r"..\thinkpi_test_db\GNR\gnr_hcc_iodie_vrmsetup.csv"

# You can also use wildcards
NETS_TO_MERGE = ['VXBR*IODIE00','VXBR*IODIE04']

# Outputs
# -------
MERGED_DATABASE_NAME = r"..\thinkpi_test_db\GNR\gnr_hcc_fullstack_pwr_100_2023_08_25_16_26_processed_vxbr_merge.spd"


# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks
from thinkpi.operations import speed as spd

if __name__ == '__main__':
    db = spd.Database(DATABASE_PATH_NAME)
    db.load_flags['plots'] = False
    db.load_data()

    pkg_ind = tasks.PdcTask(db)
    pkg_ind.import_sink_setup(SINK_SETUP_FILE)
    pkg_ind.import_vrm_setup(VRM_SETUP_FILE)
    pkg_ind.db.merge_nets(fname_db=MERGED_DATABASE_NAME,
                          nets_to_merge=NETS_TO_MERGE)
    