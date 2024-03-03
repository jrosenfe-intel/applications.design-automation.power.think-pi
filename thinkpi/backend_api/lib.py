import os
import shutil
import psutil
import socket
from time import sleep
import json
from pathlib import Path
from datetime import datetime
import math
from operator import itemgetter

import numpy as np
from concurrent.futures import ThreadPoolExecutor

import requests
import pandas as pd

from thinkpi import _thinkpi_path
from thinkpi.config import thinkpi_conf as cfg


class ProjectLevels:
    '''Class that defines project folder levels and structure.
    '''

    def __init__(self, project_name, study_name, rail_name):
        '''Initializes the generated object.

        :param project_name: The name of the project or program
        :type project_name: str
        :param study_name: The name of the study or milestone
        :type study_name: str
        :param rail_name: The name of the power supply rail
        :type rail_name: str
        '''

        self.project_name = project_name
        self.study_name = study_name
        self.rail_name = rail_name

        self.level0 = {self.project_name: [self.rail_name, 'db']}
        self.level1 = {self.rail_name: [f'config_{self.study_name}', f'reports_{self.study_name}',
                                        f'logs_{self.study_name}', f'powerdc_{self.study_name}',
                                        f'electro_thermal_{self.study_name}',
                                        f'hspice_{self.study_name}', f'powersi_{self.study_name}',
                                        f'clarity_{self.study_name}', f'fivr_{self.study_name}',
                                        f'simplis_{self.study_name}'],
                        'db': ['package', 'board', 'interposer', 'reports']
                    }
        self.level2 = {f'powerdc_{self.study_name}': ['db', 'results'],
                        f'electro_thermal_{self.study_name}': ['db', 'materials', 'results'],
                        f'hspice_{self.study_name}': ['ac', 'tran', 'brd', 'pkg',
                                                        'c4_bumps', 'cap_models',
                                                        'die', 'icct', 'skt', 'vr',
                                                        'results'],
                        f'powersi_{self.study_name}': ['db', 'sparam',
                                                        'macromodel', 'results'], 
                        f'clarity_{self.study_name}': ['db', 'sparam',
                                                        'macromodel', 'results'],
                        f'fivr_{self.study_name}': ['die', 'pkg_ind',
                                                    'icct', 'results'],
                        f'simplis_{self.study_name}': ['db', 'vr_models', 'scripts',
                                                        'icct', 'cap_models',
                                                        'schematics', 'results']}
        self.levels = [self.level0, self.level1, self.level2]


class LibManager:
    '''Class that defines the different operations related to 
    library management.
    '''

    def __init__(self, root=None):
        '''Initializes the generated object.

        :param root: Path pointing to the root of the project library.
        If None is given, the current working directory is used, defaults to None
        :type root: str or NoneType, optional
        '''

        self.root = Path.cwd() if root is None else Path(root)
        self.levels = None
        self.paths = []

    def update(self):

        # Copy code code
        shutil.copytree(cfg.SOURCE_CORE, cfg.DEST_CORE, dirs_exist_ok=True)

        # Copy backend code
        shutil.copytree(cfg.SOURCE_BACKEND, cfg.DEST_BACKEND, dirs_exist_ok=True)

    def find_drives(self):
        """Finds all available drives connected to the machine.

        :return: Drive letters
        :rtype: list[str]
        """        

        return [f'{chr(letter)}:' for letter in range(ord('A'), ord('Z') + 1)
                if os.path.exists(f'{chr(letter)}:')]
    
    def get_server_info(self, ip_address):
        """Sends a requests to a specific ip address to obtain the machine information.

        :param ip_address: Simulation server ip address
        :type ip_address: str
        :return: Machine resource information
        :rtype: dict
        """        

        try:
            r = requests.get(f'http://{ip_address}:{cfg.BACKEND_PORT}/get-server-info', timeout=10)
        except (requests.ConnectionError, requests.exceptions.ReadTimeout):
            return ip_address
        
        return json.loads(r.text)
    
    def score_servers(self, responses, cpu_weight=0.35,
                     used_mem_weight=0.3, tot_mem_weight=0.2,
                     num_cpus_weight=0.1, num_users_weight=0.05):
        
        servers_list = self.get_server_list()
        hostname_by_ip = {ip:host_name for ip, host_name in zip(servers_list['ip_address'],
                                                              servers_list['host_name'])}
