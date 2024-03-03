import os
from collections import defaultdict
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib import colors

from thinkpi import logger


class Tcl:

    def __init__(self, db=None):

        self.db = db
        if self.db is not None and self.db.lines is None:
            self.db.load_data()
        self.products = ['PowerSI', 'Clarity3DLayout', 'PowerDC',
                            'Celsius Layout', 'XtractIM', 'OptimizePI']
        self.workflows = {'PowerSI': ['extraction/ext', 'spatial/spa',
                                        'spatial-radiation', 'Spatial-planewave',
                                        'resonance/res', 'Laout/lay/TraceCheck',
                                        'FD_VRN', 's_assess'],
                            'Clarity 3D Layout': ['3DFEMExtraction/3DFEMExt',
                                                '3DFEMSpatial/3DFEMSpa',
                                                '3DFEMRFIC'],
                            'PowerDC': ['IRDropAnalysis', 'E/TCoSimulation',
                                        'PinLocationEffectiveness',
                                        'ThermalModelExtraction',
                                        'ResistanceMeasurement',
                                        'ResistanceNetworkModelGeneration',
                                        'E/TCoExtraction'],
                            'Celsius2D': ['E/TCoSimulation',
                                            'TransientETCoSimulation',
                                            'ThermalExtractionMode',
                                            'ThermalOnly',
                                            'ThermalModelExtraction'],
                            'XtractIM': ['Extraction', 'EPA'],
                            'OptimizePI': ['postLayout', 'preLayout',
                                            'DeviceImpedanceChecking',
                                            'LoopInductancesAnalysis',
                                            'PinInductancesAnalysis',
                                            'BestCapacitorLocationEstimation']}

    def available_workflows(self, product):

        print(f'The following workflows exist for {product}:')
        for workflow in self.workflows[product]:
            print(f'\t{workflow}')

    def open_workflow(self, product_name, workflow_name):

        return (f'sigrity::open workflow -product {{{product_name}}} '
                f'-workflowkey {{{workflow_name}}}')

    def update_workflow(self, product_name, workflow_name):

        return (f'sigrity::update workflow -product {{{product_name}}} '
                f'-workflowkey {{{workflow_name}}}')

    def setup_resources(self, num_cores=2):

        return (f'sigrity::update DynamicClarity3dResource -smt 0 -local -cn localhost '
                f'-cpus {num_cores} -autoresume false -resume true -finalonly false')

    def enforce_cuasality(self):

        return 'sigrity::update option -EnforceCausality 1'

    def enable_debye_model(self):

        return 'sigrity::update option -DispersiveType 1'
    
    def find_shorts(self):

        return 'sigrity::check error -short'

    def open(self, fname):

        return f'sigrity::open document {{{fname}}}'

    def close(self):

        return f'sigrity::close document'

    def save(self, fname=None):

        if fname is None:
            return f'sigrity::save'
        else:
            return f'sigrity::save {{{fname}}}'

    def cut_by_area(self, x_lower, y_lower, x_upper, y_upper, in_or_out):

        return (f'sigrity::delete area '
                f'-leftPoint {{{x_lower}, {y_lower}}} '
                f'-rightPoint {{{x_upper}, {y_upper}}} '
                f'-{in_or_out}')

    def cut_by_boundery(self, margin, *nets):

        nets = [f'{{{net_name}}}' for net_name in nets]
        return (f'sigrity::delete area -previewResultFile '
                f'{{{os.path.join(self.db.path, self.db.name)}}} '
                f'-marginForCutByNet {{{margin}}} '
                f'-netToBoundary {" ".join(nets)}')
    
    def cut_by_nets(self, margin, *nets):

        nets = [f'{{{net_name}}}' for net_name in nets]
        cmds = [f'sigrity::update option -marginForCutByNet {{{margin}}}',
                f'sigrity::delete area -net {" ".join(nets)}']
    
        return '\n'.join(cmds)

    def shape_process(self, *args):

        return 'sigrity::process shape'

    def delete_disabled_nets(self):

        return 'sigrity::delete net -disabled'

    def delete_enabled_nets(self):

        return 'sigrity::delete net -enabled'
    
    def delete_disabled_nets(self):

        return 'sigrity::delete net -disabled'

    def delete_nets(self, *nets):

        nets = [f'{{{net_name}}}' for net_name in nets]
        return f'sigrity::delete net {" ".join(nets)}'

    def disable_nets(self, *nets):

        nets = [f'{{{net_name}}}' for net_name in nets]
        return f'sigrity::update {{selected}} {{0}} {" ".join(nets)}'

    def enable_nets(self, *nets):

        nets = [f'{{{net_name}}}' for net_name in nets]
        return f'sigrity::update net {{selected}} {{1}} {" ".join(nets)}'

    def enable_all_nets(self, *args):

        return f'sigrity::update net {{selected}} {{1}} -all'

    def disable_nets(self, *nets):

        nets = [f'{{{net_name}}}' for net_name in nets]
        return f'sigrity::update net {{selected}} {{0}} {" ".join(nets)}'

    def disable_all_nets(self, *args):

        return f'sigrity::update net {{selected}} {{0}} -all'

    def classify_as_power(self, *nets):

        nets = [f'{{{net_name}}}' for net_name in nets]
        return f'sigrity::move net {{PowerNets}} {" ".join(nets)}'

    def classify_as_ground(self, *nets):

        nets = [f'{{{net_name}}}' for net_name in nets]
        return f'sigrity::move net {{GroundNets}} {" ".join(nets)}'

    def split_nets(self, *nets):

        #nets = [f'{{{net_name}}}' for net_name in nets]
        nets = [f'{net_name}' for net_name in nets]

        tcl_proc = ['proc split_nets {nets} {\n',
                    '\tif {$nets==""} {\n',
                    '\t\t\t\treturn ""\n',
                    '\t} else {\n',
                    '\t\t\t\ttry {\n',
                    '\t\t\t\t\t\t\tsigrity::split net [lindex $nets 0]\n',
                    '\t\t\t\t} finally {\n',
                    '\t\t\t\t\t\t\tsplit_nets [lrange $nets 1 end]\n',
                    '\t\t\t\t\t\t\treturn ""\n',
                    '\t\t\t\t}\n',
                    '\t}\n',
                    '}\n\n',
                    f'split_nets [list {" ".join(nets)}]\n']

        #return f'sigrity::split net {" ".join(nets)}'
        return "".join(tcl_proc)

    def color_nets(self, color, *nets):

        nets = [f'{{{net_name}}}' for net_name in nets]

        rgb = ''
        for color in colors.to_rgba(color)[:-1]:
            rgb_color = str(int(color*255))
            if len(rgb_color) < 3:
                rgb += '0'*(3-len(rgb_color)) + rgb_color
            else:
                rgb += rgb_color

        return f'sigrity::update net color {{{rgb}}} {" ".join(nets)}'

    def nets_to_signals(self, *args):

        cmds = []
        for net_type in ['power', 'ground']:
            cmds.append(f'foreach net [sigrity::query -net -option {{type({net_type})}}] {{')
            cmds.append(f'eval sigrity::move net {{NULL}} $net}}')

        return '\n'.join(cmds)

    def traces_to_shape(self, *nets):

        cmds = [f'sigrity::process tracesToShapes -net {{{net_name}}}' 
                for net_name in nets]

        return '\n'.join(cmds)
        
    def enable_all_components(self, *args):

        cmd1 = 'set myComponents [sigrity::query -CktInstance]'
        cmd2 = r'eval [format "sigrity::update circuit -manual {enable} %1\$s" $myComponents]'
        return f'{cmd1}\n{cmd2}'

    def disable_all_components(self, *args):

        cmd1 = 'set myComponents [sigrity::query -CktInstance]'
        cmd2 = r'eval [format "sigrity::update circuit -manual {disable} %1\$s" $myComponents]'
        return f'{cmd1}\n{cmd2}'

    def enable_components(self, *comps):

        comps = [f'{{{comp_name}}}' for comp_name in comps]
        return f'sigrity::update circuit -manual {{enable}} {" ".join(comps)}'

    def disable_components(self, *comps):

        comps = [f'{{{comp_name}}}' for comp_name in comps]
        return f'sigrity::update circuit -manual {{disable}} {" ".join(comps)}'

    def delete_unused_padstacks(self, *args):

        return 'sigrity::delete padStack -unused'

    def special_voids(self, dog_leg_hole, thermal_hole, small_hole, via_hole,
                            slender_hole_area, slender_hole_size):

        return (f'sigrity::update option -DoglegHoleThreshold {{{dog_leg_hole}}} '
                f'-ThermalHoleThreshold {{{thermal_hole}}} '
                f'-SmallHoleThreshold {{{small_hole}}} '
                f'-ViaHoleThreshold {{{via_hole}}} '
                f'-SlenderHoleAreaThreshold {{{slender_hole_area}}} '
                f'-SlenderHoleSizeThreshold {{{slender_hole_size}}}')

    def auto_special_voids(self):

        return 'sigrity::update option -AutoSpecialVoid {1}'

    def import_material(self, fname):

        cmds = [f'sigrity::import material {{{fname}}}',
                f'sigrity::update material {{{fname}}} -all']
        
        return '\n'.join(cmds)

    def model_all_dielectric(self, material):

        return (f'sigrity::update layer model_name {{{material}}} '
                f'{{all dielectric layers}}')

    def model_all_conductor(self, material):

        return (f'sigrity::update layer model_name {{{material}}} '
                f'{{all conductor layers}}')

    def conductivity_all_padstacks(self, conductivity):

        return f'sigrity::update PadStack -all -conductivity {{{conductivity}}}'

    def metalname_all_padstacks(self, name):

        return f'sigrity::update PadStack -all -MetalName {{{name}}}'

    def update_layer_thickness(self, layer_names, thicknesses):

        cmds = []
        for layer_name, thickness in zip(layer_names, thicknesses):
            cmds.append(f'sigrity::update layer thickness '
                        f'{{{thickness}}} {{{layer_name}}}')
        return '\n'.join(cmds)

    def update_layer_material(self, layer_names, materials):

        cmds = []
        for layer_name, material in zip(layer_names, materials):
            cmds.append(f'sigrity::update layer model_name '
                        f'{{{material}}} {{{layer_name}}}')
        return '\n'.join(cmds)

    def update_layer_conductivity(self, layer_names, conductivities):

        cmds = []
        for layer_name, conductivity in zip(layer_names, conductivities):
            cmds.append(f'sigrity::update layer conductivity '
                        f'{{{conductivity}}} {{{layer_name}}}')
        return '\n'.join(cmds)

    def update_layer_fillin_dielectric(self, layer_names, materials):

        cmds = []
        for layer_name, material in zip(layer_names, materials):
            cmds.append(f'sigrity::update layer dielectric_name '
                        f'{{{material}}} {{{layer_name}}}')
        return '\n'.join(cmds)

    def update_layer_er(self, layer_names, ers):

        cmds = []
        for layer_name, er in zip(layer_names, ers):
            cmds.append(f'sigrity::update layer Er '
                        f'{{{er}}} {{{layer_name}}}')
        return '\n'.join(cmds)

    def update_layer_losstanget(self, layer_names, lts):

        cmds = []
        for layer_name, lt in zip(layer_names, lts):
            cmds.append(f'sigrity::update layer loss_tangent '
                        f'{{{lt}}} {{{layer_name}}}')
        return '\n'.join(cmds)

    def import_stackup(self, fname):

        return f'sigrity::import stackup {{{fname}}}'

    def export_stackup(self, fname):

        return f'sigrity::export Stackup -FileName {{{fname}}}'

    def padstack_conductivity(self, padstack_names, conductivities):

        cmds = []
        for padstack_name, conductivity in zip(padstack_names, conductivities):
            cmds.append(f'sigrity::update PadStack -name {{{padstack_name}}} '
                        f'-conductivity {{{conductivity}}}')
        return '\n'.join(cmds)

    def padstack_material(self, padstack_names, materials):

        cmds = []
        for padstack_name, material in zip(padstack_names, materials):
            cmds.append(f'sigrity::update PadStack -name {{{padstack_name}}} '
                        f'-metalName {{{material}}}')
        return '\n'.join(cmds)

    def delete_vias(self, *via_names):

        via_names = [f'{{{via_name}}}' for via_name in via_names]
        return f'sigrity::delete -Via {" ".join(via_names)}'

    def delete_nodes(self, *node_names):

        node_names = [f'{{{node_name}}}' for node_name in node_names]
        return f'sigrity::delete -Node {" ".join(node_names)}'

    def delete_shapes(self, *shape_names):

        shape_names = [f'{{{shape_name}}}' for shape_name in shape_names]
        return f'sigrity::delete -Shape {" ".join(shape_names)}'
    
    def delete_traces(self, *trace_names):

        trace_names = [f'{{{trace_name}}}' for trace_name in trace_names]
        return f'sigrity::delete -Trace {" ".join(trace_names)}'

    def delete_layers(self, *layer_names):

        cmds = [f'sigrity::delete layer {{{layer_name}}}' for layer_name in layer_names]
        return '\n'.join(cmds)

    def padstack_plating(self, padstack_names, plating_thicknesses):

        cmds = []
        for padstack_name, thickness in zip(padstack_names, plating_thicknesses):
            cmds.append(f'sigrity::update PadStack -name {{{padstack_name}}} '
                        f'-platingThickness {{{thickness}}}')
        return '\n'.join(cmds)

    def padstack_diameter(self, padstack_names, diemeters):

        cmds = []
        for padstack_name, diameter in zip(padstack_names, diemeters):
            cmds.append(f'sigrity::update PadStack -name {{{padstack_name}}} '
                        f'-radius {{{diameter/2}}}')
        return '\n'.join(cmds)

    def add_ports(self, port_names, pos_nodes, neg_nodes):

        cmds = []
        for port_name, pos_node, neg_node in zip(port_names, pos_nodes, neg_nodes):
            cmd1 = f'sigrity::add port -name {{{port_name}}}'
            cmd2 = [f'{{{pnode}}}' for pnode in pos_node]
            cmd2 = f'sigrity::hook -port {{{port_name}}} -PositiveNode {" ".join(cmd2)}'
            cmd3 = [f'{{{nnode}}}' for nnode in neg_node]
            cmd3 = f'sigrity::hook -port {{{port_name}}} -NegativeNode {" ".join(cmd3)}'
            cmds.append('\n'.join([cmd1, cmd2, cmd3]))
        return '\n'.join(cmds)

    '''
    def add_nodes(self, x_coords, y_coords, layers, rotations, padstacks):

        cmds = []
        for x_coord, y_coord, layer, rotation, padstack in \
                zip(x_coords, y_coords, layers, rotations, padstacks):
            if padstack is None:
                padstack = ''
            else:
                padstack = f' -padStack {{{padstack}}}'
            cmds.append(f'sigrity::add node -point {{{x_coord}m, {y_coord}m}} '
                        f'-layer {{{layer}}} -rotation {{{rotation}}}{padstack}')
        return '\n'.join(cmds)
    '''
    
    def add_node(self, x_coord, y_coord, layer, rotation=None, padstack=None):

        padstack = '' if padstack is None else f' -padStack {{{padstack}}}'
        rotation = 0 if rotation is None else rotation
        
        return (f'sigrity::add node -point {{{x_coord}m, {y_coord}m}} '
                f'-layer {{{layer}}} -rotation {{{rotation}}}{padstack}'
        )
        
    def default_via_conduct(self, conduct):

        return f'sigrity::set defViaConductivity -value {{{conduct}}}'

    def set_output_format(self):

        return (f'sigrity::update option -ResultFileHasTouchstone {1} '
                f'-ResultFileHasTouchstone2 {0} -ResultFileHasBnp {0}')

    def set_global_temp(self, temp):

        return f'sigrity::update option -GlobalTemperature {{{temp}}}'

    def enable_DC_point(self):

        return 'sigrity::update option -CalcDCPoint {1}'

    def set_sim_freq(self, start=0, end=1e9):

        return f'sigrity::update freq -start {{{start}}} -end {{{end}}} -AFS -customize'

    def merge_db(self, top_db, bot_ckt, top_ckt, pin_res):

        return (f'sigrity::import PKG -SPDFile {{{top_db}}} -method {{ShortCkt}} '
                f'-OldCkt {{BRD{bot_ckt}}} -NewCkt {{PKG{top_ckt}}} '
                f'-Prefix -ApplyTo {{PKG&PCB}} -InternalResistance {{{pin_res}}} '
                f'-ContinueMergeForShort')

    def bypass_confirmation(self):

        return 'sigrity::update option -ByPassYesNoCancel {1}'

    def setup_constraints(self, constr=0):

        return (f'sigrity::update pdcConGlobal -viaCurrent {{{constr}}}\n'
                f'sigrity::update pdcConGlobal -viaCurrentDensity {{{constr}}}\n'
                f'sigrity::update pdcConGlobal -planeCurrentDensity {{{constr}}}')
    
    def setup_termal_constraints(self, constr=0):

        return (f'sigrity::update ThermalConstraintGlobal -ViaTemperature {{{constr}}}\n'
                f'sigrity::update ThermalConstraintGlobal -PlaneTemperature {{{constr}}}')

    def save_pdc_sim_results(self, path):

        return f"sigrity::save pdcResults {{{os.path.join(path, 'simulation_results.xml')}}}"
    
    def ports_to_sinks(self, *sink_names):

        cmds = []
        for sink_name in sink_names:
            cmds.append(f'sigrity::add reusePort -src {{psi}} -name {{{sink_name}}} -type {{sink}}')
        
        return '\n'.join(cmds)

    def ports_to_vrms(self, *vrm_names):

        cmds = []
        for vrm_name in vrm_names:
            cmds.append(f'sigrity::add reusePort -src {{psi}} -name {{{vrm_name}}} -type {{vrm}}')
        
        return '\n'.join(cmds)

    def add_nodes_to_pads(self, max_edge=None):

        if max_edge is None:
            return ('sigrity::update option -autoAddNotesOnPads {1}')
        else:
            return ('sigrity::update option -autoAddNotesOnPads {1} '
                    f'-MaxEdgeLength {{{max_edge}}}')

    def generate_padstack(self, padstack_fname=None):

        return self.db.generate_padstack(padstack_fname)

    def generate_stackup(self, stackup_fname=None):

        return self.db.generate_stackup(stackup_fname)

    def auto_setup_padstack(self, fname, db_type, brd_plating=None,
                            pkg_gnd_plating=None, pkg_pwr_plating=None,
                            conduct=None, material=None,
                            innerfill_material=None, outer_thickness=None,
                            outer_coating_material=None, unit='m'):

        padstack_df = self.db.generate_padstack(save=False, unit=unit)

        if db_type == 'board' or db_type == 'brd':
            for idx in padstack_df.index:
                padstack_df.at[idx, 'Conductivity [S/m]'] = (padstack_df.at[idx, 'Conductivity [S/m]']
                                                        if conduct is None else conduct)
                padstack_df.at[idx, 'Material'] = (padstack_df.at[idx, 'Material']
                                                    if material is None else material)
                padstack_df.at[idx, f'Plating thickness [{unit}]'] = (padstack_df.at[idx, f'Plating thickness [{unit}]']
                                                    if brd_plating is None else brd_plating)
        elif db_type == 'package' or db_type == 'pkg':
            # Organize all vias by padstack and layers
            vias_by_padstack = defaultdict(set)
            for via in self.db.vias.values():
                vias_by_padstack[via.padstack].add(via.lower_layer)
                vias_by_padstack[via.padstack].add(via.upper_layer)

            # Iterate over the current padstack's rows and add missing layer if needed
            new_padstack_df = pd.DataFrame([], columns=padstack_df.columns)
            for _, row in padstack_df.iterrows():
                if not row['Name'] in list(new_padstack_df['Name']):
                    for via_layer in vias_by_padstack[row['Name']]:
                        row.at['Layer'] = via_layer
                        new_padstack_df = pd.concat([new_padstack_df, row.to_frame().T],
                                                    ignore_index=True)
            
            padstack_df = new_padstack_df
            for idx in padstack_df.index:
                padstack_df.at[idx, 'Conductivity [S/m]'] = (padstack_df.at[idx, 'Conductivity [S/m]']
                                                        if conduct is None else conduct)
                padstack_df.at[idx, 'Material'] = (padstack_df.at[idx, 'Material']
                                                    if material is None else material)
                try:
                    pad_top, diam, pad_bottom = [int(pad) for pad in re.findall(r'\d+', padstack_df.at[idx, 'Name'])[:3]]
                except ValueError:
                    continue

                if pad_top == pad_bottom:
                    pad = pad_top
                else:
                    if 'fco' in padstack_df.at[idx, 'Layer']:
                        pad = pad_bottom
                    elif padstack_df.at[idx, 'Layer'][-1]  == 'f':
                        pad = pad_top
                    elif 'bco' in padstack_df.at[idx, 'Layer']:
                        pad = pad_top
                    elif padstack_df.at[idx, 'Layer'][-1] == 'b':
                        pad = pad_bottom
                    else:
                        if pad == int(pad_top):
                            pad = pad_bottom
                        else:
                            pad = pad_top

                padstack_df.at[idx, 'Regular shape'] = 'circle'
                padstack_df.at[idx, f'Regular width [{unit}]'] = pad*1e-6*self.db.units[unit]
                padstack_df.at[idx, f'Regular height [{unit}]'] = pad*1e-6*self.db.units[unit]
                padstack_df.at[idx, 'Anti shape'] = 'circle'
                padstack_df.at[idx, f'Anti width [{unit}]'] = pad*1e-6*self.db.units[unit]
                padstack_df.at[idx, f'Anti height [{unit}]'] = pad*1e-6*self.db.units[unit]
                if diam > 120:
                    padstack_df.at[idx, f'Plating thickness [{unit}]'] = (padstack_df.at[idx, f'Plating thickness [{unit}]']
                                                                if pkg_gnd_plating is None else pkg_gnd_plating)
                    padstack_df.at[idx, 'Inner fill material'] = (padstack_df.at[idx, 'Inner fill material']
                                                                    if innerfill_material is None
                                                                    else innerfill_material)
                if pad > 300:
                    padstack_df.at[idx, f'Plating thickness [{unit}]'] = (padstack_df.at[idx, f'Plating thickness [{unit}]']
                                                                if pkg_pwr_plating is None else pkg_pwr_plating)
                    padstack_df.at[idx, f'Outer coating thickness [{unit}]'] = (padstack_df.at[idx, f'Outer coating thickness [{unit}]']
                                                                        if outer_thickness is None
                                                                        else outer_thickness)
                    padstack_df.at[idx, f'Outer coating material'] = (padstack_df.at[idx, f'Outer coating material']
                                                                        if outer_coating_material is None
                                                                        else outer_coating_material)
        
        padstack_df.sort_values(by=['Name', 'Layer'], inplace=True)
        padstack_df.to_csv(fname, index=False)
        return self.setup_padstack(padstack_fname=None,
                                    padstack_df=padstack_df
                                )

    def oblong_via(self, padstack_name, ob_width, ob_height,
                    layer, width, height, plating_thickness,
                    conduct, material, pad_type):

        '''
        if plating_thickness is None or conduct is None or material is None:
            return (f'sigrity::update PadStack -name {{{padstack_name}}} '
                    f'-OblongVia {{{ob_width}, {ob_height}, 0}} '
                    f'-PadData -layer {{{layer}}} '
                    f'-PadAnti {{Oblong, {width}, {height}, 0, 0}}')
        '''
        return (f'sigrity::update PadStack -name {{{padstack_name}}} '
                f'-OblongVia {{{ob_width}, {ob_height}, 0}} '
                f'-PadData -layer {{{layer}}} '
                f'-{pad_type} {{Oblong, {width}, {height}, 0, 0}} '
                f'-platingThickness {{{plating_thickness}}} '
                f'-conductivity {{{conduct}}} '
                f'-metalName {{{material}}}') 
    
    def setup_padstack(self, padstack_fname, padstack_df=None):

        if padstack_df is None:
            new_padstack = pd.read_csv(padstack_fname)
            new_padstack.dropna(how='all', inplace=True)
        else:
            new_padstack = padstack_df

        headers = new_padstack.columns
        outer_diameter, plating_thickness = headers[2], headers[3]
        regular_width, regular_height = headers[7], headers[8]
        anti_width, anti_height = headers[10], headers[11]
        outer_coating_thickness = headers[13]
        unit = outer_diameter.split('[')[1][:-1]

        current_padstack = self.db.generate_padstack(padstack_fname=None,
                                                     save=False, unit=unit)
        # Sort all vias by padstack and layers
        vias_by_padstack = defaultdict(set)
        for via in self.db.vias.values():
            vias_by_padstack[via.padstack].add(via.lower_layer)
            vias_by_padstack[via.padstack].add(via.upper_layer)

        # Iterate over the current padstack's rows and add missing layer if needed
        new_current_padstack = pd.DataFrame([], columns=current_padstack.columns)
        for _, row in current_padstack.iterrows():
            if not row['Name'] in list(new_current_padstack['Name']):
                for via_layer in vias_by_padstack[row['Name']]:
                    row.at['Layer'] = via_layer
                    new_current_padstack = pd.concat([new_current_padstack, row.to_frame().T],
                                                     ignore_index=True)
        
        # Find mismatching padstack names

        # First check from the target padstack to the .csv padstack
        for idx, row in new_current_padstack.iterrows():
            if not row['Name'] in list(new_padstack['Name']):
                logger.warning((f"Padstack {row['Name']} on layer {row['Layer']} "
                                f"does not exist in the database "
                                f'and will be ignored.'))
                
        # Now check from the .csv padstack to the target padstack
        del_idx = []
        for idx, row in new_padstack.iterrows():
            if not row['Name'] in list(new_current_padstack['Name']):
                logger.warning((f"Padstack {row['Name']} on layer {row['Layer']} does not match "
                      f'and will be ignored.'))
                del_idx.append(idx)
        if del_idx:
            new_padstack.drop(index=del_idx, inplace=True)
            new_padstack.reset_index(drop=True, inplace=True)
            
        '''
        if len(new_current_padstack['Name']) != len(new_padstack['Name']):
            print(f'Mismatch between padstack file ({len(new_current_padstack)} layers) '
                    f'and database padstack ({len(new_padstack)} layers)')
            return None
        
        # Modify padsatck and layer names to be agnostic to changes
        new_current_padstack.sort_values(by=['Name', 'Layer'], inplace=True)
        new_padstack['Name'] = new_current_padstack['Name']
        new_padstack['Layer'] = new_current_padstack['Layer']
        '''
        
        # The following section updates these 3 properties directly in the spd file since they don't have tcl commands
        padstack_spd_mods = defaultdict(set)
        for _, row in new_padstack.iterrows():
            padstack_spd_mods[row['Name']].add('')
            if pd.notnull(row['Inner fill material']):
                padstack_spd_mods[row['Name']].add(f"InnerMaterial = "
                                                    f"{row['Inner fill material']}")
            #if pd.notnull(row[outer_coating_thickness]):
            if isinstance(row[outer_coating_thickness], float):
                padstack_spd_mods[row['Name']].add(f"TSVThickness = "
                                                   f"{row[outer_coating_thickness]/self.db.units[unit]*1e3}mm")
            if pd.notnull(row['Outer coating material']):
                padstack_spd_mods[row['Name']].add(f"TSVMaterial = "
                                                    f"{row['Outer coating material']}")

        line_gen = self.db.extract_block('* PadStack collection description lines',
                                        '* CoupleLine description lines')
        for idx, line in line_gen:
            if '.PadStackDef' in line:
                padstack_name = line.split()[1]
                new_line = line.split('InnerMaterial =')[0].split('TSVMaterial =')[0].split('TSVThickness =')[0]
                new_line = f"{new_line.strip()} {' '.join(padstack_spd_mods[padstack_name])}\n"
                del self.db.lines[idx]
                self.db.lines.insert(idx, new_line)
                idx, line = next(line_gen)
                if line[0] == '+':
                    del self.db.lines[idx]

        self.db.save()

        # Generate tcl commands to modify the remaining properties
        props = {outer_diameter: '-radius {%s}', plating_thickness: '-platingThickness {%s}',
                    'Conductivity [S/m]': '-conductivity {%s}', 'Material': '-metalName {%s}',
                    'Regular shape': '-padData -layer {%s} -padRegular {%s, %s, %s, 0, 0, 0}',
                    'Anti shape': '-padData -layer {%s} -padAnti {%s, %s, %s, 0, 0, 0}'
            }

        cmds = []
        new_padstack = new_padstack.fillna('')
        prop_names = new_padstack.columns
        for _, row in new_padstack.iterrows():
            cont = False
            if ((row['Regular shape'] == 'roundedrect_x'
                    or row['Regular shape'] == 'roundedrect_y')
                    and '(' in str(row[outer_diameter])):
                od = eval(str(row[outer_diameter])) # Converting a string tuple to tuple
                cmds.append(self.oblong_via(row['Name'],
                                            od[0]/self.db.units[unit],
                                            od[1]/self.db.units[unit],
                                            row['Layer'],
                                            row[regular_width]/self.db.units[unit],
                                            row[regular_height]/self.db.units[unit],
                                            row[plating_thickness]/self.db.units[unit],
                                            row['Conductivity [S/m]'],
                                            row['Material'],
                                            'padRegular'
                                        )
                        )
                cont = True
            if ((row['Anti shape'] == 'roundedrect_x'
                  or row['Anti shape'] == 'roundedrect_y')
                  and '(' in row[outer_diameter]):
                od = eval(row[outer_diameter]) # Converting a string tuple to tuple
                cmds.append(self.oblong_via(row['Name'],
                                            od[0]/self.db.units[unit],
                                            od[1]/self.db.units[unit],
                                            row['Layer'],
                                            row[anti_width]/self.db.units[unit],
                                            row[anti_height]/self.db.units[unit],
                                            row[plating_thickness]/self.db.units[unit],
                                            row['Conductivity [S/m]'],
                                            row['Material'],
                                            'padAnti'
                                        )
                        )
                cont=True
            if cont:
                continue

            cmd = [f"sigrity::update padStack -name {{{row['Name']}}}"]
            for prop_name in prop_names:
                try:
                    if row[prop_name] != '':
                        if prop_name == f'Outer diameter [{unit}]':
                            cmd.append(props[prop_name] % (float(row[outer_diameter])/self.db.units[unit]/2))
                        elif prop_name == 'Regular shape':
                            if row[prop_name] == 'roundedrect_x' or row[prop_name] == 'roundedrect_y':
                                pname = 'Oblong'
                            else:
                                pname = row[prop_name]
                            cmd.append(props[prop_name] % (row['Layer'],
                                                            pname,
                                                            row[regular_width]/self.db.units[unit],
                                                            row[regular_height]/self.db.units[unit])
                                    )
                        elif prop_name == f'Anti shape':
                            if row[prop_name] == 'roundedrect_x' or row[prop_name] == 'roundedrect_y':
                                pname = 'Oblong'
                            else:
                                pname = row[prop_name]
                            cmd.append(props[prop_name] % (row['Layer'],
                                                            pname,
                                                            row[anti_width]/self.db.units[unit],
                                                            row[anti_height]/self.db.units[unit])
                                    )
                        elif prop_name == f'Plating thickness [{unit}]':
                            cmd.append(props[prop_name] % (row[plating_thickness]/self.db.units[unit]))
                        else:
                            cmd.append(props[prop_name] % row[prop_name])
                    elif prop_name == 'Material':
                            cmd.append(props[prop_name] % row[prop_name])
                except KeyError: # Catches any key that is not in props dict
                    pass
            cmds.append(' '.join(cmd))

        return '\n'.join(cmds)

    def auto_setup_stackup(self, fname, dielec_thickness=None,
                            metal_thickness=None, core_thickness=None,
                            conduct=None, dielec_material=None,
                            metal_material=None, core_material=None,
                            fillin_dielec_material=None, er=None,
                            loss_tangent=None, unit='m'):

        stackup_df = self.db.generate_stackup(save=False, unit=unit)
        core_idx = None
        for idx in stackup_df.index:
            if 'Medium' in stackup_df.at[idx, 'Layer Name']:
                stackup_df.at[idx, f'Thickness [{unit}]'] = (stackup_df.at[idx, f'Thickness [{unit}]']
                                                        if dielec_thickness is None else dielec_thickness)
                stackup_df.at[idx, 'Material'] = (stackup_df.at[idx, 'Material']
                                                    if dielec_material is None else dielec_material)
                stackup_df.at[idx, 'Er'] = (stackup_df.at[idx, 'Er'] if er is None else er)
                stackup_df.at[idx, 'Loss Tangent'] = (stackup_df.at[idx, 'Loss Tangent']
                                                      if loss_tangent is None else loss_tangent)
            else:
                stackup_df.at[idx, f'Thickness [{unit}]'] = (stackup_df.at[idx, f'Thickness [{unit}]']
                                                        if metal_thickness is None else metal_thickness)
                stackup_df.at[idx, 'Material'] = (stackup_df.at[idx, 'Material']
                                                    if metal_material is None else metal_material)
                stackup_df.at[idx, 'Conductivity [S/m]'] = (stackup_df.at[idx, 'Conductivity [S/m]']
                                                            if conduct is None else conduct)
                stackup_df.at[idx, 'Fill-in Dielectric'] = (stackup_df.at[idx, 'Fill-in Dielectric']
                                                            if fillin_dielec_material is None else fillin_dielec_material)
                stackup_df.at[idx, 'Er'] = ''
                stackup_df.at[idx, 'Loss Tangent'] = ''
                if 'fco' in stackup_df.at[idx, 'Layer Name']:
                    core_idx = idx + 1
        if core_idx is not None:
            stackup_df.at[core_idx, f'Thickness [{unit}]'] = (stackup_df.at[core_idx, f'Thickness [{unit}]']
                                                        if core_thickness is None else core_thickness)
            stackup_df.at[core_idx, 'Material'] = (stackup_df.at[core_idx, 'Material']
                                                    if core_material is None else core_material)
    
        stackup_df.to_csv(fname, index=False)
        return self.setup_stackup(stackup_fname=None,
                                    stackup_df=stackup_df
                                )

    def setup_stackup(self, stackup_fname, stackup_df=None):

        if stackup_df is None:
            new_stackup = pd.read_csv(stackup_fname)
            new_stackup.dropna(how='all', inplace=True)
            new_stackup = new_stackup.fillna('')
        else:
            new_stackup = stackup_df

        thickness_header = new_stackup.columns[1]
        thickness_unit = thickness_header.split('[')[1][:-1]
        
        if len(self.db.stackup) != len(new_stackup):
            logger.warning(f'Mismatch between stackup file ({len(new_stackup)} layers) '
                    f'and database stackup ({len(self.db.stackup)} layers).\n'
                    f'Searching by individual layer names.')
            # Find which layer exists in the current layout
            del_idx = []
            for idx, row in new_stackup.iterrows():
                if not row['Layer Name'] in self.db.stackup:
                    logger.warning(f"Layer {row['Layer Name']} does not match "
                          f'and will be ignored.')
                    del_idx.append(idx)
            if del_idx:
                new_stackup.drop(index=del_idx, inplace=True)
                new_stackup.reset_index(drop=True, inplace=True)
        else: 
            # Modify names to be agnostic to changes in layer names
            for index, layer_name in enumerate(self.db.stackup.keys()):
                new_stackup.at[index, 'Layer Name'] = layer_name
        
        props = {thickness_header: 'thickness', 'Material': 'model_name',
                    'Conductivity [S/m]': 'conductivity',
                    'Fill-in Dielectric': 'dielectric_name',
                    'Er': 'Er', 'Loss Tangent': 'loss_tangent'}
        cmds = []
        for _, row in new_stackup.iterrows():
            if 'Medium' in row['Layer Name']:
                column_names = ['Layer Name', thickness_header, 'Material',
                                'Er', 'Loss Tangent']                   
            elif row['Material']:
                column_names = ['Layer Name', thickness_header,
                                'Material', 'Fill-in Dielectric']
            else:
                column_names = new_stackup.columns

            if (not row['Fill-in Dielectric']) and (row['Er'] or row['Loss Tangent']):
                column_names += ['Er', 'Loss Tangent']
            
            for prop_name in column_names:
                if 'Thickness' in prop_name:
                    prop_value = row[prop_name]/self.db.units[thickness_unit]
                else:
                    prop_value = row[prop_name]
                try:
                    cmds.append(f"sigrity::update layer {props[prop_name]} "
                                f"{{{prop_value}}} {{{row['Layer Name']}}}")
                except KeyError:
                    pass

        return '\n'.join(cmds)

    def save_pdc_results(self):

        return ('sigrity::update option -AutoSaveSimulationResult {1} '
                f'-AutoExportDist2Txt {1}')
    
    def pads_to_shapes(self, max_pad_size):

        return f'sigrity::update option -MaxPadSize {{{max_pad_size}}}'

    def save_layout_view(self, path, layer, coords=None):

        if coords is not None:
            xmin, ymin, xmax, ymax = coords
        cmds = [f'sigrity::open LayoutView -layer {{{layer}}}',
                '' if coords is None else
                f'sigrity::zoom area -left {{{xmin}}} -right {{{xmax}}} '
                f'-bottom {{{ymin}}} -top {{{ymax}}}',
                f'sigrity::save LayoutView -FileName {{{os.path.join(path, layer)}.png}}']

        return '\n'.join(cmds)

    def setup_3d_freq(self, sol_freq, fmin, fmax, sw_freq, magnetic):

        if magnetic:
            '''
            freq_band = (f'sigrity::update option -Wave3DFreqBand '
                        f'{{{{{fmin} 100 linear 100}}'
                        f'{{100e3 9e6 log 10}}'
                        f'{{1e7 4e7 linear 5e6}}'
                        f'{{4e7 2e8 linear 1e7}}'
                        f'{{2.2e8 3e8 linear 2e7}}'
                        f'{{3e8 6e8 linear 3e7}}'
                        f'{{7e8 1e9 linear 1e8}}}} '
                        f'-Wave3DRefleshFList {{1}}')
            '''
            freq_band = (f'sigrity::update option -Wave3DFreqBand '
                        f'{{{{{fmin} 100 linear 100}}'
                        f'{{100e3 9e6 log 10}}'
                        f'{{1e7 4e7 linear 5e6}}'
                        f'{{4e7 2e8 linear 10e6}}'
                        f'{{2e8 {fmax} linear 20e6}}}} '
                        f'-Wave3DRefleshFList {{1}}')
            afs = 'sigrity::update option -Wave3DSettingrs_flag {0}'
        else:
            freq_band = (f'sigrity::update option -Wave3DFreqBand '
                        f'{{{{{fmin} 1e+07 log 25}}{{1e+07 {fmax} linear 1e+07}}}} '
                        # f'{{{sw_freq} {sw_freq} linear 1e+07}}}} ' # Does not work in 2021. Overwrites the previous freq. bands.
                        f'-Wave3DRefleshFList {{1}}')
            afs = 'sigrity::update option -Wave3DSettingrs_flag {1} -KMOROffConvergence {0.01}'

        cmds = [f'sigrity::update option -Wave3DSettingsolutionfreq {{{sol_freq}}}',
                freq_band,
                afs]
                #'sigrity::update option -Wave3DSettingDCRefinement {1}'] # Works only in version 2022 and beyond

        return '\n'.join(cmds)

    def setup_3d_solver(self, order):

        return (f'sigrity::update option -Wave3DSettingmetalType {{1}} '
                f'-Wave3DSettingorderType {{{order}}} '
                f'-Wave3DSettingmaxMeshIteration {{20}} '
                f'-Wave3DSettingmaxmeshRefinementPercentage {{20}} '
                f'-Wave3DSettingminimumAdaptiveIterations {{3}} '
                f'-Wave3DSettingminimumConvergedIterations {{2}} '
                f'-Wave3DSettingmaxmeshTolerance {{0.01}} ' 
                f'-Wave3DSettingLowFreqSolution {{1}} '
                f'-Wave3DSettingReuseMeshFile {{0}}')

    def setup_3d_geometry(self, dx, dy, dz, mesh):

        mesh = 6 if mesh == 'XMesh' else 4
        return (f'sigrity::update option -Wave3DSettingmeshAlgorithm {{{mesh}}} '
                f'-Wave3DSettingdxp {{{dx}}} -Wave3DSettingdxm {{{dx}}} '
                f'-Wave3DSettingdyp {{{dy}}} -Wave3DSettingdym {{{dy}}} '
                f'-Wave3DSettingdzp {{{dz}}} -Wave3DSettingdzm {{{dz}}}')
    
    def setup_poly_simplification(self, enable=False):
        
        if enable:
            return 'sigrity::update option -wave3DSettingPolygonSimplification {{1}}'
        else:
            return 'sigrity::update option -wave3DSettingPolygonSimplification {{0}}'

    def setup_3d_passivity(self):

        return 'sigrity::update option -AutoOutputPassiveFile {1}'

    def setup_3d_voids(self, void_size):

        return (f'sigrity::update option -SmallHoleThreshold {{{void_size}}} '
                f'-SlenderHoleAreaThreshold {{{(np.sqrt(void_size*1e3)*1e-3)**2}}} '
                f'-SlenderHoleSizeThreshold {{{void_size}}}')

    def enable_et_sim(self):

        return 'sigrity::set pdcSimMode -E/TCoSimulation {1}'

    def setup_thermal_boundery(self, temp, top_htc=0, bot_htc=0):

        return (f'sigrity::update option -ThermalUseDefinedHTCPCBBottom {{1}} '
                f'-ThermalUseDefinedHTCPCBTop {{1}} '
                f'-ThermalHTCPCBTopValue {{{top_htc}}} '
                f'-ThermalHTCPCBBottomValue {{{bot_htc}}} '
                f'-GlobalTemperature {{{temp}}}')

    def setup_C4_thermal(self, ref_id, dmax=2.50125e-05, d1=2.50125e-05,
                            d2=2.50125e-05, ht=2e-06, o=5.8e+07):

        return (f'sigrity::update Attributes -c {{{ref_id}}} '
                f'-Type {{Die}} -Direction {{Above}} '
                f'-Dmax {{{dmax}}} -D1 {{{d1}}} '
                f'-D2 {{{d2}}} -HT {{{ht}}} -o {{{o}}} '
                f'-DielectricMaterial {{}} -Material {{}}')
    
    def set_thermal_component(self, circuit_name):

        return f'sigrity::update circuit {{{circuit_name}}} -setAsThermalComponent {{1}}'

    def setup_die_thermal(self, circuit_name, from_name, *node_names):

        nodes = [f'{{{node_name}}}' for node_name in node_names]
        cmds = [f"sigrity::add circuit -byPinBased -node {' '.join(nodes)}",
                f'sigrity::update circuit -name {{{circuit_name}}} {{{from_name}}}',
                self.set_thermal_component(circuit_name)]

        return '\n'.join(cmds)
    
    def define_die(self, circuit_name, tim_material, length, width,
                   die_material, attach_material, attach_thinkness):

        return (f'sigrity::update circuit {{{circuit_name}}} '
                f'-die {{-slugSpacer {{{tim_material},{length},{width}}} '
                f'-die {{{die_material},{attach_material},{attach_thinkness}}}}}')

    def define_power_dissipation(self, circuit_name, power):

        return (f'sigrity::update circuit {{{circuit_name}}} '
                f'-dissipation {{ -typeSimplifyMode {{0}} '
                f'-typeSorT {{Static}} -typePorT {{Power}} '
                f'-value {{{power}}} -source {{Bottom Surface}} }}')
    
    def define_die_size(self, circuit_name, model_name, thickness, length=None, height=None):

        return (f'sigrity::update cktdef {{{model_name}}} -outline '
                f'{{-sizeLabel {{{circuit_name}}} -thickness {{{thickness}}} '
                f'-rectangle {{{length},{height}}}}}' if length is not None or height is not None else ''
            )
    
    def define_package_thermal(self, circuit_name, cavity_material,
                               cavity_length, cavity_width, height,
                               cap_material, cap_thickness, cap_length,
                               cap_width, adhesive_material, adhesive_thickness):

        return (f"sigrity::update circuit {{{circuit_name}}} "
                f"-moldCompound {{{{{cavity_material},{cavity_length},{cavity_width},{height}}} "
                f"-cavity {{'',0,0}} "
                f"-cap {{{cap_material},{cap_thickness},{cap_length},{cap_width},"
                f"{adhesive_material},{adhesive_thickness}}} "
                f"-capNoSideWalls {{0}}}}")
    
    def define_heatsink(self, circuit_name, plate_material,
                        length, width, thickness,
                        adhesive_material, adhesive_thickness,
                        htc):

        return (f"sigrity::update pdcHeatSink {{{circuit_name}_HeatSink}} -enable {1} "
                f"-plate {{{plate_material},{length},{width},{thickness}}} "
                f"-adhesive {{{adhesive_material},{adhesive_thickness}}} "
                f"-ambientType {{Heat Transfer Coefficient}} "
                f"-heatTransferCoeffient {{{htc}}} "
                f"-linkedRefDes {{{circuit_name}}}")

    def setup_pcb_comp(self, circuit_name, material, thickness, temp):

        cmds = [f"sigrity::update circuit {{{circuit_name}}} "
                f"-componentProperty {{-type {{Material}} "
                f"-material {{{material},{thickness},' ',0}}}}",
                f"sigrity::update circuit {{{circuit_name}}} "
                f"-dissipation {{-typeSimplifyMode {{0}} -typeSorT {{Static}} "
                f"-typePorT {{Temperature}} -value {{{temp}}} "
                f"-source {{Bottom Surface}}}}"]

        return '\n'.join(cmds)

    def setup_exact_mesh(self, xcenter, ycenter, length, width,
                        start_layer, end_layer, mesh_edge=0.05e-3):

        cmds = [f'sigrity::set pdcThermalMaxMeshEdgeLength {{{mesh_edge}}}',
                f'sigrity::set pdcThermalSimplifyGeometry {{0}}',
                f'sigrity::set ExactMeshAreas -Area {{Area_0}} '
                f'-X {{{xcenter}}} -Y {{{ycenter}}} -L {{{length}}} -W {{{width}}} '
                f'-S {{{start_layer}}} -E {{{end_layer}}}']
    
        return '\n'.join(cmds)
    
    def change_circuit_name(self, from_name, to_name):

        return f'sigrity::update circuit -name {{{to_name}}} {{{from_name}}}'
    
    def add_circuit(self, nodes):

        all_nodes = [f'{{{node}::{self.db.nodes[node].rail}}}' for node in nodes]
        
        return f"sigrity::add circuit -byPinBased -node {' '.join(all_nodes)}"

    def place_ldo_circuit(self, in_pnodes, in_nnodes,
                            out_pnodes, out_nnodes):

        return self.add_circuit(in_pnodes + in_nnodes
                                + out_pnodes + out_nnodes
                            )
        
    def place_ldo(self, in_pnodes, in_nnodes,
                    out_pnodes, out_nnodes,
                    ckt_name, ckt_nodes):
        
        if ckt_nodes[0] == '1':
            sink_pwr_idx = slice(0, len(in_pnodes))
            sink_gnd_idx = slice(sink_pwr_idx.stop, sink_pwr_idx.stop + len(in_nnodes))
            vrm_pwr_idx = slice(sink_gnd_idx.stop, sink_gnd_idx.stop + len(out_pnodes))
            vrm_gnd_idx = slice(vrm_pwr_idx.stop, vrm_pwr_idx.stop + len(out_nnodes))

            sink_pwr_pins = [f"{{{pin}}}" for pin in ckt_nodes[sink_pwr_idx]]
            sink_gnd_pins = [f"{{{pin}}}" for pin in ckt_nodes[sink_gnd_idx]]
            vrm_pwr_pins = [f"{{{pin}}}" for pin in ckt_nodes[vrm_pwr_idx]]
            vrm_gnd_pins = [f"{{{pin}}}" for pin in ckt_nodes[vrm_gnd_idx]]

            sorted_out_pnodes = out_pnodes
        else:
            sink_pwr_pins = [f"{{{pin.split('!!')[1]}}}" for pin in in_pnodes]
            sink_gnd_pins = [f"{{{pin.split('!!')[1]}}}" for pin in in_nnodes]
            vrm_pwr_pins = [f"{{{pin.split('!!')[1]}}}" for pin in out_pnodes]
            vrm_gnd_pins = [f"{{{pin.split('!!')[1]}}}" for pin in out_nnodes]

            # Sort out_pnodes by pin number
            sorted_out_pnodes = [(int(pin.split('!!')[1]), pin) for pin in out_pnodes]
            sorted_out_pnodes = [pin[1] for pin in sorted(sorted_out_pnodes)]

        # Find ordered unique values of rail names
        in_pwr = '/'.join({self.db.nodes[pin].rail: '' for pin in in_pnodes}.keys())
        in_gnd = '/'.join({self.db.nodes[pin].rail: '' for pin in in_nnodes}.keys())
        out_pwr = '/'.join({self.db.nodes[pin].rail: '' for pin in sorted_out_pnodes}.keys())
        out_gnd = '/'.join({self.db.nodes[pin].rail: '' for pin in out_nnodes}.keys())

        cmds = [
                f'sigrity::select {{{ckt_name}}}',
                f'sigrity::add pdcSink -auto -ckt {{{ckt_name}}} '
                f"-positivePin {' '.join(sink_pwr_pins)} "
                f"-negativePin {' '.join(sink_gnd_pins)} "
                f'-voltage {{0}} -model {{Equal Voltage}}',
                f'sigrity::add pdcVRM -auto -ckt {{{ckt_name}}} '
                f"-positivePin {' '.join(vrm_pwr_pins)} "
                f"-negativePin {' '.join(vrm_gnd_pins)} "
                f'-voltage {{0}}',
                f'sigrity::add pdcDCDC -in {{SINK_{ckt_name}_{in_pwr}_{in_gnd}}} '
                f'-out {{VRM_{ckt_name}_{out_pwr}_{out_gnd}}}'
            ]
        
        return '\n'.join(cmds)
    
    def json_to_tcl(self, path, jfname, tfname):

        if '.json' in jfname:
            with open(os.path.join(path, jfname), 'rt') as jfile:
                data = json.load(jfile)
        else:
            data = json.loads(jfname)
        
        cmds = []
        for cmd_type, options in data.items():
            cmds.append(self.cmd_select[cmd_type](*options) + '\n')

        with open(os.path.join(path, tfname), 'wt') as f:
            f.writelines(cmds)

    def create_tcl(self, tcl_fname=None, *tcl_cmds):

        if tcl_fname is None:
            tcl_fname = f'{Path(self.db.path) / Path(self.db.name).stem}.tcl'
        elif str(Path(tcl_fname).parent) == '.':
            tcl_fname = str(Path(self.db.path) / Path(tcl_fname))
        else:
            tcl_fname = str(Path(tcl_fname).resolve())

        with open(tcl_fname, 'wt') as f:
            for tcl_cmd in tcl_cmds:
                f.write(tcl_cmd + '\n')

        return tcl_fname
