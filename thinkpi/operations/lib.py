import shutil
import json
from pathlib import Path


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
            






