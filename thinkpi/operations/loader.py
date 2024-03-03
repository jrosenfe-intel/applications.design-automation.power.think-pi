import os
from copy import deepcopy
from collections import namedtuple
import re
import glob
from pathlib import Path

import numpy as np
import pandas as pd
import skrf as rf

from thinkpi.waveforms.primitives import Wave, WaveNet
from thinkpi.operations.calculations import GroupOps
from thinkpi import DataVector, logger

class Waveforms(GroupOps):
    '''Returns a :class:`operations.loader.Waveforms` class that is responsible
    for waveform group handeling.

    :param file_exts: Extensions of file formats in the form of ``*.ext``, defaults to ['*.txt', '*.csv', '*.inc', '*.s*p']
    :type file_exts: list[str], optional
    :return: Waveforms object
    :rtype: :class:`loader.Waveforms()` class
    '''

    def __init__(self, file_exts=['*.txt', '*.csv', '*.inc',
                                    '*.s*p', '*.tr*', '*.ac*',
                                    '*.xlsx']):
        
        super().__init__()
        self.file_exts = file_exts
        self.waves = {}
        self.path = ''

    def __repr__(self):

        all_wave_names = 'Waveform group\n'
        for idx, wave_name in enumerate(self.wave_names(verbose=False)):
            all_wave_names += f'\t[{idx}]\t{wave_name}\n'

        return all_wave_names

    def __add__(self, other):
        
        # Check for name collisions
        self_names = self.wave_names(verbose=False)
        for other_name in other.waves.keys():
            if other_name in self_names:
                new_name = f'{other_name}{Wave.wave_num}'
                Wave.wave_num += 1
                logger.warning(f'{other_name}\talready exists. '
                        f'Assigning a new name {new_name}')
                other.waves[new_name] = deepcopy(other.waves[other_name])
                other.waves[new_name].wave_name = new_name
                del other.waves[other_name]

        return self.group(self, other)

    def __getitem__(self, item_id):

        if isinstance(item_id, int):
            wave_names = list(self.waves.keys())
            return self.waves[wave_names[item_id]]
        elif isinstance(item_id, str):
            return self.waves[item_id]
        else:
            raise TypeError(f'Waveform indices must be integer or a string, not {type(item_id)}')
    
    def group(self, *wave_ids):
        '''Creates a new group of waveforms based on a selection from exisiting waveforms.

        :param *wave_ids: variable number of arguments indicating existing wave names and ranges
        :type *wave_ids: int, str, :class:`primitives.Wave()`, :class:`loader.Waveforms()` 
        :return: A new group of waveforms
        :rtype: :class:`loader.Waveforms()`
        '''

        other = deepcopy(self)
        other.waves = {}
        group_names = []
        group_clr = next(Wave.group_clr)
        
        for wave_id in wave_ids:
            if isinstance(wave_id, Waveforms):
                other.waves = {**other.waves, **deepcopy(wave_id.waves)}
                for name in other.waves.keys():
                    other.waves[name].group_clr = group_clr
            elif isinstance(wave_id, (Wave, WaveNet)):
                other.waves[wave_id.wave_name] = deepcopy(wave_id)
                other.waves[wave_id.wave_name].group_clr = group_clr
            else:
                group_names += self.port_selection(wave_id)
        
        for name in group_names:
            other.waves[name] = deepcopy(self.waves[name])
            other.waves[name].group_clr = group_clr

        return other

    def create_output_folders(self, folder_names=None):
        '''Creates output folders for Wave to organize outputs

        :param folder_names: Folder names to be created, defaults to None
        :type folder_names: list[str], optional
        '''

        folders = ['plots', 'reports', 'new_waveforms'] if folder_names is None else folder_names
        for folder in folders:
            if not os.path.isdir(os.path.join(self.path, folder)):
                os.mkdir(os.path.join(self.path, folder))

    def _load_touchstone(self, fname):

        net = rf.Network(fname)
        port_names = []
        TS_Info = namedtuple('TS_Info', 'generated_from sigrity_ver host_name')
        generated_from, sigrity_ver, host_name = None, None, None
        for comment in net.comments.split('\n'):
            if '::' in comment:
                port_names.append(comment.split('::')[0].strip())
            elif 'Generated from' in comment:
                generated_from = comment.split(': ')[1]
            elif 'Sigrity Suite Version' in comment:
                sigrity_ver = comment.split(':')[1].strip()
            elif 'Computer Host Name' in comment:
                host_name = comment.split(':')[1].strip()

        freq = deepcopy(net.f)
        z_mag = deepcopy(net.z_mag)
        for port_idx in range(net.z.shape[-1]):
            double_tab = '\t\t'
            try:
                wave_name = port_names[port_idx]
                if wave_name in self.waves:
                    logger.warning(f'\t\t--> {wave_name} already exists. '
                                    f'Assigning a new name ', end='')
                    wave_name = f'{wave_name}{Wave.wave_num}'
                    Wave.wave_num += 1
                    double_tab = ' '
            except IndexError:
                wave_name = f'Port{Wave.wave_num}'
                Wave.wave_num += 1
            logger.info(f'{double_tab}{wave_name}')

            wave = WaveNet(DataVector(x=freq, y=z_mag[:, port_idx, port_idx],
                            x_unit='Hz',
                            y_unit='Ohm',
                            wave_name=wave_name,
                            file_name=fname.split('\\')[-1],
                            path=self.path,
                            proc_hist=[]),
                            net,
                            TS_Info(generated_from=generated_from,
                                    sigrity_ver=sigrity_ver,
                                    host_name=host_name),
                            port_idx
                                    )
            self.waves[wave_name] = wave

    def _load_inc(self, fname):

        vec = []
        with open(fname, 'rt') as f:
            for line in f:
                split_line = line.split()
                if len(split_line) == 3 and split_line[0] == '+':
                    try:
                        vec.append([float(split_line[1]), float(split_line[2])])
                    except ValueError:
                        pass
            
        return pd.DataFrame(vec)

    def _load_excel(self, fname, sheets=None):

        data = pd.read_excel(fname, sheet_name=sheets)
        all_df = pd.DataFrame()
        for tab_name, df in data.items():
            df = df.add_suffix(f'_{tab_name}')
            all_df = pd.concat([all_df, df], axis=1)
        all_df = pd.DataFrame(np.vstack([all_df.columns, all_df]))

        ts_mode = 'alter' if len(data) > 1 else 'single'
        return ts_mode, all_df

    def __load_csv(self, fname, x_unit, y_unit, ts_score, fix):

        if fname.split('.')[-1][:2] == 'ac' or fname.split('.')[-1][:2] == 'tr':
            data = self._load_hspice_ascii(fname, fname.split('.')[-1][:2])
        elif fname.split('.')[-1] == 'xlsx':
            data = self._load_excel(fname)
        elif fname.split('.')[-1] == 'inc':
            data = self._load_inc(fname)
        else:
            data = pd.read_csv(fname, sep=None, engine='python', header=None, index_col=False)
        if data.empty:
            data.reset_index(level=0, inplace=True)
        header = None

        while True:
            try:
                vec = data.to_numpy(dtype=float)
                break
            except ValueError:
                header = data.iloc[0]
                data = data.drop(index=0).reset_index(drop=True)

        time_series = np.arange(0, vec.shape[0]*1e-6, 1e-6)
        
        no_timeseries = True
        file_name = fname.split('\\')[-1]
        for wave_idx in range(0, vec.shape[-1]):
            if np.all(np.isnan(vec[:, wave_idx])):
                continue

            # Detect if the current vector is a time series
            timeseries_diff = vec[1:, wave_idx] - vec[:-1, wave_idx]
            # Remove any remaining NaN values
            timeseries_diff = timeseries_diff[~np.isnan(timeseries_diff)]

            timeseries_score = np.sum(timeseries_diff < 0)/len(timeseries_diff)
            raw_timeseries = deepcopy(time_series)
            if timeseries_score < ts_score:
                time_series = vec[:, wave_idx]
                # Remove any remaining NaN values
                time_series = time_series[~np.isnan(time_series)]
                no_timeseries = False
                continue
                
            if header is None:
                wave_name = f'Wave{Wave.wave_num}'
                Wave.wave_num += 1
            else:
                wave_name = header[wave_idx].strip()

            if wave_name in self.waves:
                logger.warning(f'\t\t--> {wave_name} already exists. Assigning a new name ', end='')
                wave_name = f'{wave_name}{Wave.wave_num}'
                logger.info(f'{wave_name}')
                Wave.wave_num += 1
            else:
                logger.info(f'\t\t{wave_name}')
            data = vec[:, wave_idx]
            # Remove any remaining NaN values
            data = data[~np.isnan(data)]

            # Fix time series integrity if needed
            if fix:
                msg = ''
                end_with = ''
                while True:
                    idx = np.where((time_series[1:] - time_series[:-1]) <= 0)[0]
                    if idx.size > 0:
                        idx += 1
                        time_series = np.delete(time_series, idx)
                        data = np.delete(data, idx)
                        msg = f'\t\t--> Time precision violations are found and fixed in {wave_name}'
                        end_with = '\n'
                    else:
                        logger.warning(msg, end=end_with)
                        break
    
            self.waves[wave_name] = Wave(DataVector(x=time_series, y=data,
                                                    x_unit=x_unit,
                                                    y_unit=y_unit,
                                                    wave_name=wave_name,
                                                    file_name=file_name,
                                                    path=self.path,
                                                    proc_hist=[]))
            time_series = raw_timeseries

        if no_timeseries:
            logger.warning(f'\t\t--> Time vector was not detected in {fname}.'
                    f'\n\t\t    Application has assigned an arbitrary time vector.'
                    f'\n\t\t    If time vector is expected in the data try to '
                    f'increase the value of ts_score from its current value of {ts_score}.')

    def _load_csv(self, fname, x_unit, y_unit, ts_mode, fix, sheets=None, add_fname=False):

        if fname.split('.')[-1][:2] == 'ac' or fname.split('.')[-1][:2] == 'tr':
            data = self._load_hspice_ascii(fname, fname.split('.')[-1][:2])
        elif fname.split('.')[-1] == 'xlsx':
            ts_mode, data = self._load_excel(fname, sheets)
        elif fname.split('.')[-1] == 'inc':
            data = self._load_inc(fname)
        else:
            data = pd.read_csv(fname, sep=None, engine='python', header=None, index_col=False)
        if data.empty:
            data.reset_index(level=0, inplace=True)
        header = None

        while True:
            try:
                vec = data.to_numpy(dtype=float)
                break
            except ValueError:
                header = data.iloc[0]
                data = data.drop(index=0).reset_index(drop=True)

        time_series = np.arange(0, vec.shape[0]*1e-6, 1e-6)
        file_name = os.path.basename(fname)
        msg = ''
        end_with = ''
        for wave_idx in range(0, vec.shape[-1]):
            if np.all(np.isnan(vec[:, wave_idx])):
                continue

            if ((wave_idx == 0 and ts_mode == 'single')
                or (wave_idx % 2 == 0 and ts_mode == 'alter')):
                time_series = vec[:, wave_idx]
                # Remove any remaining NaN values
                time_series = time_series[~np.isnan(time_series)]
                continue
                
            if header is None:
                wave_name = f'Wave{Wave.wave_num}'
                Wave.wave_num += 1
            else:
                wave_name = header[wave_idx].strip()
            if add_fname:
                wave_name = f'{wave_name}_{file_name.split(".")[0]}'

            if wave_name in self.waves:
                prev_name = wave_name
                wave_name = f'{wave_name}{Wave.wave_num}'
                logger.warning(f'\t\t{prev_name} already exists. Assigning a new name {wave_name}.')
                Wave.wave_num += 1
            else:
                logger.info(f'\t\t{wave_name}')

            data = vec[:, wave_idx]
            # Remove any remaining NaN values
            data = data[~np.isnan(data)]

            # Check for precision errors in the data
            idx = np.where((time_series[1:] - time_series[:-1]) <= 0)[0]
            if idx.size > 0:
                logger.warning(f'\t\tTime precision violations are found. '
                               f'To remove these violations set fix=True.')
            # Fix time series integrity if needed
            if fix:
                while True:
                    idx = np.where((time_series[1:] - time_series[:-1]) <= 0)[0]
                    if idx.size > 0:
                        idx += 1
                        time_series = np.delete(time_series, idx)
                        data = np.delete(data, idx)
                        msg = f'\tTime precision violations are found and fixed'
                        end_with = '\n'
                    else:
                        break
    
            f'{wave_name}_{file_name.split(".")[0]}' if add_fname else wave_name
            self.waves[wave_name] = Wave(DataVector(x=time_series, y=data,
                                                    x_unit=x_unit,
                                                    y_unit=y_unit,
                                                    wave_name=wave_name,
                                                    file_name=file_name,
                                                    path=self.path,
                                                    proc_hist=[]))
        
        logger.warning(msg, end=end_with)

    def _load_hspice_ascii(self, fname, sim_type):

        with open(fname, 'rt') as f:
            block = f.read()
        n_digits = len(re.search(r'E[+,-][0-9]*\n', block).group().strip()[2:])
        block = block.replace('\n', '')
        block = block.split()

        if sim_type == 'ac':
            names_start, names_end = block.index('HERTZ') + 1, block.index('$&%#')
        if sim_type == 'tr':
            names_start, names_end = block.index('TIME') + 1, block.index('$&%#')

        wave_names = []
        for name in block[names_start:names_end]:
            wave_names.append(name)

        block_length = len(wave_names) + 1
        data = re.findall(r'-?[0-9]*\.[0-9]*E[+,-][0-9]' + f'{{{n_digits}}}', block[-1])
        data = np.array(data, dtype=float)

        block_height = int(len(data)/block_length)
        data = data[:block_height*block_length]
        data = data.reshape((block_height, block_length))

        return pd.concat([pd.DataFrame([['x_axis'] + wave_names]),
                            pd.DataFrame(data)]).reset_index(drop = True)

    def load_waves(self, path=None, x_unit='sec', y_unit='V',
                    ts_mode='single', fix=True, sheets=None, add_fname=False):
        '''Imports and loads waveforms, creating a group.

        :param path: A path to the waveforms to be uploaded, defaults to None
        :type path: str, optional
        :param x_unit: The desired units of the X-axis, defaults to 'sec'
        :type x_unit: str, optional
        :param y_unit: The desired units of the Y-axis, defaults to 'V'
        :type y_unit: str, optional
        :param ts_score: A threshold to determine if the vector is a time/frequency vector or a data vector, defaults to 0.1
        :type ts_score: float, optional
        '''

        if path is None:
            self.path = ''
        else:
            if os.path.isdir(path):
                self.path = path
                file_name = None
            else:
                self.path, file_name = os.path.dirname(path), os.path.basename(path)
            logger.add(Path(self.path) / Path('thinkpi.log'), mode='w',
                        format="[{time:DD-MM-YYYY HH:mm:ss}] {message}",
                        level='INFO')

        if file_name:
            load_files = [path]
        else:
            load_files = []
            for file_ext in self.file_exts:
                load_files += glob.glob(os.path.join(self.path, file_ext))
        
        # Create sub-folders (if don't exist) for application outputs
        self.create_output_folders()
        logger.info(f'Reading data from:')
        for fname in load_files:
            logger.info(f'\t{fname}')

            # Identifying touchstone file
            ext = fname.split('.')[-1]
            if ext[0].lower() == 's' and ext[-1].lower() == 'p' and ext[1:-1].isdecimal():
                self._load_touchstone(fname)
            else:
                self._load_csv(fname, x_unit, y_unit, ts_mode, fix, sheets, add_fname) # This method loads or the other types

    def append_wave(self, waves):
        '''Append Wave objects (waveforms) to a group.

        :param waves: Waves to be added to a specific group
        :type waves: :class:`primitives.Wave()`, list[:class:`primitives.Wave()`]
        '''

        if isinstance(waves, Wave):
            waves = [waves]
        for wave in waves:
            if wave.wave_name in self.waves and wave is not self.waves[wave.wave_name]:
                wave.wave_name = f'{wave.wave_name}{Wave.wave_num}'
                self.waves[wave.wave_name] = wave
                Wave.wave_num += 1
            else:
                self.waves[wave.wave_name] = wave

    def remove_wave(self, wave_names):
        '''Remove waveforms from a group.

        :param wave_names: Names of the waveforms to remove
        :type wave_names: str, list[str]
        '''

        if isinstance(wave_names, str):
            wave_names = [wave_names]
        for wave_name in wave_names:
            del self.waves[wave_name]

    def clear_waves(self):
        '''Remove all the waves in the group.
        '''

        self.waves = {}

    def wave_names(self, verbose=True):
        '''Prints or returns wave names in the group. A handy shortcut is just to type the group name to print the waveform names.

        :param verbose: If True prints the names on the screen, otherwise return a list of names, defaults to True
        :type verbose: bool, optional
        :return: If verbose is False a list of waveform names is returned
        :rtype: list[str]
        '''

        names = []
        for name in self.waves.keys():
            if verbose:
                print(name)
            names.append(name)
        if not verbose:
            return names

    def change_names(self, new_names):
        '''Modify waveform names.

        :param new_names: An Excel file or a list of current and modified waveform names
        :type new_names: str, list[tuple]
        '''

        if isinstance(new_names, str):
            name_map = pd.read_excel(new_names, header=None)
            new_names = [(prev_name, new_name) for prev_name, new_name in zip(name_map[0], name_map[1])]
        for prev_name, new_name in new_names:
            self.waves[new_name] = self.waves.pop(prev_name)
            self.waves[new_name].wave_name = new_name
            self.waves[new_name].prev_wave_name = prev_name

    def restore_names(self):
        '''Restore all the old waveform names that were modified.
        '''

        for wave_name, wave in self.waves.items():
            if wave.prev_wave_name is not None:
                logger.info(f'{wave.wave_name} --> {wave.prev_wave_name}')
                self.waves[wave.prev_wave_name] = self.waves.pop(wave_name)
                self.waves[wave.prev_wave_name].wave_name = wave.prev_wave_name
                self.waves[wave.prev_wave_name].prev_wave_name = None
            
    def prev_names(self, verbose=True):
        '''Prints or returns previous modified waveform names.

        :param verbose: If True prints the previous names on the screen, otherwise returns a list of previous names, defaults to True
        :type verbose: bool, optional
        :return: If verbose is False a list of previous waveform names is returned
        :rtype: list[str]
        '''

        prev_names = []
        for wave in self.waves.values():
            if verbose:
                if wave.prev_wave_name is not None:
                    logger.info(f'{wave.prev_wave_name} --> {wave.wave_name}')
            else:
                prev_names.append(wave.prev_wave_name)

        if not verbose:
            return prev_names

    def cports(self, i, j):
        '''Prints the names of the (i, j) ports of a group of s-parameter waveforms.

        :param i: The ith port, defaults to None
        :type i: int, optional
        :param j: The jth port, defaults to None
        :type j: int, optional
        '''

        i_name, j_name = None, None
        for wave_name, wave in self.waves.items():
            if isinstance(wave, WaveNet):
                if i == wave.port_num:
                    i_name = wave_name
                if j == wave.port_num:
                    j_name = wave_name
        
        logger.info(f'({i}, {j}) <--> ({i_name}, {j_name})')