<<<<<<< HEAD
        
=======
>>>>>>> 1c6304a4c09f18c88dd2e91926471b4e2ffc3c7e
        results = {}
        data = []
        for response in responses:
            if isinstance(response, str): # Error of some sort
                results[hostname_by_ip[response]] = 'Connection error'
            else: # Success
                results[response['host_name']] = response
                data += [response['cpu_per'], response['used_memory_per'],
                            1/response['total_memory_GB'], 1/response['num_cpus'],
                            len(response['users'])]
        
        sorted_servers = []
        if data:
            data_min = min(data)
            data_range = max(data) - data_min
            for host_name, result in results.items():
                if result == 'Connection error':
                    sorted_servers.append((host_name, np.inf))
                else:
                    score = ((result['cpu_per'] - data_min)/data_range*cpu_weight
                             + (result['used_memory_per'] - data_min)/data_range*used_mem_weight
                             + (1/result['total_memory_GB'] - data_min)/data_range*tot_mem_weight
                             + (1/result['num_cpus'] - data_min)/data_range*num_cpus_weight
                             + (len(result['users']) - data_min)/data_range*num_users_weight
                    )
                    sorted_servers.append((host_name, score))

            sorted_servers = sorted(sorted_servers, key=itemgetter(1))
            sorted_results = []
            for (host_name, score) in sorted_servers:
                if score < np.inf:
                    sorted_results.append({**results[host_name], **{'score': round(score, 3)}})
                else:
                    sorted_results.append({'host_name': host_name,
                                           'cpu_per': '',
                                           'num_cpus': '',
                                           'total_memory_GB': '',
                                           'used_memory_GB': '',
                                           'num_users': '',
                                           'score': 'Connection error'
                                    })
        else:
            sorted_results = [{'host_name': host_name,
                                           'cpu_per': '',
                                           'num_cpus': '',
                                           'total_memory_GB': '',
                                           'used_memory_GB': '',
                                           'num_users': '',
                                           'score': 'Connection error'} 
                                    for host_name in servers_list['host_name']]
        return sorted_results
        
    def scan_servers(self, cpu_weight=0.35,
                     used_mem_weight=0.3, tot_mem_weight=0.2,
                     num_cpus_weight=0.1, num_users_weight=0.05):
        """Scans all the servers specified in csv file to obtain
        their resource information. Based on this information
        a score is calculated for each server to determine which machine
        is the most available for usage.

        :param cpu_weight: The weight to assign to cpu %, defaults to 0.35
        :type cpu_weight: float, optional
        :param used_mem_weight: The weight to assign to used memory %, defaults to 0.3
        :type used_mem_weight: float, optional
        :param tot_mem_weight: The weight to assign to total memory, defaults to 0.2
        :type tot_mem_weight: float, optional
        :param num_cpus_weight: The weight to assign to number of logical cpus, defaults to 0.1
        :type num_cpus_weight: float, optional
        :param num_users_weight: The weight to assign to number of users, defaults to 0.05
        :type num_users_weight: float, optional
        :return: A sorted list of servers based on their score
        from smaller (least used) to larger (most used)
        :rtype: dict
        """        

        servers_list = self.get_server_list()
        hostname_by_ip = {ip:host_name for ip, host_name in zip(servers_list['ip_address'],
                                                              servers_list['host_name'])}

        results = {}
        data = []
        with ThreadPoolExecutor(len(servers_list['ip_address'])) as tpe:
            responses = [response for response in tpe.map(self.get_server_info,
                                                          servers_list['ip_address'])]
            for response in responses:
                if isinstance(response, str): # Error of some sort
                    results[hostname_by_ip[response]] = 'Connection error'
                else: # Success
                    results[response['host_name']] = response
                    data += [response['cpu_per'], response['used_memory_per'],
                             1/response['total_memory_GB'], 1/response['num_cpus'],
                             len(response['users'])]
        
        sorted_servers = []
        if data:
            data_min = min(data)
            data_range = max(data) - data_min
            for host_name, result in results.items():
                if result == 'Connection error':
                    sorted_servers.append((host_name, np.inf))
                else:
                    score = ((result['cpu_per'] - data_min)/data_range*cpu_weight
                             + (result['used_memory_per'] - data_min)/data_range*used_mem_weight
                             + (1/result['total_memory_GB'] - data_min)/data_range*tot_mem_weight
                             + (1/result['num_cpus'] - data_min)/data_range*num_cpus_weight
                             + (len(result['users']) - data_min)/data_range*num_users_weight
                    )
                    sorted_servers.append((host_name, score))

            sorted_servers = sorted(sorted_servers, key=itemgetter(1))
            sorted_results = []
            for (host_name, score) in sorted_servers:
                if score < np.inf:
                    sorted_results.append({**results[host_name], **{'score': round(score, 3)}})
                else:
                    sorted_results.append({'host_name': host_name,
                                           'cpu_per': '',
                                           'num_cpus': '',
                                           'total_memory_GB': '',
                                           'used_memory_GB': '',
                                           'num_users': '',
                                           'score': 'Connection error'
                                    })
                # if score < np.inf:
                #     sorted_results[host_name] = {**results[host_name], **{'score': round(score, 3)}}
                # else:
                #     sorted_results[host_name] = 'Connection error'
        else:
            sorted_results = [{'host_name': host_name,
                                           'cpu_per': '',
                                           'num_cpus': '',
                                           'total_memory_GB': '',
                                           'used_memory_GB': '',
                                           'num_users': '',
                                           'score': 'Connection error'} 
                                    for host_name in servers_list['host_name']]
        return sorted_results
    
    def get_resource_info(self):
        """Obtains machine resources information.

        :return: Available information regarding the specific machine,
        such as, host name, ip address, cpuand memory usage
        :rtype: dict
        """        

        while True:
            try:
                cpu_percent = round(np.mean([cpu for cpu in psutil.cpu_percent(interval=1, percpu=True)
                                             if cpu > 0])
                            )
                break
            except ValueError:
                pass
        users = [user for user in psutil.users() if user.host is not None]
        # Check drives are not a mapped path
        drives = []
        for drive in self.find_drives():
            if os.path.realpath(drive)[:2] != '\\\\':
                drives.append(drive)
        return {'drives': drives,
                'host_name': socket.gethostname(),
                'ip_address': socket.gethostbyname(socket.gethostname()),
                'cpu_per': cpu_percent,
                'num_cpus': psutil.cpu_count(),
                'total_memory_GB': round(psutil.virtual_memory().total/1024**3),
                'free_memory_GB': round(psutil.virtual_memory().free/1024**3),
                'used_memory_GB': round((psutil.virtual_memory().total
                                   - psutil.virtual_memory().free)/1024**3),
                'used_memory_per': round((psutil.virtual_memory().total
                                   - psutil.virtual_memory().free)/psutil.virtual_memory().total*100),
                'users': users,
                'num_users': len(users),
                'port': cfg.BACKEND_PORT
            }
    
    def get_server_list(self):
        """Reads a stored list of simulation server names and ip addresses.

        :return: Simulation servers host names and their corresponding ip addresses 
        :rtype: dict
        """

        return pd.read_csv(Path(_thinkpi_path) / Path('thinkpi/config/resources/servers.csv')).to_dict(orient='list')
        
    def get_path_content(self, path):
        """Finds all folders and files in the specified
        path location and their modification time and size.

        :param path: Path in the file system
        :type path: str
        :return: File and folder names and their corresponding info
        :rtype: dict
        """

        path_info = {'dirs': [], 'files': []}
        for content in Path(path).glob('*'):
            try:
                date_time = datetime.fromtimestamp(content.stat().st_mtime).strftime("%m/%d/%Y %r")
            except OSError:
                date_time = ''
            if content.is_file():
                size = content.stat().st_size
                if size < 1024:
                    size = f'{size} B'
                elif 1024 < size < 1024**2:
                    size = f'{math.ceil(size/1024)} KB'
                elif 1024**2 < size < 1024**3:
                    size = f'{math.ceil(size/1024**2)} MB'   
                else:
                    size = f'{math.ceil(size/1024**3)} GB'
                path_info['files'].append({'name': content.name,
                                            'date_modified': date_time,
                                            'size': size,
                                            'file_type': 'file'})
            else:
                path_info['dirs'].append({'name': content.name,
                                        'date_modified': date_time,
                                        'size': '',
                                        'file_type': 'dir'})

        return path_info

    def tree(self, root=None, verbose=True):
        '''Prints out the entire directory tree starting at the root.

        :param root: Path pointing to the root of the project library.
        If None is given, the existing root path is used, defaults to None
        :type root: str, optional
        :param verbose: If True print out the tree structure,
        otherwise returns the tree as a string, defaults to True
        :type verbose: bool, optional
        :return: If verbose is False a json is returned with the corresponding levels
        :rtype: str
        '''

        root = Path(self.root) if root is None else Path(root)
        tree_json = [{0: root.name}]
        tree = []
        tree.append(f'├─ {root}')
        for path in sorted(root.rglob('*')):
            depth = len(path.relative_to(root).parts)
            spacer = '│    '*depth + '├─ '
            tree.append(f'{spacer}{path.name}')
            tree_json.append({depth: path.name})

        if verbose:
            tree = '\n'.join(tree)
            print(tree)
        else:
            return json.dumps(tree_json)

    def add_folder(self, path):

        Path.mkdir(Path(path))

    def delete_folder(self, path):

        shutil.rmtree(path)

    def path_to_dict(self, root=None):
        root = Path(self.root) if root is None else Path(root)

        d = {'name': os.path.basename(root)}
        if os.path.isdir(root):
            d['children'] = [self.path_to_dict(os.path.join(root,x)) for x in os.listdir(root)]
        else:
            d['type'] = "file"
        return d

    def delete_rail(self, project_name, rail_name):
        '''Deletes a power supply rail and its subsequent folders and files from the project.

        :param project_name: Project name
        :type project_name: str
        :param rail_name: Rail name
        :type rail_name: str
        '''

        shutil.rmtree(Path(self.root, project_name, rail_name))

    def new_rail(self, project_name, study_name, rail_name, copy_rail=None):
        '''Creates a new power supply rail and its subsequent folders in a specific project.
        If 'copy_rail' is provided, creates a copy of the given rail.

        :param project_name: Project name
        :type project_name: str
        :param study_name: Study name
        :type study_name: str
        :param rail_name: Rail name
        :type rail_name: str
        :param copy_rail: Rail name to copy.
        If not given, only empty folders are created, defaults to None
        :type copy_rail: str or NoneType, optional
        '''

        if copy_rail is None:
            self.new_project(project_name, study_name, rail_name)
        else:
            folders = ProjectLevels(project_name, study_name, copy_rail)
            self.levels = folders.levels
            self._create_folder_struct(0, [project_name])
            src_paths = self.paths
            self.paths = []

            folders = ProjectLevels(project_name, study_name, rail_name)
            self.levels = folders.levels
            self._create_folder_struct(0, [project_name])
            dst_paths = self.paths
            self.paths = []

            for src_path, dst_path in zip(src_paths, dst_paths):
                shutil.copytree(src_path, dst_path)

    def delete_study(self, project_name, study_name, rail_name):
        '''Deletes a study and its subsequent folders and files from the project.

        :param project_name: Project name
        :type project_name: str
        :param study_name: Study name
        :type study_name: str
        :param rail_name: Rail name
        :type rail_name: str
        '''

        folders = ProjectLevels(project_name, study_name, rail_name)

        for stem_path in folders.level1[rail_name]:
            shutil.rmtree(Path(self.root, project_name, rail_name, stem_path))

    def new_study(self, project_name, study_name, rail_name, copy_study=None):
        '''Creates a new study and its subsequent folders in a specific project.
        If 'copy_study' is provided, creates a copy of the given study.

        :param project_name: Project name
        :type project_name: str
        :param study_name: Study name
        :type study_name: str
        :param rail_name: Rail name
        :type rail_name: str
        :param copy_study: Study name to copy.
        If not given, only empty folders are created, defaults to None
        :type copy_study: str or NoneType, optional
        '''

        if copy_study is None:
            self.new_project(project_name, study_name, rail_name)
        else:
            folders = ProjectLevels(project_name, copy_study, rail_name)
            self.levels = folders.levels
            self._create_folder_struct(0, [project_name])
            src_paths = self.paths
            self.paths = []

            folders = ProjectLevels(project_name, study_name, rail_name)
            self.levels = folders.levels
            self._create_folder_struct(0, [project_name])
            dst_paths = self.paths
            self.paths = []

            for src_path, dst_path in zip(src_paths, dst_paths):
                _ = shutil.copytree(src_path, dst_path)

    def delete_project(self, project_name):
        '''Deletes a project and all its subsequent folders and files.

        :param project_name: Project name
        :type project_name: str
        '''

        shutil.rmtree(Path(self.root, project_name))

    def new_project(self, project_name, study_name, rail_name, copy_project=None):
        '''Creates a new project and its subsequent folders.
        If 'copy_project' is provided, creates a copy of the given project.

        :param project_name: Project name
        :type project_name: str
        :param study_name: Study name
        :type study_name: str
        :param rail_name: Rail name
        :type rail_name: str
        :param copy_project: Project name to copy.
        If not given, only empty folders are created, defaults to None
        :type copy_project: str or NoneType, optional
        '''

        if copy_project is None:
            folder = ProjectLevels(project_name, study_name, rail_name)
            self.levels = folder.levels
            self._create_folder_struct(0, [project_name])

            for path in self.paths:
                path.mkdir(parents=True, exist_ok=True)
            self.paths = []
        else:
            folders = ProjectLevels(copy_project, study_name, rail_name)
            self.levels = folders.levels
            self._create_folder_struct(0, [copy_project])
            src_paths = self.paths
            self.paths = []

            folders = ProjectLevels(project_name, study_name, rail_name)
            self.levels = folders.levels
            self._create_folder_struct(0, [project_name])
            dst_paths = self.paths
            self.paths = []

            for src_path, dst_path in zip(src_paths, dst_paths):
                _ = shutil.copytree(src_path, dst_path)
    
    def _create_folder_struct(self, idx_level, path):
        '''Recursively scan dictionaries to produce paths of the project.

        :param idx_level: Index level of the folder structure
        :type idx_level: int
        :param path: The current path at the corresponding idx_level
        :type path: str
        :raises IndexError: Raised when reaching to the last dictionary level
        and ending the recusion process
        '''

        try:
            if path[-1] in self.levels[idx_level]:
                for next_folder in self.levels[idx_level][path[-1]]:
                    self._create_folder_struct(idx_level + 1, path + [next_folder])
            else:
                raise IndexError
        except IndexError:
            self.paths.append(Path(self.root, *path))
            






