# ------------- Introduction -------------
'''
In this phase, both swithcing (VXBR*) and vout plane ports are placed automatically.
If desired, ports can be placed based on boxes which are placed prior in the database.
Not that DC refinement check box is not enabled due to a missing tcl command, so for now
the user must check this box manually.

This flow implements the following tasks:
- Placing switching and output ports
- Merge switching nets
- Setup Clarity simulation based on user inputs,
  i.e., frequencies, meshing, number of cpus, etc.
'''

# ------------- User defined parameters -------------
r"""
PROCESSED_DATABASE_PATH_NAME = r"..\thinkpi_test_db\spr\clarity\spr-mcc_k42410-001_cfc-cfn-io_2020_10_30_22_48_cfc_ios_cfns_thinkPI_process.spd"
PWR_NET_NAMES = ['VXBR_VCCCFNHCB*','VCCCFNHCB'] # You can also use wildcards

NUM_SINK_PORTS = 20
PORTS_LAYER = 'Signal$surface_outer'
NETS_TO_MERGE = 'VXBR_VCCCFNHCB*'
RADIUS = 1e-3 # Radius in meters to look for net to merge to
MAP_FILE_NAME = r"..\thinkpi_test_db\spr\clarity\net_merge_map.csv"

# If True, NUM_SINK_PORTS will be ignored
# If True, it is assumed boxes are placed in the database
# by the user prior to running this flow
USE_BOXES = False
"""

r'''
# Inputs
# ------
PROCESSED_DATABASE_PATH_NAME = r"..\thinkpi_test_db\dmr\dmr_ap_pwr_vcciose_cfcmem_23ww07p5_odb_process.spd"
PWR_NET_NAMES = ['VXBR_UCIEOSE_PH0','VXBR_UCIEOSE_PH1','VCCIO_SE'] # You can also use wildcards

NUM_SINK_PORTS = 1000
PORTS_LAYER = 'Signal$surface'
NETS_TO_MERGE = ['VXBR_UCIEOSE_PH0','VXBR_UCIEOSE_PH1']

# If True, NUM_SINK_PORTS will be ignored
# If True, it is assumed boxes are placed in the database
# by the user prior to running this flow
USE_BOXES = False

# Rail to remove on surface layer only to adhere to correct 3D ports placement 
INPUT_RAIL = 'VCCIN'

# Recommended to use XMesh for large rails.
# For example, layout area > 10x10 mm^2 and number of port > 100.
# XMesh is a massively distributed meshing technology that can be
# distributed to multiple CPUs. It is applied during the initial mesh generation. 
# XMesh shows significant performance improvement when extracting large domains.
# XMesh or DMesh can be used if layout is relatively small, i.e., a single core.
MESH = 'XMesh'

# Outputs
# -------
MERGED_DATABASE_NAME = r'..\thinkpi_test_db\spr\clarity\merged_net_db.spd'
TCL_FILE_NAME = r"clarity_setup_test.tcl"
'''

r'''
# Inputs
# ------
PROCESSED_DATABASE_PATH_NAME = r"..\thinkpi_test_db\GNR\clarity_preprocess_debug\gnr_hcc_vccin-vccd-fivra-inf_odb_2023_05_23_18_44_processed_clarity.spd"
PWR_NET_NAMES = 'VCCIO_PCIE0_IODIE00' # You can also use wildcards and use a list

NUM_SINK_PORTS = 22
PORTS_LAYER = 'Signal$surface_outer'
NETS_TO_MERGE = None

# If True, NUM_SINK_PORTS will be ignored
# If True, it is assumed boxes are placed in the database
# by the user prior to running this flow
USE_BOXES = False

# Rail to remove on surface layer only to adhere to correct 3D ports placement 
INPUT_RAIL = 'VCCFA_EHV_FIVRA'

# Recommended to use XMesh for large rails.
# For example, layout area > 10x10 mm^2 and number of port > 100.
# XMesh is a massively distributed meshing technology that can be
# distributed to multiple CPUs. It is applied during the initial mesh generation. 
# XMesh shows significant performance improvement when extracting large domains.
# XMesh or DMesh can be used if layout is relatively small, i.e., a single core.
MESH = 'DMesh'

# Do not set the number to more than the number of cores a server has
# Do not use all the resources of a shared server for one simulation
# For large designs (ex. >10x10mm, >100 ports),
# it is recommended to use 32 cores or more (if the server permits)
NUM_CORES = 32

# Outputs
# -------
MERGED_DATABASE_NAME = r'..\thinkpi_test_db\GNR\clarity_preprocess_debug\gnr_hcc_vccin-vccd-fivra-inf_odb_2023_05_23_18_44_processed_clarity_ports.spd'
TCL_FILE_NAME = r"clarity_setup_ports.tcl"
'''

