from thinkpi.operations import lib
import time


if __name__ == '__main__':
    lib_mgr = lib.LibManager(root=r"C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\lib_manager")
    
    # Create a new project
    lib_mgr.new_project(project_name='GNR',
                        study_name='rev0',
                        rail_name='VCCIN')

    # Copy a project
    time.sleep(1)
    lib_mgr.new_project(project_name='OKS',
                        study_name='rev0',
                        rail_name='VCCIN',
                        copy_project='GNR')
    
    # Create a new study
    time.sleep(1)
    lib_mgr.new_study(project_name='OKS',
                        study_name='rev0.3',
                        rail_name='VCCIN')

    # Copy a study
    time.sleep(1)
    lib_mgr.new_study(project_name='OKS',
                        study_name='rev0.5',
                        rail_name='VCCIN',
                        copy_study='rev0')

    # Create a new rail
    time.sleep(1)
    lib_mgr.new_rail(project_name='OKS',
                    study_name='rev0',
                    rail_name='VCCINF')
    
    # Copy a rail
    time.sleep(1)
    lib_mgr.new_rail(project_name='OKS',
                    study_name='rev0',
                    rail_name='VCCINFAON',
                    copy_rail='VCCINF')

    time.sleep(1)

    a=lib_mgr.tree()
    
    # Comment out when testing the section above
    """
    lib_mgr.delete_project('GNR')
    time.sleep(1)
    lib_mgr.delete_rail('OKS', 'VCCINFAON')
    time.sleep(1)
    lib_mgr.delete_study('OKS', 'rev0.5', 'VCCIN')
    """



    
    
    
