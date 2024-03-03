import os
from itertools import cycle
from collections import namedtuple

from scipy.interpolate import interp1d
import numpy as np
from bokeh.palettes import Category20, Category10
from bokeh.io import output_file, show
from bokeh.layouts import column

import thinkpi.operations.calculations as calc
from thinkpi import DataVector

class Wave(calc.Ops):

    wave_num = 0
    group_clr = cycle(Category10[10])

    def __init__(self, data_source):
        
        super().__init__()
        self.data = None
        self.x_unit = None
        self.y_unit = None
        self.wave_name = None
        self.prev_wave_name = None
        self.file_name = None
        self.path = None
        self.history = []
        self.results = dict()
        self.group_clr = next(Wave.group_clr)
        self.reg(data_source)

    def __repr__(self):

        return (f'Waveform name: {self.wave_name}\nX-axis unit: {self.x_unit}'
                f'\nY-axis unit: {self.y_unit}\nFile name: {self.file_name}\nPath: {self.path}\n')
        
    def reg(self, data_source):

        Data = namedtuple('Data', 'x y')
        self.data = Data(x=data_source.x, y=data_source.y)
        self.x_unit = data_source.x_unit
        self.y_unit = data_source.y_unit
        self.file_name = data_source.file_name
        self.path = data_source.path
        self.wave_name = data_source.wave_name
        self.history = data_source.proc_hist

    def _perform_op(self, other, op_type, right_op=False):

        ops = {'add': lambda y1, y2 : y1 + y2,
               'sub': lambda y1, y2 : y2 - y1 if right_op else y1 - y2,
               'mul': lambda y1, y2: y1 * y2,
               'div': lambda y1, y2: y2 / y1 if right_op else y1 / y2}

        if not isinstance(self, Wave):
            self = Wave(DataVector(x=other.data.x, y=np.array([self]*len(other.data.x)),
                                   x_unit=other.x_unit,
                                   y_unit=other.y_unit,
                                   wave_name=None,
                                   file_name=None,
                                   path=other.path,
                                   proc_hist=[]
                                  ))

        if not isinstance(other, Wave):
            other = Wave(DataVector(x=self.data.x, y=np.array([other]*len(self.data.x)),
                                   x_unit=self.x_unit,
                                   y_unit=self.y_unit,
                                   wave_name=None,
                                   file_name=None,
                                   path=self.path,
                                   proc_hist=[]
                                  ))
        if (self.y_unit != other.y_unit and (op_type == 'add' or op_type == 'sub')) or self.x_unit != other.x_unit:
            raise ValueError(f'Cannot perform {op_type} operation between '
                            f'waveformes with different units:\nX-axis '
                            f'--> {self.x_unit} and {other.x_unit}, Y-axis '
                            f'--> {self.y_unit} and {other.y_unit}')

        # match time points for the two waveforms to correctly perform the operation
        self_inter = interp1d(self.data.x, self.data.y, bounds_error=False, fill_value=(0, 0))
        other_inter = interp1d(other.data.x, other.data.y, bounds_error=False, fill_value=(0, 0))
        all_xpoints = np.array(list(set(np.concatenate((self.data.x, other.data.x), axis=None))))
        all_xpoints.sort()
        
        Wave.wave_num += 1
        return Wave(DataVector(x=all_xpoints,
                                y=ops[op_type](self_inter(all_xpoints), other_inter(all_xpoints)),
                                x_unit = self.x_unit,
                                y_unit=self.y_unit if self.y_unit == other.y_unit else self.y_unit + other.y_unit,
                                wave_name=f'Wave{Wave.wave_num-1}',
                                file_name=self.file_name,
                                path=self.path,
                                proc_hist=[op_type]
                              )
                    )

    def __add__(self, other):

        return self._perform_op(other, 'add')
    
    def __radd__(self, other):

        return self.__add__(other)

    def __sub__(self, other):

        return self._perform_op(other, 'sub')
    
    def __rsub__(self, other):

        return self._perform_op(other, 'sub', right_op=True)

    def __mul__(self, other):

        return self._perform_op(other, 'mul')
    
    def __rmul__(self, other):

        return self.__mul__(other)

    def __truediv__(self, other):

        return self._perform_op(other, 'div')
    
    def __rtruediv__(self, other):

        return self._perform_op(other, 'div', right_op=True)


