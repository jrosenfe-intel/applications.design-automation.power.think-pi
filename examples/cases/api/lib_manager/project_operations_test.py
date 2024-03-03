from thinkpi.backend_api import lib
import time


if __name__ == '__main__':
    lib_mgr = lib.LibManager(root=r"D:\jrosenfe\lib_manager")
    
    # Create a new project
    # lib_mgr.new_project(project_name='GNR',
    #                     study_name='rev0',
    #                     rail_name='VCCIN')

    # Copy a project
    # time.sleep(1)
    # lib_mgr.new_project(project_name='OKS',
    #                     study_name='rev0',
    #                     rail_name='VCCIN',
    #                     copy_project='GNR')
    
    # # Create a new study
    # time.sleep(1)
    # lib_mgr.new_study(project_name='OKS',
    #                     study_name='rev0.3',
    #                     rail_name='VCCIN')

    # # Copy a study
    # time.sleep(1)
    # lib_mgr.new_study(project_name='OKS',
    #                     study_name='rev0.5',
    #                     rail_name='VCCIN',
    #                     copy_study='rev0')

    # # Create a new rail
    # time.sleep(1)
    # lib_mgr.new_rail(project_name='OKS',
    #                 study_name='rev0',
    #                 rail_name='VCCINF')
    
    # # Copy a rail
    # time.sleep(1)
    # lib_mgr.new_rail(project_name='OKS',
    #                 study_name='rev0',
    #                 rail_name='VCCINFAON',
    #                 copy_rail='VCCINF')

    # time.sleep(1)
    # tree = lib_mgr.tree(verbose=False)
    # lib_mgr.path_to_dict()
    
    # Comment out when testing the section above
    """
    lib_mgr.delete_project('GNR')
    time.sleep(1)
    lib_mgr.delete_rail('OKS', 'VCCINFAON')
    time.sleep(1)
    lib_mgr.delete_study('OKS', 'rev0.5', 'VCCIN')
    """

    #lib_mgr.add_folder(r"E:\intel\lib_manager\fds\test")
    #time.sleep(1)

    #print(lib_mgr.get_resource_info())

    #print(lib_mgr.get_path_content(r"D:\jrosenfe\ThinkPI\app\frontend".split("\\")))

    print(lib_mgr.get_path_content("C:"))


    #r = lib_mgr.scan_servers()



    
    
    