r'''
# Inputs
# ------
PROCESSED_DATABASE_PATH_NAME = r"..\thinkpi_test_db\GNR\gnr_hcc_pcie1_2023_05_23_18_44_processed_clarity_boxes.spd"
PWR_NET_NAMES = 'VCCIO_PCIE1_IODIE00' # You can also use wildcards and use a list

NUM_SINK_PORTS = 22
PORTS_LAYER = 'Signal$surface_outer'
NETS_TO_MERGE = None

# If True, NUM_SINK_PORTS will be ignored
# If True, it is assumed boxes are placed in the database
# by the user prior to running this flow
USE_BOXES = True

# Rail to remove on surface layer only to adhere to correct 3D ports placement 
INPUT_RAIL = 'VCCFA_EHV_FIVRA'

# Recommended to use XMesh for large rails.
# For example, layout area > 10x10 mm^2 and number of port > 100.
# XMesh is a massively distributed meshing technology that can be
# distributed to multiple CPUs. It is applied during the initial mesh generation. 
# XMesh shows significant performance improvement when extracting large domains.
# XMesh or DMesh can be used if layout is relatively small, i.e., a single core.
MESH = 'DMesh'

# Do not set the number to more than the number of cores a server has
# Do not use all the resources of a shared server for one simulation
# For large designs (ex. >10x10mm, >100 ports),
# it is recommended to use 32 cores or more (if the server permits)
NUM_CORES = 32

# Outputs
# -------
MERGED_DATABASE_NAME = r'..\thinkpi_test_db\GNR\gnr_hcc_vccin-vccd-fivra-inf_odb_2023_05_23_18_44_processed_clarity.spd'
TCL_FILE_NAME = r"clarity_setup_ports.tcl"
'''

r'''
# Inputs
# ------
PROCESSED_DATABASE_PATH_NAME = r"D:\jrosenfe\ThinkPI\thinkpi_test_db\OKS\clarity\dmr_ap_ucc1_pwr_vccin_uciea_23ww42_odb_processed_clarity_box_v2.spd"
PWR_NET_NAMES = ['VCCUCIEA_SE','VXBR_UCIEA_SE_P00','VXBR_UCIEA_SE_P01'] # You can also use wildcards and use a list

NUM_SINK_PORTS = 116
PORTS_LAYER = 'Signal$surface'
NETS_TO_MERGE = ['VXBR_UCIEA_SE_P00','VXBR_UCIEA_SE_P01']

# If True, NUM_SINK_PORTS will be ignored
# If True, it is assumed boxes are placed in the database
# by the user prior to running this flow
USE_BOXES = True

# Rail to remove on surface layer only to adhere to correct 3D ports placement 
INPUT_RAIL = 'VCCIN_EHV1'

# Recommended to use XMesh for large rails.
# For example, layout area > 10x10 mm^2 and number of port > 100.
# XMesh is a massively distributed meshing technology that can be
# distributed to multiple CPUs. It is applied during the initial mesh generation. 
# XMesh shows significant performance improvement when extracting large domains.
# XMesh or DMesh can be used if layout is relatively small, i.e., a single core.
MESH = 'DMesh'

# Do not set the number to more than the number of cores a server has
# Do not use all the resources of a shared server for one simulation
# For large designs (ex. >10x10mm, >100 ports),
# it is recommended to use 32 cores or more (if the server permits)
NUM_CORES = 36

# Outputs
# -------
MERGED_DATABASE_NAME = r"D:\jrosenfe\ThinkPI\thinkpi_test_db\OKS\clarity\dmr_ap_ucc1_pwr_vccin_uciea_23ww42_odb_processed_clarity_box_v2_merged.spd"
TCL_FILE_NAME = r"D:\jrosenfe\ThinkPI\thinkpi_test_db\OKS\clarity\clarity_setup_ports.tcl"
'''


