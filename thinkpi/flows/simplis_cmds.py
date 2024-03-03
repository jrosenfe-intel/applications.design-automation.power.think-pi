from pathlib import Path

from thinkpi.config import thinkpi_conf as cfg

class SimplisCommands:

    def __init__(self):

        pass

    def spice_to_simplis(self, fname, x=0, y=0, orient=0):

        return f'{cfg.SIMPLIS_PARSER} {fname} {x} {y} {orient}'
    
    def place_symbol(self, ckt_name, x, y, orient):

        return f'inst /loc {x} {y} {orient} {{{ckt_name}}}'
    
    def get_pin_locs(self, ref_id):

        return f"let start_locs = GetInstancePinLocs('ref', '{ref_id}', 'absolute')"
    
    def draw_horiz_wire(self, idx, length):

        return (f"wire /loc {{start_locs[{idx}]}} {{start_locs[{idx + 1}]}} "
                f"{{start_locs[{idx}] + {length}}} {{start_locs[{idx + 1}]}}"
            )
    
    def draw_vert_wire(self, idx, length):

        return (f"wire /loc {{start_locs[{idx}]}} {{start_locs[{idx + 1}]}} "
                f"{{start_locs[{idx}]}} {{start_locs[{idx + 1}] + {length}}}"
            )
    
    def draw_horiz_term(self, idx, length, orient, term_name):

        return (f'inst term /centre /loc {{start_locs[{idx}] + {length}}} '
                f'{{start_locs[{idx + 1}]}} {{{orient}}} value {term_name}'
            )
    
    def draw_vert_term(self, idx, length, orient, term_name):

        return (f'inst term /centre /loc {{start_locs[{idx}]}} '
                f'{{start_locs[{idx + 1}] + {length}}} {{{orient}}} value {term_name}'
            )
    
    def draw_term(self, x, y, orient, term_name):

        return f'inst term /centre /loc {{{x}}} {{{y}}} {{{orient}}} value {term_name}'
    
    def draw_wire(self, xstart, ystart, xend, yend):

        return f'wire /loc {{{xstart}}} {{{ystart}}} {{{xend}}} {{{yend}}}'
    
    def draw_gnd(self, x, y, orient):

        return f'inst gnd /centre /loc {{{x}}} {{{y}}} {{{orient}}}'
    
    def new_schem(self, fname):

        return f"NewSchem /simulator SIMPLIS {{'{Path(fname).stem}'}}"
    
    def save_as(self, fname):

        return f"SaveAs /force {{'{fname}'}}"
    
    def close_sch(self):

        return 'CloseSchem'
    
    def ncaps_prop(self, ref_id, mul):

        return '\n'.join([f'select /prop ref {ref_id}',
                          f'prop NCAPS "NCAPS={mul}"',
                          'unselect'])
    
    def vdc(self, voltage, orient, x=None, y=None):

        if x is None or y is None:
            return '\n'.join([f'inst /select dc_source /loc %s %s {orient}',
                              f'prop VALUE {voltage}',
                              'unselect'])
        else:
            return '\n'.join([f'inst /select dc_source /loc {x} {y} {orient}',
                              f'prop VALUE {voltage}',
                              'unselect'])
        
    def vac(self, mag_phase, orient, x=None, y=None):

        mag_phase = mag_phase.split()
        if x is None or y is None:
            return '\n'.join([f'inst /select ac_source /loc %s %s {orient}',
                              f'prop VALUE "AC {mag_phase[0]} {mag_phase[1]}"',
                              'unselect'])
        else:
            return '\n'.join([f'inst /select ac_source /loc {x} {y} {orient}',
                              f'prop VALUE "AC {mag_phase[0]} {mag_phase[1]}"',
                              'unselect'])
    
    def idc(self, current, orient, x=None, y=None):

        if x is None or y is None:
            return '\n'.join([f'inst /select dc_isource /loc %s %s {orient}',
                              f'prop VALUE {current}',
                              'unselect'])
        else:
            return '\n'.join([f'inst /select dc_isource /loc {x} {y} {orient}',
                              f'prop VALUE {current}',
                              'unselect'])
        
    def ipwl_file(self, fname, orient, x=None, y=None):

        if x is None or y is None:
            return '\n'.join([f'inst /select file_defined_pwl_current_source /loc %s %s {orient}',
                              f'prop FILE {fname}', 'prop PERIODIC 1', 'unselect'])
        else:
            return '\n'.join([f'inst /select file_defined_pwl_current_source /loc {x} {y} {orient}',
                              f'prop FILE {fname}', 'prop PERIODIC 1', 'unselect'])
        
    def ipwl(self, pairs, orient, x=None, y=None):

        pairs = pairs.split()
        it = iter(pairs)
        pairs_str = [f'"NSEG={int(len(pairs)/2 - 1)}']
        for idx, single in enumerate(it):
            pairs_str.append(f'X{idx}={single} Y{idx}={next(it)}')
        pairs_str = ' '.join(pairs_str) + '"'

        if x is None or y is None:
            return '\n'.join([f'inst /select ipwl /loc %s %s {orient}',
                              f'prop VALUE {pairs_str}', 'unselect'])
        else:
            return '\n'.join([f'inst /select ipwl /loc {x} {y} {orient}',
                              f'prop VALUE {pairs_str}', 'unselect'])
        
    def iprobe(self, probe_name, orient, x=None, y=None):

        if x is None or y is None:
            return '\n'.join([f'inst /select probei_new /loc %s %s {orient}',
                                f'prop VALUE "curvelabel={probe_name}"',
                                f'prop label "{probe_name}"',
                                'unselect'])
        else:
            return '\n'.join([f'inst /select probei_new /loc {x} {y} {orient}',
                                f'prop VALUE "curvelabel={probe_name}"',
                                f'prop label "{probe_name}"',
                                'unselect'])
        
    def vprobe(self, probe_name, orient, x=None, y=None):

        if x is None or y is None:
            return '\n'.join([f'inst /select probev_new /loc %s %s {orient}',
                                f'prop VALUE "curvelabel={probe_name}"',
                                f'prop LABEL "{probe_name}"',
                                'unselect'])
        else:
            return '\n'.join([f'inst /select probev_new /loc {x} {y} {orient}',
                                f'prop VALUE "curvelabel={probe_name}"',
                                f'prop LABEL "{probe_name}"',
                                'unselect'])