class WaveNet(Wave):

    def __init__(self, data_source, net, ts_info, port_num):

        super().__init__(data_source)
        self.net = net
        self.ts_info = ts_info
        self.port_num = port_num

    def net_attr(self, net_type='z', i=None, j=None):

        '''
        Props = namedtuple('Props', 'mag phase re im unit deg_wrap y_mag_axis')
        nets = {'z': Props(mag=self.net.z_mag, phase=self.net.z_deg_unwrap,
                            re=self.net.z_re, im=self.net.z_im,
                            unit='Ohm', deg_wrap=360, y_mag_axis='log'),
                's': Props(mag=self.net.s_mag, phase=self.net.s_deg_unwrap,
                            re=self.net.s_re, im=self.net.s_im,
                            unit='', deg_wrap=0, y_mag_axis='linear'),
                'y': Props(mag=self.net.y_mag, phase=self.net.y_deg_unwrap,
                            re=self.net.y_re, im=self.net.y_im,
                            unit='S', deg_wrap=0, y_mag_axis='linear')
                }
        '''
        Props = namedtuple('Props', 'mag phase re im unit y_mag_axis')
        nets = {'z': Props(mag=self.net.z_mag, phase=self.net.z_deg_unwrap,
                            re=self.net.z_re, im=self.net.z_im,
                            unit='Ohm', y_mag_axis='log'),
                's': Props(mag=self.net.s_mag, phase=self.net.s_deg_unwrap,
                            re=self.net.s_re, im=self.net.s_im,
                            unit='', y_mag_axis='linear'),
                'y': Props(mag=self.net.y_mag, phase=self.net.y_deg_unwrap,
                            re=self.net.y_re, im=self.net.y_im,
                            unit='S', y_mag_axis='linear')
                }

        cwaves = {}
        i = self.port_num if i is None else i
        j = self.port_num if j is None else j

        cwaves['mag'] = (WaveNet(DataVector(x=self.net.f,
                                            y=nets[net_type].mag[:, i, j],
                                            x_unit=self.x_unit,
                                            y_unit=nets[net_type].unit,
                                            wave_name=self.wave_name,
                                            file_name=self.file_name,
                                            path=self.path,
                                            proc_hist=self.history),
                                            net=self.net, ts_info=self.ts_info,
                                            port_num = self.port_num,
                                ),
                        nets[net_type].y_mag_axis)
        
        cwaves['phase'] = (WaveNet(DataVector(x=self.net.f[:],
                                                y=nets[net_type].phase[:, i, j],
                                                x_unit=self.x_unit,
                                                y_unit='Deg',
                                                wave_name=self.wave_name,
                                                file_name=self.file_name,
                                                path=self.path,
                                                proc_hist=self.history),
                                                net=self.net, ts_info=self.ts_info,
                                                port_num = self.port_num,
                                ),
                            'linear')

        cwaves['re'] = (WaveNet(DataVector(x=self.net.f,
                                            y=nets[net_type].re[:, i, j],
                                            x_unit=self.x_unit,
                                            y_unit=nets[net_type].unit,
                                            wave_name=self.wave_name,
                                            file_name=self.file_name,
                                            path=self.path,
                                            proc_hist=self.history),
                                            net=self.net, ts_info=self.ts_info,
                                            port_num = self.port_num,
                                ),
                        'linear')

        cwaves['im'] = (WaveNet(DataVector(x=self.net.f,
                                            y=nets[net_type].im[:, i, j],
                                            x_unit=self.x_unit,
                                            y_unit=nets[net_type].unit,
                                            wave_name=self.wave_name,
                                            file_name=self.file_name,
                                            path=self.path,
                                            proc_hist=self.history),
                                            net=self.net, ts_info=self.ts_info,
                                            port_num = self.port_num,
                                ),
                        'linear')

        # Copy group color
        for net_type in cwaves.copy().keys():
            cwaves[net_type][0].group_clr=self.group_clr

        return cwaves

    def plot(self, wave_name=None, x_scale='M', y_scale='', xaxis_type='log',
             clr=None, net_type='z', i=None, j=None):

        net_type = net_type.lower()
        if wave_name is None:
            wave_name = self.wave_name
            for invalid_char in ['/', '\\', '(', ')', '<', '>']:
                wave_name = wave_name.replace(invalid_char, '')
            wave_name = wave_name.split(' ')[0]

        output_file(os.path.join(self.path, 'plots', f'{wave_name}.html'))

        clr_cycle = cycle(Category20[20]) if clr is None else cycle([clr])
        all_plots = []
        if (i is None and j is None) or (self.port_num == i and self.port_num == j):
            port_name = self.wave_name
        else:
            port_name = ''
        i = self.port_num if i is None else i
        j = self.port_num if j is None else j

        for net_attr, cwaves in self.net_attr(net_type, i, j).items():
            all_plots.append(
                self.plt.single_plot(cwaves[0], x_scale=x_scale, y_scale=y_scale,
                                    xaxis_type=xaxis_type, yaxis_type=cwaves[1],
                                    clr=next(clr_cycle),
                                    suffix=f'{port_name} {net_attr.capitalize()} '
                                            f'{net_type.upper()}[{i}, {j}]',
                                    y_title=f'{net_attr.capitalize()} {net_type.upper()}',
                                    stretch_mode=False
                                    )
                            )
            
        show(column(all_plots))

    def sparam_props(self):

        props = {'reciprocal': self.net.is_reciprocal, 'symmetric': self.net.is_symmetric,
                    'passive': self.net.is_passive, 'lossless': self.net.is_lossless}

        print(self.wave_name)
        for prop, prop_func in props.items():
            try:
                print(f'\t{prop.capitalize()}:\t{prop_func()}')
            except ValueError:
                pass
