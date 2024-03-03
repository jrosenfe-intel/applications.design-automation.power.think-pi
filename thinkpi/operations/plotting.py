from collections import namedtuple
from itertools import cycle

import numpy as np
from scipy import signal

from bokeh.models import CrosshairTool, Arrow, NormalHead, Label, Range1d
from bokeh.models import BasicTicker, ColorBar, LinearColorMapper
from bokeh.plotting import ColumnDataSource, figure
from bokeh.palettes import Category20, RdYlGn
from bokeh.transform import transform

from thinkpi import logger


class Plotter:

    def __init__(self):

        self.scales = {'a': 1e-18, 'f': 1e-15, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6,
                       'm': 1e-3, '': 1, 'k': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12}

    def setup_plot(self, title, data, x_scale, y_scale, stretch_mode, xaxis_type, yaxis_type):

        if 's' in data.x_unit.lower():
            xaxis_name = 'Time'
        elif 'h' in data.x_unit.lower():
            xaxis_name = 'Frequency'
        else:
            xaxis_name = 'X axis'

        # Check if there is a zero frequency value and if so set it to 0.01 Hz for log plotting
        if data.x[0] == 0 and xaxis_type == 'log':
            data.x[0] = 0.01
        if data.y[0] == 0 and yaxis_type == 'log':
            data.y[0] = 0.01
        
        TOOLTIPS = [
            (f"({xaxis_name}, {title.y_title})",
                f"($x {x_scale}{data.x_unit}, $y {y_scale}{data.y_unit})"
            )
        ]

        if stretch_mode:
            p = figure(width=1500, height=600,
                        title=f'{title.file_name}:{title.wave_name} {title.suffix}',
                        tooltips=TOOLTIPS, sizing_mode='stretch_both',
                        x_axis_type=xaxis_type, y_axis_type=yaxis_type, output_backend="webgl")
        else:
            p = figure(width=1500, height=600,
                       title=f'{title.file_name}: {title.wave_name} {title.suffix}',
                       tooltips=TOOLTIPS, x_axis_type=xaxis_type, y_axis_type=yaxis_type, output_backend="webgl")
        
        p.xaxis.axis_label = f'{xaxis_name} [{x_scale}{data.x_unit}]'
        p.yaxis.axis_label = f'{title.y_title} [{y_scale}{data.y_unit}]'
        source = ColumnDataSource(data=dict(
                                            x=data.x/self.scales[x_scale],
                                            y=data.y/self.scales[y_scale]
                                            )
                                 )
        p.line('x', 'y', source=source, alpha=1,
                color=data.clr, line_width=2)
        p.add_tools(CrosshairTool())

        return p

    def plot_measurements(self, p, results, x_scale, y_scale, x_unit, y_unit):

        xs = self.scales[x_scale]
        ys = self.scales[y_scale]

        # Plot markers on droops and overshoots 
        for point in ['min_1st_V', 'min_2nd_V', 'min_3rd_V',
                        'max_1st_V', 'max_2nd_V', 'max_3rd_V']:
            try:
                p.circle_x(x=results[point][0]/xs, y=results[point][1]/ys,
                           size=10, color="#DD1C77", fill_alpha=0.2)
                p.add_layout(Label(x=results[point][0]/xs, y=results[point][1]/ys,
                                    text=f'({results[point][0]/xs:.3f}{x_scale}{x_unit}, '
                                        f'{results[point][1]/ys:.3f}{y_scale}{y_unit})',
                            x_offset=10, y_offset=0))
            except KeyError:
                pass
        
        # Plot peak to peak measurement
        if 'pk2pk' in results:
            x_midpoint = (results['min'][0] + results['max'][0])/2
            y_midpoint = (results['min'][1] + results['max'][1])/2
            p.line([results['min'][0]/xs, x_midpoint/xs],
                    [results['min'][1]/ys, results['min'][1]/ys],
                    color='black', line_dash='dashed')
            p.line([x_midpoint/xs, results['max'][0]/xs],
                    [results['max'][1]/ys, results['max'][1]/ys],
                    color='black', line_dash='dashed')
            p.add_layout(Arrow(end=NormalHead(line_width=1, size=10),
                               start=NormalHead(line_width=1, size=10),
                               x_start=x_midpoint/xs, y_start=results['min'][1]/ys,
                               x_end=x_midpoint/xs, y_end=results['max'][1]/ys
                              )
                        )
            p.add_layout(Label(x=x_midpoint/xs, y=y_midpoint/ys,
                               text=f'{results["pk2pk"][1]*1000:.3f} m{y_unit}',
                         x_offset=5, y_offset=0))

        return p

    def single_plot(self, other, x_scale, y_scale, xaxis_type, yaxis_type,
                    clr, suffix='', y_title='Amplitude', stretch_mode=False):

        # Check if waveform is complex
        if np.iscomplexobj(other.data.y):
            logger.info(f'Waveform {other.wave_name} is a complex waveform. Plotting magnitude.')
            other = other.abs()

        Title = namedtuple('Title', 'file_name wave_name suffix y_title')
        Data = namedtuple('Data', 'x y x_unit y_unit clr')
        p = self.setup_plot(Title(file_name=other.file_name,
                                  wave_name=other.wave_name if not suffix else '',
                                  suffix=suffix,
                                  y_title=y_title
                                  ),
                            Data(x=other.data.x,
                                    y=other.data.y,
                                    x_unit = other.x_unit,
                                    y_unit = other.y_unit,
                                    clr=clr
                                ),
                            x_scale, y_scale, stretch_mode,
                            xaxis_type, yaxis_type
                            )
        return self.plot_measurements(p, other.results, x_scale, y_scale,
                                      other.x_unit, other.y_unit)

    def plot_heatmap(self, data, x_range, y_range, unit, title=''):

        y_axis, x_axis, map_value = data.columns
        TOOLTIPS = [('', f"@{y_axis} to @{x_axis}"),
            (map_value, f"@{map_value} {unit}")
        ]
        mapper = LinearColorMapper(palette=RdYlGn[11],
                                    low=data[map_value].min(),
                                    high=data[map_value].max()
                                    )

        p = figure(width=1500, height=27*len(y_range)+446,
                    title=title,
                    x_range=x_range, y_range=y_range,
                    tooltips=TOOLTIPS, x_axis_location="above"
                    )

        p.rect(x=x_axis, y=y_axis, width=1, height=1,
                source=ColumnDataSource(data),
                line_color=None,
                fill_color=transform(map_value, mapper)
                )

        color_bar = ColorBar(color_mapper=mapper,
                                ticker=BasicTicker(desired_num_ticks=len(RdYlGn[11]))
                            )

        p.add_layout(color_bar, 'right')
        p.add_tools(CrosshairTool())

        p.axis.axis_line_color = None
        p.axis.major_tick_line_color = None
        p.axis.major_label_standoff = 0
        p.xaxis.major_label_orientation = 1.0

        return p

    def plot_overlay(self, waves, title='', yaxis_title='', x_scale='u', y_scale='',
                     xaxis_type='linear', yaxis_type='linear',
                     stretch_mode='stretch_both', clr=None):

        # Find all units for both X and Y axis
        x_units = set()
        y_units = set()
        for wave in waves:
            x_units.add(wave.x_unit)
            y_units.add(wave.y_unit)

        x_unit, y_unit = '', ''
        for unit in x_units:
            x_unit += f'{x_scale}{unit}, '
        for unit in y_units:
            y_unit += f'{y_scale}{unit}, '

        TOOLTIPS = [('Name', "$name"), ("(X-axis, Y-axis)", "($x, $y)")]
        clr_cycle = cycle(Category20[20]) if clr is None else cycle([clr])
        p = figure(width=int(1500), height=int(600), tooltips=TOOLTIPS,
                    title=title,
                    sizing_mode=stretch_mode, x_axis_type=xaxis_type,
                    y_axis_type=yaxis_type)
        p.xaxis.axis_label = f'[{x_unit[:-2]}]'
        p.yaxis.axis_label = f'{yaxis_title} [{y_unit[:-2]}]'

        for wave in waves:
            # Check if there is a zero frequency value
            # and if so set it to 0.1 for log plotting
            if wave.data.x[0] == 0 and xaxis_type == 'log':
                wave.data.x[0] = 0.01
            if wave.data.y[0] == 0 and yaxis_type == 'log':
                wave.data.y[0] = 0.01
                
            source = ColumnDataSource(data=dict(x=wave.data.x/self.scales[x_scale],
                                      y=wave.data.y/self.scales[y_scale]),
                                      )
            p.line('x', 'y', source=source, alpha=1,
                    color=wave.group_clr if clr == 'group' else next(clr_cycle),
                    line_width=2, legend_label=wave.wave_name, name=wave.wave_name)
    
        p.legend.location = 'top_left'
        p.legend.click_policy = 'hide'
        p.add_tools(CrosshairTool())
        return p

    def plot_filter_response(self, other, xaxis_type='log',
                             yaxis_type='linear'):

        TOOLTIPS = [("(frequency, amplitude)", f"($x GHz, $y dB)")]
        clr_cycle = cycle(Category20[20])
        p = figure(tooltips=TOOLTIPS, sizing_mode='stretch_both',
                   title=f'{other.filter_type} | Order: {other.order} | '
                         f'Cutoff freq.: {other.cutoff_freq} [Hz] | '
                         f'Sampling: {1/other.fs} [sec]',
                   x_axis_type=xaxis_type, y_axis_type=yaxis_type)
        p.xaxis.axis_label = 'Frequency [GHz]'
        p.yaxis.axis_label = f'Transfer function [dB]'
        p.x_range = Range1d(0, 1)

        for filter_name, filter_func in other.filter_types.items():
            try:
                w, h = signal.sosfreqz(filter_func(), fs=other.fs, worN=2**12)
                db = 20*np.log10(np.maximum(np.abs(h), 1e-5))
                source = ColumnDataSource(data=dict(x=w*1e-9, y=db))
                p.line('x', 'y', source=source, alpha=1, color=next(clr_cycle),
                        line_width=2, legend_label=filter_name)
            except ValueError:
                pass

        p.legend.location = 'top_right'
        p.legend.click_policy = 'hide'
        p.add_tools(CrosshairTool())
        
        return p
