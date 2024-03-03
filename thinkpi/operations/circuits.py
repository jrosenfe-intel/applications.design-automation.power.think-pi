import os
from collections import defaultdict
import glob
from copy import deepcopy

import skrf as rf
import pandas as pd


class Circuit:

    def __init__(self, fname, freq, z0):

        self.fname = fname
        self.freq = freq
        self.z0 = z0
        self.comp_models = None
        self.nodes = None
        self.tl_media = None
        self.comp_def = None
        self.info = []

    def import_circuit(self):

        # Parse Spice file
        with open(self.fname, 'rt') as f:
            all_lines = f.readlines()

        for line in all_lines:
            if line[0] == '*' and len(line) > 2:
                self.info.append(line[1:].strip())

            split_equal = line.strip('+').strip().split('=')
            try:
                exec(f"{split_equal[0].split(' ')[-1]}={split_equal[1].split(' ')[0]}")
            except IndexError:
                pass
        
        prefix = ['c', 'l', 'r']
        nodes = defaultdict(list)
        comp_models = {}
        # Parse circuit nodes
        for line in all_lines:
            comp_prefix = line[0].lower()
            if comp_prefix in prefix:
                comp_name, node1, node2, comp_value = line.split(' ')
                comp_value = eval(comp_value.replace("'", ''))
                comp_models[comp_name] = comp_value
                nodes[node1].append((comp_name, 0))
                nodes[node2].append((comp_name, 1))
            if '.subckt' in line.lower():
                split_line = line.split(' ')
                pos_node, neg_node = split_line[2:4]
        nodes[pos_node].append(('port', 0))
        nodes[neg_node].append(('gnd', 0))

        tl_media = rf.DefinedGammaZ0(self.freq, z0=self.z0,
                                        gamma=1j*self.freq.w/rf.c
                                    )
        comp_models['gnd'] = rf.Circuit.Ground(self.freq, name='gnd')
        comp_models['port'] = rf.Circuit.Port(self.freq, name='port',
                                                z0=self.z0
                                            )

        self.comp_models, self.nodes, self.tl_media = comp_models, nodes, tl_media
        self.comp_def = {'c': self.tl_media.capacitor,
                            'l': self.tl_media.inductor,
                            'r': self.tl_media.resistor
                    }

    def create_circuit(self, mul=1):

        prefix = {'c': mul,'l': 1/mul, 'r': 1/mul}
        mod_comp_models = {}
        for comp_name, comp_value in self.comp_models.items():
            if comp_name[0] in prefix:
                mod_comp_models[comp_name] = comp_value*prefix[comp_name[0]]
            else:
                mod_comp_models[comp_name] = comp_value

        connections = []
        for conns in self.nodes.values():
            some_conns = []
            for conn in conns:
                comp_type = conn[0][0].lower()
                try:
                    comp_model = self.comp_def[comp_type](mod_comp_models[conn[0]],
                                                            name=conn[0])
                except KeyError:
                    comp_model = mod_comp_models[conn[0]]
                some_conns.append((comp_model, conn[1]))
            connections.append(some_conns)

        cir = rf.Circuit(connections)
        ntw = cir.network
        ntw.name = os.path.basename(self.fname)
        
        return ntw

class Circuits:

    def __init__(self, path, net_ports, exts=['*.inc', '*.sp']):

        self.path = path
        self.net_ports = net_ports
        self.file_exts = exts
        self.models = {}
        self.cir_map = {}
        self.port_nums = None
    
    def load_models(self):

        port_name = list(self.net_ports.waves.keys())[0]
        f = deepcopy(self.net_ports.waves[port_name].net.f)
        if f[0] == 0:
            f[0] = 0.01
        freq = rf.Frequency.from_f(f, unit='Hz')
        z0 = self.net_ports.waves[port_name].net.z0[0, 0]
        print(f'Reading circuit models:')
        for file_ext in self.file_exts:
            for fname in glob.glob(os.path.join(self.path, file_ext)):
                cir = Circuit(fname, freq, z0)
                cir.import_circuit()
                self.models[os.path.basename(fname)] = (cir.create_circuit(), cir)
                print(f'\t{os.path.basename(fname)}')

    def model_names(self, verbose=True):

        mnames = list(self.models.keys())
        if verbose:
            print('Model names:')
            for name in mnames:
                print(f'\t{name}')
        else:
            return mnames

    def create_map(self, *map):

        if isinstance(map[0], str):
            cir_map = pd.read_csv(map[0], header=None)
        else:
            cir_map = pd.DataFrame(map)

        for idx, (port_name, cir_model) in enumerate(zip(cir_map[0], cir_map[1])):
            model = deepcopy(self.models[cir_model][0])
            model.name = f'{model.name}_{idx}' 
            self.cir_map[self.net_ports.waves[port_name].port_num] = model
        self.port_nums = list(self.cir_map.keys())