r'''
# Inputs
# ------
PROCESSED_DATABASE_PATH_NAME = r"D:\jrosenfe\ThinkPI\thinkpi_test_db\CWF\cwf_ap_point_cfc_23ww37p1_patch_clarity.spd"
PWR_NET_NAMES = ['VCCCFC_E_CDIE09_1', 'VXBR_CFC_E_P0*_CDIE09'] # You can also use wildcards

NUM_SINK_PORTS = 100
PORTS_LAYER = 'Signal$surface_outer'
NETS_TO_MERGE = ['VXBR_CFC_E_P0*_CDIE09']

# If True, NUM_SINK_PORTS will be ignored
# If True, it is assumed boxes are placed in the database
# by the user prior to running this flow
USE_BOXES = False

# Rail to remove on surface layer only to adhere to correct 3D ports placement 
INPUT_RAIL = 'VCCIN'

# Recommended to use XMesh for large rails.
# For example, layout area > 10x10 mm^2 and number of port > 100.
# XMesh is a massively distributed meshing technology that can be
# distributed to multiple CPUs. It is applied during the initial mesh generation. 
# XMesh shows significant performance improvement when extracting large domains.
# XMesh or DMesh can be used if layout is relatively small, i.e., a single core.
MESH = 'DMesh'

# Do not set the number to more than the number of cores a server has
# Do not use all the resources of a shared server for one simulation
# For large designs (ex. >10x10mm, >100 ports),
# it is recommended to use 32 cores or more (if the server permits)
NUM_CORES = 36

# Outputs
# -------
MERGED_DATABASE_NAME = r"D:\jrosenfe\ThinkPI\thinkpi_test_db\CWF\cwf_ap_point_cfc_23ww37p1_patch_clarity_auto_merged_v3_test.spd"
TCL_FILE_NAME = r"D:\jrosenfe\ThinkPI\thinkpi_test_db\CWF\clarity_setup_ports_test.tcl"
'''

r'''
# Inputs
# ------
PROCESSED_DATABASE_PATH_NAME = r"..\thinkpi_test_db\DMR\dmr_ap_ucc1_mlc_23ww43p3_proc_clean_ian_boxes.spd"
PWR_NET_NAMES = ['VXBR_MLC_P00','VXBR_MLC_P01','VCCMLC'] # You can also use wildcards

NUM_SINK_PORTS = 64
PORTS_LAYER = 'Signal$surface'
NETS_TO_MERGE = ['VXBR_MLC_P00','VXBR_MLC_P01']

# If True, NUM_SINK_PORTS will be ignored
# If True, it is assumed boxes are placed in the database
# by the user prior to running this flow
USE_BOXES = False

# Rail to remove on surface layer only to adhere to correct 3D ports placement 
INPUT_RAIL = 'VCCIN_EHV'

# Recommended to use XMesh for large rails.
# For example, layout area > 10x10 mm^2 and number of port > 100.
# XMesh is a massively distributed meshing technology that can be
# distributed to multiple CPUs. It is applied during the initial mesh generation. 
# XMesh shows significant performance improvement when extracting large domains.
# XMesh or DMesh can be used if layout is relatively small, i.e., a single core.
MESH = 'XMesh'

# Do not set the number to more than the number of cores a server has
# Do not use all the resources of a shared server for one simulation
# For large designs (ex. >10x10mm, >100 ports),
# it is recommended to use 32 cores or more (if the server permits)
NUM_CORES = 36

# Outputs
# -------
MERGED_DATABASE_NAME = r"..\thinkpi_test_db\DMR\dmr_ap_ucc1_mlc_23ww43p3_proc_clean_thinkPI_process_ian.spd"
TCL_FILE_NAME = r"..\thinkpi_test_db\DMR\clarity_setup_ports_test_ian.tcl"
'''

# Inputs
# ------
PROCESSED_DATABASE_PATH_NAME = r"..\thinkpi_test_db\DMR\dmr_ap_ucc1_23ww43p3_POR_VCCR_Diemodel_1_Clarity_boxes.spd"
# Include here all your VXBR nets as well
# You can also use wildcards
PWR_NET_NAMES = ['VCCR_C01_S3','VXBR_R_CLST01_S3_P0*']

NUM_SINK_PORTS = 1
PORTS_LAYER = 'Signal$surface'
NETS_TO_MERGE = ['VXBR_R_CLST01_S3_P0*']

# If True, NUM_SINK_PORTS will be ignored
# If True, it is assumed boxes are placed in the database
# by the user prior to running this flow
USE_BOXES = True

# Rail to remove on surface layer only to adhere to correct 3D ports placement 
INPUT_RAIL = 'VCCIN_EHV1'

# Recommended to use XMesh for large rails.
# For example, layout area > 10x10 mm^2 and number of port > 100.
# XMesh is a massively distributed meshing technology that can be
# distributed to multiple CPUs. It is applied during the initial mesh generation. 
# XMesh shows significant performance improvement when extracting large domains.
# XMesh or DMesh can be used if layout is relatively small, i.e., a single core.
MESH = 'XMesh'

# Do not set the number to more than the number of cores a server has
# Do not use all the resources of a shared server for one simulation
# For large designs (ex. >10x10mm, >100 ports),
# it is recommended to use 32 cores or more (if the server permits)
NUM_CORES = 36

# Outputs
# -------
MERGED_DATABASE_NAME = r"..\thinkpi_test_db\DMR\dmr_ap_ucc1_23ww43p3_POR_VCCR_Diemodel_1_Clarity_ports.spd"
TCL_FILE_NAME = r"..\thinkpi_test_db\DMR\clarity_setup_DMR_VCCR.tcl"

# ------------- Don't modify anything below this line -------------
from thinkpi.flows import tasks

if __name__ == '__main__':
    pkg = tasks.ClarityTask(PROCESSED_DATABASE_PATH_NAME)

    if isinstance(PWR_NET_NAMES, str):
        PWR_NET_NAMES = [PWR_NET_NAMES]
    pkg.place_ports(pwr_net=[rail for rail in PWR_NET_NAMES
                                if 'vxbr' not in rail.lower()],
                            num_ports=NUM_SINK_PORTS,
                            from_boxes=USE_BOXES)
    pkg.db.save(MERGED_DATABASE_NAME)
    
    pkg.db.delete_overlap_vias(save=False)
    pkg.db.merge_nets(fname_db=MERGED_DATABASE_NAME,
                      nets_to_merge=NETS_TO_MERGE,
                      save=False)
    cmds = pkg.delete_metal(INPUT_RAIL,
                            MERGED_DATABASE_NAME,
                            save=True)

    pkg = tasks.ClarityTask(MERGED_DATABASE_NAME)
    pkg.db.prepare_plots(PORTS_LAYER)
    pkg.db.plot(PORTS_LAYER)

    pkg.setup_clarity_sim2(num_cores=NUM_CORES,
                           mesh=MESH)

    tcl_fname = pkg.create_tcl(
                    ('Clarity 3D Layout', '3DFEMExtraction'),
                   TCL_FILE_NAME, cmds
                )
    pkg.run_tcl(tcl_fname, pkg.exec_paths['sigrity'][0])

    
    


    