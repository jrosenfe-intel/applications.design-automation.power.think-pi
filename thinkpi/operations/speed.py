import os
import re
import json
from typing import List
from datetime import datetime
from operator import attrgetter, itemgetter
from copy import deepcopy
from itertools import cycle
from collections import defaultdict
from difflib import get_close_matches
from pathlib import Path
from dataclasses import dataclass, field
import matplotlib.path as mpltPath

import numpy as np
import pandas as pd

from bokeh.io import show, curdoc
from bokeh.models import ColumnDataSource, CrosshairTool, BoxZoomTool, HoverTool, Patches, Circle, Rect
from bokeh.models import Model
from bokeh.models import BasicTicker, ColorBar, LinearColorMapper
from bokeh.plotting import figure, output_file
from bokeh.layouts import column
from bokeh.palettes import Category20, RdYlBu

from thinkpi import logger


class Sink:

    def __init__(self, properties):

        self.name = properties['name']
        self.nom_voltage = properties['nom_voltage']
        self.current = properties['current']
        self.model = properties['model']
        self.pos_nodes = properties['pos_nodes']
        self.neg_nodes = properties['neg_nodes']
        self.x_center = properties['x_center']
        self.y_center = properties['y_center']

    def __repr__(self):

        return (f'Sink name: {self.name}, Nominal voltage: {self.nom_voltage} V, '
                f'Current: {self.current} A')
    
    def __eq__(self, other):

        try:
            return all([self_attr == other_attr
                        for self_attr, other_attr in zip(self.__dict__.values(),
                                                        other.__dict__.values())])
        except AttributeError:
            return False
        
    def to_port(self, ref_z=1, suffix=None):

        suffix = '' if suffix is None else f'_{suffix}'
        port_props = {'port_name': f'{self.name}{suffix}', 'port_width': None, 
                      'ref_z': ref_z, 'pos_nodes': self.pos_nodes, 
                      'neg_nodes': self.neg_nodes}
        return Port(port_props)


class Vrm:

    def __init__(self, properties):

        self.name = properties['name']
        self.nom_voltage = properties['nom_voltage']
        self.sense_voltage = properties['sense_voltage']
        self.out_current = properties['out_current']
        self.pos_nodes = properties['pos_nodes']
        self.neg_nodes = properties['neg_nodes']
        self.pos_sense_nodes = properties['pos_sense_nodes']
        self.neg_sense_nodes = properties['neg_sense_nodes']

    def __repr__(self):

        return (f'VRM name: {self.name}, Nominal voltage: {self.nom_voltage} V, '
                f'Output current: {self.out_current} A')
    
    def __eq__(self, other):

        try:
            return all([self_attr == other_attr
                        for self_attr, other_attr in zip(self.__dict__.values(),
                                                    other.__dict__.values())])
        except AttributeError:
            return False
        
    def to_port(self, ref_z=1, suffix=None):

        suffix = '' if suffix is None else f'_{suffix}'
        port_props = {'port_name': f'{self.name}{suffix}', 'port_width': None, 
                      'ref_z': ref_z, 'pos_nodes': self.pos_nodes, 
                      'neg_nodes': self.neg_nodes}
        return Port(port_props)
    
    def sense_to_port(self, ref_z=1, suffix=None):

        suffix = '_sense' if suffix is None else suffix
        if self.pos_sense_nodes or self.neg_sense_nodes:
            port_props = {'port_name': f'{self.name}{suffix}', 'port_width': None, 
                      'ref_z': ref_z, 'pos_nodes': self.pos_sense_nodes, 
                      'neg_nodes': self.neg_sense_nodes}
            return Port(port_props)
        else:
            return None


class Node:

    idx = 0

    def __init__(self, properties):

        self.name = properties['name']
        self.type = properties['type']
        self.rail = properties['rail']
        self.x = properties['x']
        self.y = properties['y']
        self.layer = properties['layer']
        self.rotation = properties['rotation']
        self.padstack = properties['padstack']

    def __repr__(self):
        
        return (f'Node name: {self.name}, Type: {self.type}, '
                f'Rail: {self.rail}, Layer: {self.layer}, '
                f'Rotation: {self.rotation}')

    def __eq__(self, other):

        try:
            return all([self_attr == other_attr
                    for self_attr, other_attr in zip(self.__dict__.values(),
                                                    other.__dict__.values())])
        except AttributeError:
            return False


class Port:

    idx = 0

    def __init__(self, properties):

        self.name = properties['port_name']
        self.width = properties['port_width']
        self.ref_z = properties['ref_z']
        self.pos_nodes = properties['pos_nodes']
        self.neg_nodes = properties['neg_nodes']
        # The rest of the attributes are initialized by internal methods
        self.x_center = None
        self.y_center = None
        self.box_x1, self.box_y1 = None, None # Bottom left
        self.box_x2, self.box_y2 = None, None # Top right
        self.pnode_box = (None, None, None, None)
        self.nnode_box = (None, None, None, None)
        self._find_port_boxes()
        self.pos_rails, self.neg_rails = self._find_port_rails()
        self.layers = self._find_port_layers()

    def __repr__(self):
        
        return (f'Port name: {self.name}, Center (x, y): ({self.x_center}, '
                f'{self.y_center})')

    def __eq__(self, other):

        try:
            return all([self_attr == other_attr
                    for self_attr, other_attr in zip(self.__dict__.values(),
                                                    other.__dict__.values())])
        except AttributeError:
            return False

    def _find_port_rails(self):

        pos_rails = [pos_node.rail for pos_node in self.pos_nodes]
        pos_rails = list(set(pos_rails))
        neg_rails = [neg_node.rail for neg_node in self.neg_nodes]
        neg_rails = list(set(neg_rails))
        return pos_rails, neg_rails
    
    def _find_port_layers(self):

        if self.pos_nodes:
            layers = [node_name.layer for node_name in self.pos_nodes]
        else:
            layers = [node_name.layer for node_name in self.neg_nodes]
        return list(set(layers))

    def _find_port_boxes(self):

        all_nodes = self.pos_nodes + self.neg_nodes
        if not all_nodes:
            return

        self.x_center = (min(all_nodes, key=attrgetter('x')).x
                        + max(all_nodes, key=attrgetter('x')).x)/2
        self.y_center = (min(all_nodes, key=attrgetter('y')).y
                        + max(all_nodes, key=attrgetter('y')).y)/2

        # Find coordinates of the most top right and bottom left port area
        self.box_x1, self.box_y1 = (min(all_nodes, key=attrgetter('x')).x,
                                        min(all_nodes, key=attrgetter('y')).y)
        self.box_x2, self.box_y2 = (max(all_nodes, key=attrgetter('x')).x,
                                        max(all_nodes, key=attrgetter('y')).y)

         # Find coordinates of the most top right and bottom left positive and negative areas
        if self.pos_nodes:
            self.pnode_box = (min(self.pos_nodes, key=attrgetter('x')).x,
                                min(self.pos_nodes, key=attrgetter('y')).y,
                                max(self.pos_nodes, key=attrgetter('x')).x,
                                max(self.pos_nodes, key=attrgetter('y')).y)
        if self.neg_nodes:
            self.nnode_box = (min(self.neg_nodes, key=attrgetter('x')).x,
                                min(self.neg_nodes, key=attrgetter('y')).y,
                                max(self.neg_nodes, key=attrgetter('x')).x,
                                max(self.neg_nodes, key=attrgetter('y')).y)
        
    def _nodes_in_box(self, x1, y1, x2, y2, nodes: tuple):

        nodes_x, nodes_y, nodes = nodes

        return nodes[(nodes_x >= x1)
                        & (nodes_x <= x2)
                        & (nodes_y >= y1)
                        & (nodes_y <= y2)]

    def _rotate(self, angle: float, xr: float, yr: float,
                    xp: np.ndarray, yp: np.ndarray):

        cos_a = np.cos((np.pi/180)*angle)
        sin_a = np.sin((np.pi/180)*angle) 
        rot_angle = np.array([[cos_a, -sin_a],
                              [sin_a,  cos_a]])
        rot_point = np.array([[xr]*len(xp),
                              [yr]*len(yp)])
        poly = np.array([xp,
                         yp])

        rot_poly = rot_angle.dot(poly - rot_point) + rot_point
        return rot_poly[0], rot_poly[1]

    def cart_copy(self, dx, dy, nodes,
                    adj_win=(1e-5, 1e-5, 1e-5, 1e-5),
                    ref_z=None, force=False, new_name=None):

        new_props = {}
        if new_name is None:
            new_props['port_name'] = f'{self.name}_{Port.idx}'
            Port.idx += 1
        else:
            new_props['port_name'] = new_name

        new_props['port_width'] = self.width
        new_props['ref_z'] = self.ref_z if ref_z is None else ref_z
        pos_new_nodes = defaultdict(list)
        new_props['neg_nodes'] = []
        new_props['pos_nodes'] = []
        if None not in self.pnode_box:
            pnodes_in_box = self._nodes_in_box(self.pnode_box[0] + dx - adj_win[0],
                                                self.pnode_box[1] + dy - adj_win[1],
                                                self.pnode_box[2] + dx + adj_win[2],
                                                self.pnode_box[3] + dy + adj_win[3],
                                                nodes)
            for new_node in pnodes_in_box:
                if new_node.rail is not None and 'vss' not in new_node.rail.lower() and 'gnd' not in new_node.rail.lower():
                    pos_new_nodes[new_node.rail].append(new_node)
            # Find maximum number of nodes for the corresponding power rail name
            # This is done to exclude other rails that might have been included
            if pos_new_nodes:
               new_props['pos_nodes'] = max(pos_new_nodes.values(), key=len)

        if None not in self.nnode_box:                            
            nnodes_in_box = self._nodes_in_box(self.nnode_box[0] + dx - adj_win[0],
                                                self.nnode_box[1] + dy - adj_win[1],
                                                self.nnode_box[2] + dx + adj_win[2],
                                                self.nnode_box[3] + dy + adj_win[3],
                                                nodes)
            for new_node in nnodes_in_box:
                if new_node.rail is not None and ('vss' in new_node.rail.lower() or 'gnd' in new_node.rail.lower()):
                    new_props['neg_nodes'].append(new_node)

        # Copy and use nodes if nodes cannot be found in the coppied area
        if force:
            if not new_props['pos_nodes']:
                node_props = {}
                for pos_node in self.pos_nodes:
                    node_props['name'] = f'{pos_node.name}_tpi{Node.idx}'
                    Node.idx += 1
                    node_props['type'] = 'node'
                    node_props['rail'] = pos_node.rail
                    node_props['x'] = pos_node.x + dx
                    node_props['y'] = pos_node.y + dy
                    node_props['layer'] = self.layers[0]
                    node_props['rotation'] = pos_node.rotation
                    node_props['padstack'] = None
                    new_props['pos_nodes'].append(Node(node_props))
            if not new_props['neg_nodes']:
                node_props = {}
                for neg_node in self.neg_nodes:
                    node_props['name'] = f'{neg_node.name}_tpi{Node.idx}'
                    Node.idx += 1
                    node_props['type'] = 'node'
                    node_props['rail'] = neg_node.rail
                    node_props['x'] = neg_node.x + dx
                    node_props['y'] = neg_node.y + dy
                    node_props['layer'] = self.layers[0]
                    node_props['rotation'] = neg_node.rotation
                    node_props['padstack'] = None
                    new_props['neg_nodes'].append(Node(node_props))
    
        return Port(new_props)

    def mirror_copy(self, x_src, y_src, x_dst, y_dst,
                        nodes,
                        adj_win=(1e-5, 1e-5, 1e-5, 1e-5),
                        ref_z=None, force=False, new_name=None):

        # Find the line equation (ax + by + c = 0) perpendicular to the line created
        # by the given source and destination points. This line will pass
        # throught the middle of the line between the given source and destination points.
        x_mid = (x_src + x_dst)/2
        y_mid = (y_src + y_dst)/2
        if x_dst == x_src:
            a = 0
            b = 1
            c = -y_mid
        elif y_dst == y_src:
            a = 1
            b = 0
            c = -x_mid
        else:
            m = (y_dst - y_src)/(x_dst - x_src)
            a = -(-1/m)
            b = 1
            c = (-1/m)*x_mid - y_mid

        # Create mirrored artificial nodes
        mirr_pos_nodes = []
        mirr_neg_nodes = []
        node_props = {'name': None, 'type': None,
                        'rail': self.pos_rails[0], 'layer': self.layers[0],
                        'rotation': None, 'padstack': None}
        for node in self.pos_nodes:
            node_props['x'] = node.x - (2*a*(a*node.x + b*node.y + c))/(a**2 + b**2)
            node_props['y'] = node.y - (2*b*(a*node.x + b*node.y + c))/(a**2 + b**2)
            mirr_pos_nodes.append(Node(node_props))
        node_props['rail'] = self.neg_rails[0]
        for node in self.neg_nodes:
            node_props['x'] = node.x - (2*a*(a*node.x + b*node.y + c))/(a**2 + b**2)
            node_props['y'] = node.y - (2*b*(a*node.x + b*node.y + c))/(a**2 + b**2)
            mirr_neg_nodes.append(Node(node_props))

        mirr_port = Port({'port_name': f'{self.name}_{Port.idx}',
                        'port_width': None, 'ref_z': self.ref_z if ref_z is None else ref_z,
                        'pos_nodes': mirr_pos_nodes,
                        'neg_nodes': mirr_neg_nodes})
        Port.idx += 1

        return mirr_port.cart_copy(0, 0, nodes,
                                    adj_win, ref_z, force,
                                    new_name)

    def rotate_copy(self, x_src, y_src, x_dst, y_dst, rot_angle,
                        nodes,
                        adj_win=(1e-5, 1e-5, 1e-5, 1e-5),
                        ref_z=None, force=False, new_name=None):

        # Find Cartesian deltas between the two given points
        # after rotating the source point
        x_src_rot, y_src_rot = self._rotate(rot_angle, 0, 0,
                                    np.array([x_src]),
                                    np.array([y_src])
                                )
        dx = x_dst - x_src_rot
        dy = y_dst - y_src_rot
        
        # Rotate nodes by angle degrees around point (0, 0)
        pos_x, pos_y = [], []
        neg_x, neg_y = [], []
        for node in self.pos_nodes:
            pos_x.append(node.x)
            pos_y.append(node.y)
        for node in self.neg_nodes:
            neg_x.append(node.x)
            neg_y.append(node.y)
        rot_pos_x, rot_pos_y = self._rotate(rot_angle, 0, 0,
                                            np.array(pos_x),
                                            np.array(pos_y) 
                                        )
        rot_neg_x, rot_neg_y = self._rotate(rot_angle, 0, 0,
                                            np.array(neg_x),
                                            np.array(neg_y) 
                                        )
        # Create artificial nodes based on the rotated coordinates
        # Then create ports which can be copied using the existing cart_copy method
        pos_nodes = []
        neg_nodes = []
        node_props = {'name': None, 'type': None,
                        'rail': self.pos_rails[0], 'layer': self.layers[0],
                        'rotation': None, 'padstack': None}
        for x, y in zip(rot_pos_x, rot_pos_y):
            node_props['x'] = x
            node_props['y'] = y
            pos_nodes.append(Node(node_props))
        node_props['rail'] = self.neg_rails[0]
        for x, y in zip(rot_neg_x, rot_neg_y):
            node_props['x'] = x
            node_props['y'] = y
            neg_nodes.append(Node(node_props))

        rot_port = Port({'port_name': f'{self.name}_{Port.idx}',
                        'port_width': None, 'ref_z': self.ref_z if ref_z is None else ref_z,
                        'pos_nodes': pos_nodes,
                        'neg_nodes': neg_nodes})
        Port.idx += 1

        return rot_port.cart_copy(dx, dy, nodes,
                                    adj_win, ref_z, force,
                                    new_name)

    def df_props(self):

        columns = ['Name', 'New name', 'Ref Z', 'Width', 'Layer',
                    'Power rail', 'Ground rail',
                    'Positive nodes', 'Negative nodes']

        try:
            data = [self.name, None, self.ref_z, self.width, self.layers[0],
                    self.pos_rails[0], self.neg_rails[0],
                    len(self.pos_nodes), len(self.neg_nodes) 
                ]
        except IndexError: # Catches if port is not well connected or missing some info
            return None

        return pd.DataFrame([data], columns=columns)


class Layer:
    
    def __init__(self, properties: dict):

        self.name = properties['name']
        self.thickness = properties['thickness']
        self.material = properties['material']
        self.freq = properties['freq']
        self.conduct = properties['conduct']
        self.fillin_dielec = properties['fillin_dielec']
        self.perm = properties['perm']
        self.loss_tangent = properties['loss_tangent']
        self.shape = properties['shape']

    def __repr__(self):

        return (f'Layer name: {self.name}, Thickness: {self.thickness*1e6:.2f} um, '
                f'Material: {self.material}')

    def __eq__(self, other):

        try:
            return all([self_attr == other_attr
                    for self_attr, other_attr in zip(self.__dict__.values(),
                                                    other.__dict__.values())])
        except AttributeError:
            return False

    @property
    def is_signal(self):

        if 'Medium' in self.name or 'Bump' in self.name:
            return False
        else:
            return True


class Shape:

    def __init__(self, properties: dict):

        self.name = properties['name']
        self.net_name = properties['net_name']
        self.layer = properties['layer']
        self.polarity = properties['polarity']
        self.xcoords = properties['xcoords']
        self.ycoords = properties['ycoords']
        self.radius = properties['radius']
        self.xc = properties['xc']
        self.yc = properties['yc']

    def __repr__(self):

        if 'Circle' in self.name:
            return (
                f'Shape name: {self.name}, Net name: {self.net_name}, '
                f'Layer: {self.layer}, (x, y): ({self.xcoords[0]}, {self.ycoords[0]}), '
                f'Radius: {self.radius*1e3:.2f} mm, Polarity: {self.polarity}'
            )
        else:
            return (
                f'Shape name: {self.name}, Net name: {self.net_name}, '
                f'Layer: {self.layer}, Polarity: {self.polarity}'
            )

    def __eq__(self, other):

        try:
            return all([self_attr == other_attr
                    for self_attr, other_attr in zip(self.__dict__.values(),
                                                    other.__dict__.values())])
        except AttributeError:
            return False

    @property
    def is_poly(self):

        if 'Polygon' in self.name or 'Box' in self.name:
            return True
        else:
            return False

    @property
    def is_circle(self):

        if 'Circle' in self.name:
            return True
        else:
            return False

    @property
    def is_trace(self):

        if 'Trace' in self.name:
            return True
        else:
            return False
        
    @property
    def area(self):

        if self.is_poly or self.is_trace:
            # Using Shoelace algorithm
            poly_area = 0.5*np.abs(np.dot(self.xcoords, np.roll(self.ycoords, 1))
                                    - np.dot(self.ycoords, np.roll(self.xcoords, 1)))
        else:
            poly_area = np.pi*self.radius**2

        return poly_area
    

class Via:

    def __init__(self, properties: dict):

        self.name = properties['name']
        self.net_name = properties['net_name']
        self.x = properties['x']
        self.y = properties['y']
        self.upper_node = properties['upper_node']
        self.upper_layer = properties['upper_layer']
        self.lower_node = properties['lower_node']
        self.lower_layer = properties['lower_layer']
        self.padstack = properties['padstack']

    def __repr__(self):

        return (f'Via name: {self.name}, Net name: {self.net_name}, '
                f'Layers {self.lower_layer} to {self.upper_layer},\n'
                f'(x, y): ({self.x*1e3:.2f} mm, {self.y*1e3:.2f} mm), '
                f'Padstack: {self.padstack}')

    def __hash__(self):

        return hash((self.name, self.net_name,
                     self.x, self.y, self.upper_node,
                     self.upper_layer, self.lower_node,
                     self.lower_layer, self.padstack))

    def __eq__(self, other):

        try:
            return all([self_attr == other_attr
                    for self_attr, other_attr in zip(self.__dict__.values(),
                                                    other.__dict__.values())])
        except AttributeError:
            return False

class Padstack:

    def __init__(self, properties: dict):

        self.name = properties['name']
        self.layer = properties['layer']
        self.regular_geom = properties['regular_geom']
        self.anti_geom = properties['anti_geom']
        self.regular_dim = properties['regular_dim']
        self.anti_dim = properties['anti_dim']
        self.material = properties['material']
        self.inner_material = properties['inner_material']
        self.tsv_material = properties['tsv_material']
        self.tsv_thickness = properties['tsv_thickness']
        self.tsv_radius = properties['tsv_radius']
        self.plating_thickness = properties['plating_thickness']
        self.regular_shift_x = properties['regular_shift_x']
        self.regular_shift_y = properties['regular_shift_y']
        self.anti_shift_x = properties['anti_shift_x']
        self.anti_shift_y = properties['anti_shift_y']
        self.rounded_corners = properties['rounded_corners']
        self.oblong_via = properties['oblong_via']
        self.geom_select = {'circle': self.circle_geom,
                            'box': self.box_geom,
                            'square': self.square_geom,
                            'polygon': self.polygon_geom,
                            'roundedrect_x': self.roundedrectx_geom,
                            'roundedrect_y': self.roundedrecty_geom,
                            'n-poly': self.npoly_geom}

    def __repr__(self):

        return (f'Name: {self.name}, Layer: {self.layer}, '
                f'Regular geomtry: {self.regular_geom}, '
                f'Anti geometry: {self.anti_geom}')

    def __eq__(self, other):

        try:
            self_pads = [prop_pad for prop_name, prop_pad in self.__dict__.items()
                                if prop_name != 'geom_select']
            other_pads = [prop_pad for prop_name, prop_pad in other.__dict__.items()
                                if prop_name != 'geom_select']
            return all([self_attr == other_attr
                    for self_attr, other_attr in zip(self_pads,
                                                    other_pads)])
        except AttributeError:
            return False

    def _regular_anti_overlap(self):

        pass

    def _rotate(self, angle: float, xr: float, yr: float,
                    xp: np.ndarray, yp: np.ndarray):

        cos_a = np.cos((np.pi/180)*angle)
        sin_a = np.sin((np.pi/180)*angle) 
        rot_angle = np.array([[cos_a, -sin_a],
                              [sin_a,  cos_a]])
        rot_point = np.array([[xr]*len(xp),
                              [yr]*len(yp)])
        poly = np.array([xp,
                         yp])

        rot_poly = rot_angle.dot(poly - rot_point) + rot_point
        return rot_poly[0], rot_poly[1]

    def via_geom(self, direction, xc, yc, *args):

        if self.tsv_radius is None:
            side = 0.05e-3
        else:
            side = self.tsv_radius
        if direction == 'down':
            x = [xc, xc + side, xc + side, xc - side, xc - side]
            y = [yc + side, yc + side, yc - side, yc - side, yc + side]
        elif direction == 'up':
            x = [xc, xc - side, xc, xc + side, xc, xc + side, xc, xc - side]
            y = [yc, yc + side, yc, yc + side, yc, yc - side, yc, yc - side] 

        return np.array(x), np.array(y)
    
    def square_geom(self, polarity, xc, yc, *args):

        if polarity == 'regular':
            side = self.regular_dim[0]/2
        elif polarity == 'anti':
            side = self.anti_dim[0]/2
        x = [xc + side, xc + side, xc - side, xc - side]
        y = [yc + side, yc - side, yc - side, yc + side]

        return np.array(x), np.array(y)
        
    def circle_geom(self, polarity):

        if polarity == 'regular':
            return self.regular_dim[0]
        elif polarity == 'anti':
            return self.anti_dim[0]

    def box_geom(self, polarity, xc, yc, rot_angle):

        if polarity == 'regular':
            hside, vside = self.regular_dim[0]/2, self.regular_dim[1]/2
        elif polarity == 'anti':
            hside, vside = self.anti_dim[0]/2, self.anti_dim[1]/2
        x = [xc + hside, xc + hside, xc - hside, xc - hside]
        y = [yc + vside, yc - vside, yc - vside, yc + vside]

        return self._rotate(rot_angle, xc, yc,
                            np.array(x),
                            np.array(y))

    def polygon_geom(self, polarity, xc, yc, rot_angle):

        if polarity == 'regular':
            x, y = self.regular_dim[0], self.regular_dim[1]
        elif polarity == 'anti':
            x, y = self.anti_dim[0], self.anti_dim[1]

        return self._rotate(rot_angle, xc, yc,
                            np.array(x) + xc,
                            np.array(y) + yc)
    
    def _arc(self, xc, yc, r, start_angle, end_angle, n):

        angles = np.linspace((np.pi/180)*start_angle,
                                (np.pi/180)*end_angle, n)
        return xc + r*np.cos(angles), yc + r*np.sin(angles)

    def roundedrectx_geom(self, polarity, xc, yc, rot_angle):

        x, y = self.box_geom(polarity, xc, yc, 0)
        if polarity == 'regular':
            x += self.regular_shift_x
            y += self.regular_shift_y
        if polarity == 'anti':
            x += self.anti_shift_x
            y += self.anti_shift_y
        try:
            if polarity == 'regular':
                r = self.regular_dim[2]/2
            elif polarity == 'anti':
                r = self.anti_dim[2]/2
        except IndexError:
            return np.array(x), np.array(y)

        xcs = [x[0] - r, x[3] + r, x[2] + r, x[1] - r]
        ycs = [y[0] - r, y[3] - r, y[2] + r, y[1] + r]

        xvec, yvec = [], []
        angles = {'UR': (0, 90, x[0], y[0]),
                    'UL': (-270, -180, x[3], y[3]),
                    'LL': (180, 270, x[2], y[2]),
                    'LR': (-90, 0, x[1], y[1])}
        for xarc, yarc, corner in zip(xcs, ycs, angles.keys()):
            if corner in self.rounded_corners:
                x, y = self._arc(xarc, yarc, r,
                                    angles[corner][0],
                                    angles[corner][1], 10
                                )
                xvec += list(x)
                yvec += list(y)
            else:
                xvec.append(angles[corner][2])
                yvec.append(angles[corner][3])
        
        return self._rotate(rot_angle, xc, yc,
                            np.array(xvec),
                            np.array(yvec))

    def roundedrecty_geom(self, polarity, xc, yc, rot_angle):

        x, y = self.box_geom(polarity, xc, yc, 0)
        if polarity == 'regular':
            x += self.regular_shift_x
            y += self.regular_shift_y
        if polarity == 'anti':
            x += self.anti_shift_x
            y += self.anti_shift_y
        
        if polarity == 'regular':
            r = self.regular_dim[0]/2
        elif polarity == 'anti':
            r = self.anti_dim[0]/2

        xarc, yarc = self._arc(xc, yc, r, -180, 0, 20)
        xvec, yvec = list(xarc), list(yarc)
        xarc, yarc = self._arc(xc, y[0]-r,
                                r, 0, 180, 20)
        xvec += list(xarc)
        yvec += list(yarc)

        return self._rotate(rot_angle, xc, yc,
                            np.array(xvec),
                            np.array(yvec))

    def npoly_geom(self, polarity, xc, yc, rot_angle):

        if polarity == 'regular':
            nsides = int(self.regular_dim[0]*1000) + 1
            radius = self.regular_dim[1]/2
        if polarity == 'anti':
            nsides = int(self.anti_dim[0]*1000) + 1
            radius = self.anti_dim[1]/2
        xvec, yvec = self._arc(xc, yc, radius, 0, 360, nsides)

        return self._rotate(rot_angle + 360/((nsides-1)*2), xc, yc,
                            np.array(xvec),
                            np.array(yvec))

    def df_props(self, conduct=None, unit='m'):

        columns = ['Name', 'Layer', f'Outer diameter [{unit}]', f'Plating thickness [{unit}]',
                    'Conductivity [S/m]', 'Material',
                    'Regular shape', f'Regular width [{unit}]', f'Regular height [{unit}]',
                    'Anti shape', f'Anti width [{unit}]', f'Anti height [{unit}]',
                    'Inner fill material',
                    f'Outer coating thickness [{unit}]', 'Outer coating material']

        data_sorter = {('circle', 'regular_width'): lambda: self.regular_dim[0]*2,
                        ('circle', 'regular_height'): lambda: self.regular_dim[0]*2,
                        ('circle', 'anti_width'): lambda: self.anti_dim[0]*2,
                        ('circle', 'anti_height'): lambda: self.anti_dim[0]*2,
                        ('square', 'regular_width'): lambda: self.regular_dim[0]*2,
                        ('square', 'regular_height'): lambda: self.regular_dim[0]*2,
                        ('square', 'anti_width'): lambda: self.anti_dim[0]*2,
                        ('square', 'anti_height'): lambda: self.anti_dim[0]*2,
                        ('roundedrect_x', 'regular_width'): lambda: self.regular_dim[0],
                        ('roundedrect_x', 'regular_height'): lambda: self.regular_dim[1],
                        ('roundedrect_x', 'anti_width'): lambda: self.anti_dim[0],
                        ('roundedrect_x', 'anti_height'): lambda: self.anti_dim[1],
                        ('roundedrect_y', 'regular_width'): lambda: self.regular_dim[0],
                        ('roundedrect_y', 'regular_height'): lambda: self.regular_dim[1],
                        ('roundedrect_y', 'anti_width'): lambda: self.anti_dim[0],
                        ('roundedrect_y', 'anti_height'): lambda: self.anti_dim[1],
                        ('polygon', 'regular_width'): lambda: None, #lambda: self.regular_dim[0],
                        ('polygon', 'regular_height'): lambda: None, #lambda: self.regular_dim[1],
                        ('polygon', 'anti_width'): lambda: None, #lambda: self.anti_dim[0],
                        ('polygon', 'anti_height'): lambda: None} #lambda: self.anti_dim[1]}

        database = Database()

        try:
            regular_width = data_sorter[(self.regular_geom, 'regular_width')]()
            regular_height = data_sorter[(self.regular_geom, 'regular_height')]()
        except KeyError:
            regular_width = self.regular_dim[0]*2 if self.regular_dim is not None else None
            regular_height = self.regular_dim[1]*2 if self.regular_dim is not None else None
        try:
            anti_width = data_sorter[(self.anti_geom, 'anti_width')]()
            anti_height = data_sorter[(self.anti_geom, 'anti_height')]()
        except KeyError:
            anti_width = self.anti_dim[0]*2 if self.anti_dim is not None else None
            anti_height = self.anti_dim[1]*2 if self.anti_dim is not None else None

        regular_geom, anti_geom = self.regular_geom, self.anti_geom
        if regular_geom == 'box':
            regular_geom = 'rectangle'
        elif regular_geom == 'polygon':
            regular_geom = None
        if anti_geom == 'box':
            anti_geom = 'rectangle'
        elif anti_geom == 'polygon':
            anti_geom = None

        if regular_geom == 'roundedrect_x' or anti_geom == 'roundedrect_x':
            if self.oblong_via is None:
                tsv_radius = self.tsv_radius*2*database.units[unit]
            else:
                tsv_radius = ((self.tsv_radius*2 + self.oblong_via[0])*database.units[unit],
                                self.oblong_via[1]*database.units[unit])
        elif regular_geom == 'roundedrect_y' or anti_geom == 'roundedrect_y':
            if self.oblong_via is None:
                tsv_radius = self.tsv_radius*2*database.units[unit]
            else:
                tsv_radius = (self.oblong_via[0]*database.units[unit],
                                (self.tsv_radius*2 + self.oblong_via[1])*database.units[unit])
        else:
            tsv_radius = self.tsv_radius*2*database.units[unit]
        
        data = [self.name, self.layer,
                tsv_radius,
                None if self.plating_thickness is None else (self.tsv_radius - self.plating_thickness)*database.units[unit],
                conduct if self.material is None else None,
                self.material,
                regular_geom,
                None if regular_width is None else regular_width*database.units[unit],
                None if regular_height is None else regular_height*database.units[unit],
                anti_geom,
                None if anti_width is None else anti_width*database.units[unit],
                None if anti_height is None else anti_height*database.units[unit],
                self.inner_material,
                None if self.tsv_thickness is None else self.tsv_thickness*database.units[unit],
                self.tsv_material
            ]

        return pd.DataFrame([data], columns=columns)


class PadstackParser:

    def __init__(self, padstacks):

        self.props = {
            'material': lambda l: l.split('Material = ')[1].split()[0],
            'inner_material': lambda l: l.split('InnerMaterial = ')[1].split()[0],
            'tsv_material': lambda l: l.split('TSVMaterial = ')[1].split()[0],
            'tsv_thickness': lambda l: float(l.split('TSVThickness = ')[1].split('mm')[0])*1e-3,
            'oblong_via': self._oblong_via
            }
        self.prop_names = ['name', 'layer', 'regular_geom', 'anti_geom', 'regular_dim',
                            'anti_dim', 'material', 'inner_material', 'tsv_material',
                            'tsv_thickness', 'tsv_radius', 'plating_thickness',
                            'regular_shift_x', 'regular_shift_y',
                            'anti_shift_x', 'anti_shift_y', 'rounded_corners',
                            'oblong_via']
        self.padstack_props = self.reset_props()
        self.padstacks = padstacks

    def _oblong_via(self, l):

        oblong_dim = l.split('OblongVia = ')[1]
        re_exp = r'-?\ *[0-9]+\.?[0-9]*(?:[Ee]\ *[-+]?\ *[0-9]+)?'
        return [float(dim)*1e-3 for dim in re.findall(re_exp, oblong_dim)]

    def reset_props(self):

        return {prop: None for prop in self.prop_names}

    def end_pad_def(self, _):
        
        self.padstacks[self.padstack_props['name']][self.padstack_props['layer']] = \
                                                    Padstack(self.padstack_props)
        
        # Only 5 properties are reset since the remaining are further used
        for prop_name in self.prop_names[1:6]:
            self.padstack_props[prop_name] = None

    def end_padstack_def(self, _):

        # Save padstack that does not have any pad definition or layer assignment
        if self.padstack_props['name'] not in self.padstacks:
            self.padstacks[self.padstack_props['name']][self.padstack_props['layer']] = \
                                                Padstack(self.padstack_props)
        
        self.padstack_props = self.reset_props()

    def padstack_def(self, line):

        if line[0] != '+':
            split_line = line.split()
            self.padstack_props['name'] = split_line[1]
            try:
                self.padstack_props['tsv_radius'] = float(split_line[2][:-2])*1e-3
            except (IndexError, ValueError):
                pass
            try:
                self.padstack_props['plating_thickness'] = float(split_line[3][:-2])*1e-3
            except (IndexError, ValueError):
                pass
        for prop_name, prop in self.props.items():
            try:
                self.padstack_props[prop_name] = prop(line)
            except IndexError:
                pass
    
    def pad_shape(self, line):

        polarity = line.split()[0].lower()
        self.padstack_props[f'{polarity}_geom'] = line.split()[1].lower()
        re_exp = r'-?\ *[0-9]+\.?[0-9]*(?:[Ee]\ *[-+]?\ *[0-9]+)?'
        self.padstack_props[f'{polarity}_dim'] = [ 
                                float(dim)*1e-3 for dim in re.findall(re_exp, line)
                            ]

        if 'OffsetY' in line:
            self.padstack_props[f'{polarity}_shift_y'] = self.padstack_props[f'{polarity}_dim'][0]
            self.padstack_props[f'{polarity}_dim'].pop(0)
        else:
            self.padstack_props[f'{polarity}_shift_y'] = 0
        if 'OffsetX' in line:
            self.padstack_props[f'{polarity}_shift_x'] = self.padstack_props[f'{polarity}_dim'][0]
            self.padstack_props[f'{polarity}_dim'].pop(0)
        else:
            self.padstack_props[f'{polarity}_shift_x'] = 0

        if 'Rounded = ' in line:
            corners = re.findall(r'\[[A-Z]*\]', line.split('Rounded = ')[1])
            if corners:
                self.padstack_props['rounded_corners'] = [corner[1:-1] for corner in corners]
            else:
                self.padstack_props['rounded_corners'] = ['UL', 'UR', 'LL', 'LR']
        else:
            self.padstack_props['rounded_corners'] = None

    def pad_def(self, line):

        self.padstack_props['layer'] = line.split()[1]

    def pad(self, line):

        polarity = line.split()[0].lower()
        self.padstack_props[f'{polarity}_geom'] = line.split()[1].lower()
        self.padstack_props[f'{polarity}_dim'] = np.abs(float(line.split()[2][:-2])*1e-3)

    def polygon(self, line):

        if line[0] != '+':
            polarity = line.split()[0].lower()
            self.padstack_props[f'{polarity}_geom'] = line.split()[1].lower()
            self.padstack_props[f'{polarity}_dim'] = ([], [])
            split_line = line.split()[2:]
        else:
            if self.padstack_props['regular_geom'] is None:
                self.padstack_def(line)
                return
            if self.padstack_props['anti_geom'] is None:
                polarity = 'regular'
            else:
                polarity = 'anti'
            split_line = line.split()[1:]

        it = iter(split_line)
        for coord in it:
            self.padstack_props[f'{polarity}_dim'][0].append(float(coord[:-2])*1e-3)
            self.padstack_props[f'{polarity}_dim'][1].append(float(next(it)[:-2])*1e-3)


class ComponetConnection:

    def __init__(self, properties):

        self.name = properties['name']
        self.part = properties['part']
        self.usage = properties['usage']
        self.checked = properties['checked']
        self.nodes = properties['nodes']

    def __repr__(self):

        return f'Name: {self.name}, Part name: {self.part}'

    def __eq__(self, other):

        try:
            return all([self_attr == other_attr
                    for self_attr, other_attr in zip(self.__dict__.values(),
                                                    other.__dict__.values())])
        except AttributeError:
            return False

class Component:

    def __init__(self, properties):

        self.name = properties['name']
        self.xc = properties['xc']
        self.yc = properties['yc']
        self.rot_angle = properties['rot_angle']
        self.start_layer = properties['start_layer']
        self.attach_layer = properties['attach_layer']
        self.property_type = properties['property_type']

    def __repr__(self):

        return (f'Name: {self.name}, (x, y): ({self.xc}, {self.yc})\n'
                f'Rotation: {self.rot_angle}')

    def __eq__(self, other):

        try:
            return all([self_attr == other_attr
                    for self_attr, other_attr in zip(self.__dict__.values(),
                                                    other.__dict__.values())])
        except AttributeError:
            return False


class Part:

    def __init__(self, properties):

        self.name = properties['name']
        self.height = properties['height']
        self.width = properties['width']
        self.x_outline = properties['x_outline']
        self.y_outline = properties['y_outline']
        self.tags = properties['tags']

    def __repr__(self):

       return f'Part: {self.name}, Height: {self.height},\nTags: {self.tags}'

    def __eq__(self, other):

        try:
            return all([self_attr == other_attr
                    for self_attr, other_attr in zip(self.__dict__.values(),
                                                    other.__dict__.values())])
        except AttributeError:
            return False

    def _rotate(self, angle: float, xr: float, yr: float,
                    xp: np.ndarray, yp: np.ndarray):

        cos_a = np.cos((np.pi/180)*angle)
        sin_a = np.sin((np.pi/180)*angle) 
        rot_angle = np.array([[cos_a, -sin_a],
                              [sin_a,  cos_a]])
        rot_point = np.array([[xr]*len(xp),
                              [yr]*len(yp)])
        poly = np.array([xp,
                         yp])

        rot_poly = rot_angle.dot(poly - rot_point) + rot_point
        return rot_poly[0], rot_poly[1]

    def box_geom(self, xc, yc, rot_angle):

        hside, vside = self.x_outline[0]/2, self.y_outline[0]/2
        x = [xc + hside, xc + hside, xc - hside, xc - hside]
        y = [yc + vside, yc - vside, yc - vside, yc + vside]

        return self._rotate(rot_angle, xc, yc,
                            np.array(x),
                            np.array(y))

    def circle_geom(self, xc, yc, r, n=100):

        angles = np.linspace(0, 2*np.pi, n)
        return xc + r*np.cos(angles), yc + r*np.sin(angles)

    def part_geom(self, xc, yc, rot_angle):

        if self.x_outline is None and self.y_outline is None:
            return None, None
        if self.y_outline is None:
            # This means it is a ciruclar part
            return self.circle_geom(xc, yc, self.x_outline[0])
        if len(self.x_outline) == 1:
            return self.box_geom(xc, yc, rot_angle)

        x = np.array(self.x_outline) + xc
        y = np.array(self.y_outline) + yc
        return self._rotate(rot_angle, xc, yc, x, y)


class ComponentParser:

    def __init__(self, parts, components, connects):

        self.parts = parts
        self.components = components
        self.connects = connects
        self.part_props = {
                'name': lambda l: l.split()[1],
                'height': lambda l: float(l.split('Height = ')[1].split('mm')[0])*1e-3,
                'width': lambda l: float(l.split('W3DCktWidth = ')[1].split('mm')[0])*1e-3,
                'tags': self._extract_tags
            }
        self.component_props = {
                'name': lambda l: l.split()[1],
                'rot_angle': lambda l: float(l.split('Rotation = ')[1].split()[0]),
                'start_layer': lambda l: l.split('StartLayer = ')[1].split()[0],
                'attach_layer': lambda l: l.split('AttachLayer = ')[1].split()[0],
                'property_type': self._extract_prop_type 
            }
        self.connect_props = {
                'name': lambda l: l.split()[1],
                'part': lambda l: l.split()[2],
                'usage': lambda l: l.split('Usage = ')[1].split()[0],
                'checked': lambda l: l.split('Checked = ')[1].split()[0],
                'nodes': self._extract_nodes
            }
        self.item_select = {'.Part': self.part, '.Connect': self.connect,
                            '.Component': self.component}

    def _extract_prop_type(self, l):

        l = l.split('PropertyType = ')[1].strip().strip('"')
        return [prop for prop in l.split(', ')]

    def _extract_component_coords(self, l):

        re_exp = r'-?\ *[0-9]+\.?[0-9]*(?:[Ee]\ *[-+]?\ *[0-9]+)?mm'
        coords = [float(coord[:-2])*1e-3 for coord in re.findall(re_exp, l)]

        if coords:
            return coords[0], coords[1]
        else:
            return None, None

    def _extract_outline(self, l):

        if 'Outline = ' not in l:
            return None, None

        coords = l.split('Outline = ')[1]
        re_exp = r'-?\ *[0-9]+\.?[0-9]*(?:[Ee]\ *[-+]?\ *[0-9]+)?mm'
        coords = [float(coord[:-2])*1e-3 for coord in re.findall(re_exp, coords)]
        if len(coords) == 1:
            return [coords[0]], None
        
        x_outline, y_outline = [], []
        it = iter(coords)
        for coord in it:
            try:
                x_outline.append(coord)
                y_outline.append(next(it))
            except ValueError:
                pass

        return x_outline, y_outline

    def _extract_tags(self, l):

        tags = l.split('Tags = ')[1].split()
        return [tag.strip('"') for tag in tags]

    def _extract_nodes(self, l):

        re_exp = r'Node[A-Z]*\d+[!!]*[A-Z]*[a-z]*[0-9]*_?[A-Z]*[a-z]*[0-9]*'
        return re.findall(re_exp, l)
    
    def connect(self, line):

        properties = {}
        for  prop_name, prop_func in self.connect_props.items():
            try:
                properties[prop_name] = prop_func(line)
            except IndexError:
                properties[prop_name] = None
        self.connects[properties['name']] = ComponetConnection(properties)

    def component(self, line):

        properties = {}
        for  prop_name, prop_func in self.component_props.items():
            try:
                properties[prop_name] = prop_func(line)
            except IndexError:
                properties[prop_name] = None
        properties['xc'], properties['yc'] = self._extract_component_coords(line)
        if properties['rot_angle'] is None:
            properties['rot_angle'] = 0
        self.components[properties['name']] = Component(properties)

    def part(self, line):
        
        properties = {}
        for  prop_name, prop_func in self.part_props.items():
            try:
                properties[prop_name] = prop_func(line)
            except IndexError:
                properties[prop_name] = None
        properties['x_outline'], properties['y_outline'] = self._extract_outline(line)
        self.parts[properties['name']] = Part(properties)


class Trace:

    def __init__(self, properties):

        self.name = properties['name']
        self.rail = properties['rail']
        self.start_node = properties['start_node']
        self.end_node = properties['end_node']
        self.width = properties['width']
        self.layer = properties['layer']
    
    def __repr__(self):

        return (f'Name: {self.name}, Rail: {self.rail}\n'
                f'Width: {self.width}, Layer: {self.layer}')

    def __eq__(self, other):

        try:
            return all([self_attr == other_attr
                    for self_attr, other_attr in zip(self.__dict__.values(),
                                                    other.__dict__.values())])
        except AttributeError:
            return False

    def trace_geom(self, x_start, y_start, x_end, y_end):

        if self.width is None:
            return None, None
        d = self.width/2
        if x_end - x_start == 0:
            return (np.array([x_start + d, x_end + d, x_end - d, x_start - d]),
                        np.array([y_start, y_end, y_end, y_start]))
        elif y_end - y_start == 0:
            return (np.array([x_start, x_end, x_end, x_start]),
                        np.array([y_start - d, y_end - d, y_end + d, y_start + d])) 

        m = (y_start - y_end)/(x_start - x_end)
        x_start_right = x_start + np.sqrt(d**2/(1 + 1/m**2))
        x_start_left = x_start - np.sqrt(d**2/(1 + 1/m**2))
        y_start_right = y_start - (1/m)*(x_start_right - x_start)
        y_start_left = y_start - (1/m)*(x_start_left - x_start)

        x_end_right = x_end + np.sqrt(d**2/(1 + 1/m**2))
        x_end_left = x_end - np.sqrt(d**2/(1 + 1/m**2))
        y_end_right = y_end - (1/m)*(x_end_right - x_end)
        y_end_left = y_end - (1/m)*(x_end_left - x_end)

        return (np.array([x_start_right, x_end_right, x_end_left, x_start_left]),
                np.array([y_start_right, y_end_right, y_end_left, y_start_left]))


class Plotter:

    def __init__(self):

        self.plot_flags = {'traces': True, 'shapes': True, 'vias': True, 'pads': True,
                            'ports': True, 'components': False}
        self.comps_to_plot = []
        self.ports_to_plot = []

    def plot_shapes(self, p, layer, unit, background_clr, fill_alpha=1):

        xs, ys, xc, yc = [], [], [], []
        clr, clr_cir, radii = [], [], []
        shape_names = []
        shape_net_names = []

        for shape in (shape for shape in self.shapes.values() if shape.layer == layer):
            if shape.net_name is None:
                continue

            if shape.is_poly:
                xs.append(np.array(shape.xcoords)*self.units[unit])
                ys.append(np.array(shape.ycoords)*self.units[unit])
                if shape.polarity == '+':
                    clr.append(self.shape_clr[shape.net_name][0])
                else:
                    clr.append(background_clr)
                shape_names.append(shape.name)
                shape_net_names.append(shape.net_name)
            else:
                xc.append(shape.xc*self.units[unit])
                yc.append(shape.yc*self.units[unit])
                radii.append(shape.radius*self.units[unit])
                if shape.polarity == '+':
                    clr_cir.append(self.shape_clr[shape.net_name][0])
                else:
                    clr_cir.append(background_clr)
        
        source = ColumnDataSource(dict(xs=xs, ys=ys, clr=clr,
                                        shape_names=shape_names,
                                        shape_net_names=shape_net_names))

        patch_glyph = Patches(xs='xs', ys='ys', fill_color='clr',
                                fill_alpha=fill_alpha, line_color='gray')
        patch_glyph_r = p.add_glyph(source_or_glyph=source, glyph=patch_glyph)
        if fill_alpha == 1:
            tooltips = [('Shape', '@shape_names: @shape_net_names')]
            p.add_tools(HoverTool(renderers=[patch_glyph_r], tooltips=tooltips))
        # p.patches(xs='xs', ys='ys', color='clr', source=source)
        # tooltips = [('Shape', '@shape_names: @shape_net_names')]
        #hover_tool = HoverTool(tooltips=tooltips)
        #hover_tool.renderers.append(shapes_r)
        #ipythonp.add_tools(hover_tool)

        source = ColumnDataSource(dict(xc=xc, yc=yc, radii=radii,
                                        clr_cir=clr_cir))
        p.circle(x='xc', y='yc', radius='radii', color='clr_cir',
                    line_color='gray', alpha=fill_alpha, source=source)

        return p
    
    def plot_grad_grid(self, all_plot_grids, plot_min_max, layer_name, unit='mm'):
        """Plots a given grid on top of a layer plot, as well as minimum and maximum voltages.

        :param all_plot_grids: Coordinates of cells to construct
        a grid and DC gradient for each cell
        :type all_plot_grids: dict[list]
        :param plot_min_max:Coordinates of minimum and maximum
        locations and their corresponding voltages
        :type plot_min_max: dict[list]
        :param layer_name: Layer name to plot the grid on
        :type layer_name: str
        :param unit: Plotting unit, defaults to 'mm'
        :type unit: str, optional
        """        

        for cell, grids in all_plot_grids.items():
            p = self.plot_layer(layer_name, fname=f'{layer_name}_{cell}.html')
            for grid in grids:
                source = ColumnDataSource(dict(x=np.array(grid['x'])*self.units[unit],
                                               y=np.array(grid['y'])*self.units[unit],
                                               w=np.array(grid['w'])*self.units[unit],
                                               h=np.array(grid['h'])*self.units[unit])
                                    )
                p.add_glyph(source, Rect(x="x", y="y", width="w", height="h",
                                 line_color='white', line_width = 2,
                                 fill_color = None))
                source = ColumnDataSource(dict(x=np.array(grid['x'])*self.units[unit],
                                               y=np.array(grid['y'])*self.units[unit],
                                               grad=grid['grad'])
                                    )
                p.text(x='x', y='y', text='grad',
                        text_color='white',
                        text_align='center', text_baseline='middle',
                        text_font_size={'value': '15px'},
                        source=source)
        
            source = ColumnDataSource(dict(x=[np.array(plot_min_max['vmin_x'])*self.units[unit],
                                              np.array(plot_min_max['vmax_x'])*self.units[unit]],
                                            y=[np.array(plot_min_max['vmin_y'])*self.units[unit],
                                               np.array(plot_min_max['vmax_y'])*self.units[unit]],
                                            volt=[plot_min_max['min_volt'], plot_min_max['max_volt']])
                                    )
            p.text(x='x', y='y', text='volt',
                    text_color='lightgreen',
                    text_align='center', text_baseline='middle',
                    text_font_size={'value': '15px'},
                    source=source)

            p.title.text = f'{p.title.text} {cell}'
            show(p)
            for model in p.select({'type': Model}):
                prev_doc = model.document
                model._document = None
                if prev_doc:
                    prev_doc.remove_root(model)
            
    def plot_pin_current(self, data, unit='mm', background_clr='black',
                         fname=None, scale=1):
        '''Plots a heat map of pins current or temperature based on PowerDC simulation results.

        :param data: Information of the pins names and current
        :type data: pandas.DataFrame
        :param unit: The units to be used for the plot, defaults to 'mm'
        :type unit: str, optional
        :param background_clr:The background color to be used for the plot, defaults to 'black'
        :type background_clr: str, optional
        '''

        if data.empty:
            return
        
        if 'Node' in data['NodeName'].iloc[0]:
            layer = self.nodes[data['NodeName'].iloc[0].split('::')[0]].layer
            data_unit = 'mA'
            data_type = 'Current'
        elif 'Via' in data['NodeName'].iloc[0]:
            layer = self.vias[data['NodeName'].iloc[0].split('::')[0]].lower_layer
            data_unit = '⁰C'
            data_type = 'Temperature'
        else:
            raise ValueError(f'Unsupported data {type(data)}')
        
        plot_title = (f"{layer}\tMin: {data['ActualCurrent'].min():.3f} {data_unit}, "
                        f"Max: {data['ActualCurrent'].max():.3f} {data_unit}")
        p = self.canvas(plot_title, background_clr, fname)
        mapper = LinearColorMapper(palette=RdYlBu[11],
                                    low=data['ActualCurrent'].min(),
                                    high=data['ActualCurrent'].max()
                                    )
        
        bins = np.linspace(data['ActualCurrent'].min(), data['ActualCurrent'].max(), len(RdYlBu[11]))
        labels = list(range(len(RdYlBu[11]) - 1))
        df = pd.cut(data['ActualCurrent'], bins=bins, labels=labels).to_frame()
        df.columns = ['color_idx']
        data = pd.merge(data, df, left_index=True, right_index=True)
        data.dropna(inplace=True)

        node_names_patch = []
        pin_currents_patch = []
        node_names_circle = []
        pin_currents_circle = []
        x, y = [], []
        clr = []
        xcir, ycir = [], []
        clr_cir, radii = [], []
        current_xcoord, current_ycoord, current_values = [], [], []

        # Find a representative padstack in case node does not have one
        rep_padstacks = []
        for node in self.nodes.values():
            try:
                if (node.layer == layer
                        and self.padstacks[node.padstack][layer].regular_geom == 'circle'
                        and self.padstacks[node.padstack][layer].tsv_radius is not None):
                    rep_padstacks.append((self.padstacks[node.padstack][layer],
                                         self.padstacks[node.padstack][layer].tsv_radius))
            except KeyError:
                pass
        if rep_padstacks:
            rep_padstack = min(rep_padstacks, key=itemgetter(1))[0]

        max_value = -np.inf
        xmax = ymax = wmax = hmax = 0
        for node_name, clr_idx, current in zip(data['NodeName'], data['color_idx'], data['ActualCurrent']):
            if 'Node' in node_name:
                node = self.nodes[node_name.split('::')[0]]
            elif 'Via' in node_name:
                node = self.vias[node_name.split('::')[0]]
            else:
                raise TypeError(f'Unsupported data type {type(data)}')
            
            try:
                padstack = self.padstacks[node.padstack][layer]
            except KeyError:
                if 'DefaultLibLayer' in self.padstacks[node.padstack]:
                    padstack = self.padstacks[node.padstack]['DefaultLibLayer']
                else:
                    padstack = rep_padstack

            if padstack.regular_geom is not None:
                pad_type = 'regular'
            elif padstack.anti_geom is not None:
                pad_type = 'anti'
            else:
                continue
            if padstack.regular_geom == 'circle' or padstack.anti_geom == 'circle':
                xcir.append(node.x*self.units[unit])
                ycir.append(node.y*self.units[unit])
                radii.append(padstack.geom_select['circle'](pad_type)*self.units[unit]*scale)
                clr_cir.append(mapper.palette[clr_idx])
                node_names_circle.append(node_name)
                pin_currents_circle.append(current)
                if current > max_value:
                    max_value = current
                    xmax = node.x*self.units[unit]
                    ymax = node.y*self.units[unit]
                    wmax = 2*padstack.geom_select['circle'](pad_type)*self.units[unit]*1.5*scale
                    hmax = wmax

                if ('vss' not in node_name.split('::')[1].lower()
                        and 'gnd' not in node_name.split('::')[1].lower()):
                    current_xcoord.append(node.x*self.units[unit])
                    current_ycoord.append(node.y*self.units[unit])
                    if data_type == 'Current':
                        current_values.append(f'{current*1e-3:.2f}')
                    else:
                        current_values.append(f'{current:.2f}')
            else:
                geom = (padstack.regular_geom if pad_type == 'regular'
                        else padstack.anti_geom)
                xvec, yvec = padstack.geom_select[geom](pad_type, 
                                                        node.x,
                                                        node.y,
                                                        node.rotation)
                x.append(xvec*self.units[unit])
                y.append(yvec*self.units[unit])
                clr.append(mapper.palette[clr_idx])
                node_names_patch.append(node_name)
                pin_currents_patch.append(current)
                if current > max_value:
                    max_value = current
                    xmax = np.mean(xvec)*self.units[unit]
                    ymax = np.mean(yvec)*self.units[unit]
                    wmax = (max(xvec) - min(xvec))*self.units[unit]*1.5
                    hmax = (max(yvec) - min(yvec))*self.units[unit]*1.5

                if ('vss' not in node_name.split('::')[1].lower()
                        and 'gnd' not in node_name.split('::')[1].lower()):
                    current_xcoord.append(np.mean(xvec)*self.units[unit])
                    current_ycoord.append(np.mean(yvec)*self.units[unit])
                    if data_type == 'Current':
                        current_values.append(f'{current*1e-3:.2f}')
                    else:
                        current_values.append(f'{current:.2f}')
        
        source = ColumnDataSource(dict(x=x, y=y, clr=clr,
                                        node_names=node_names_patch,
                                        pin_currents=pin_currents_patch))
        patch_glyph = Patches(xs='x', ys='y', fill_color='clr')
        patch_glyph_r = p.add_glyph(source_or_glyph=source, glyph=patch_glyph)
        source = ColumnDataSource(dict(xcir=xcir, ycir=ycir, radii=radii,
                                 clr_cir=clr_cir,
                                 node_names=node_names_circle,
                                 pin_currents=pin_currents_circle))
        circle_glyph = Circle(x='xcir', y='ycir', radius='radii', fill_color='clr_cir',
                               line_color=None)
        circle_glyph_r = p.add_glyph(source_or_glyph=source, glyph=circle_glyph)
        source = ColumnDataSource(dict(current_xcoord=current_xcoord,
                                        current_ycoord=current_ycoord,
                                        current_values=current_values))
        p.text(x='current_xcoord', y='current_ycoord', text='current_values',
                    text_color='black',
                    text_align='center', text_baseline='middle',
                    text_font_size={'value': '10px'},
                    source=source)
        source = ColumnDataSource(dict(x=[xmax], y=[ymax], w=[wmax], h=[hmax]))
        p.add_glyph(source, Rect(x="x", y="y", width="w", height="h",
                                 line_color='white', line_width = 3,
                                 line_dash='dashed', fill_color = None))

        color_bar = ColorBar(color_mapper=mapper,
                                ticker=BasicTicker(desired_num_ticks=len(RdYlBu[11]))
                            )
        p.add_layout(color_bar, 'right')
        p.add_tools(CrosshairTool(), BoxZoomTool(match_aspect=True))
        TOOLTIPS = [('Pin', "@node_names"),
                    (data_type, f"@pin_currents {data_unit}")]
        p.add_tools(HoverTool(renderers=[patch_glyph_r, circle_glyph_r],
                                tooltips=TOOLTIPS
                            )
                )

        show(p)
        for model in p.select({'type': Model}):
            prev_doc = model.document
            model._document = None
            if prev_doc:
                prev_doc.remove_root(model)
        
    def plot_node_pads(self, p, layer, unit, background_clr):

        x, y = [], []
        clr = []
        xcir, ycir = [], []
        clr_cir, radii = [], []

        for node in (node for node in self.nodes.values() if node.layer == layer):
            try:
                padstack = self.padstacks[node.padstack][layer]
            except KeyError:
                if 'DefaultLibLayer' in self.padstacks[node.padstack]:
                    padstack = self.padstacks[node.padstack]['DefaultLibLayer']
                    if padstack.regular_geom is None:
                        continue
                else:
                    continue
            
            if padstack.regular_geom is None:
                continue
            elif padstack.regular_geom == 'circle':
                xcir.append(node.x*self.units[unit])
                ycir.append(node.y*self.units[unit])
                radii.append(padstack.geom_select['circle']('regular')*self.units[unit])
                clr_cir.append(self.shape_clr[node.rail][0])
            else:
                xvec, yvec = padstack.geom_select[padstack.regular_geom]('regular', 
                                                                            node.x,
                                                                            node.y,
                                                                            node.rotation)
                x.append(xvec*self.units[unit])
                y.append(yvec*self.units[unit])
                clr.append(self.shape_clr[node.rail][0])
            if padstack.plating_thickness is not None:
                    xcir.append(node.x*self.units[unit])
                    ycir.append(node.y*self.units[unit])
                    radii.append(padstack.plating_thickness*self.units[unit])
                    clr_cir.append(background_clr)

        source = ColumnDataSource(dict(x=x, y=y, clr=clr))
        p.patches(xs='x', ys='y', color='clr',
                    line_color='gray', source=source)
        source = ColumnDataSource(dict(xcir=xcir, ycir=ycir, radii=radii,
                                        clr_cir=clr_cir))
        p.circle(x='xcir', y='ycir', radius='radii', color='clr_cir',
                    line_color='gray', source=source)

        return p

    def plot_vias(self, p, layer, unit, background_clr):

        x, y = [], []
        clr = []
        xpad, ypad = [], []
        clr_pad = []
        xcir, ycir, xcir_anti, ycir_anti = [], [], [], []
        clr_cir, radii, radii_anti = [], [], []
        for via in self.vias.values():
            try:
                padstack = self.padstacks[via.padstack][layer]
            except KeyError:
                if None in self.padstacks[via.padstack]:
                    padstack = self.padstacks[via.padstack][None]
                else:
                    continue
            if via.upper_layer == layer:
                direction = 'down'
                rot_angle = self.nodes[via.upper_node].rotation
            elif via.lower_layer == layer:
                direction = 'up'
                rot_angle = self.nodes[via.lower_node].rotation
            else:
                continue

            xvec, yvec = padstack.via_geom(direction, via.x, via.y)
            x.append(xvec*self.units[unit])
            y.append(yvec*self.units[unit])
            clr.append(self.shape_clr[via.net_name][0])
            if padstack.regular_geom == 'circle':
                xcir.append(via.x*self.units[unit])
                ycir.append(via.y*self.units[unit])
                radii.append(padstack.geom_select['circle']('regular')*self.units[unit])
                clr_cir.append(self.shape_clr[via.net_name][0])
                if padstack.plating_thickness is not None:
                    xcir_anti.append(via.x*self.units[unit])
                    ycir_anti.append(via.y*self.units[unit])
                    radii_anti.append(padstack.plating_thickness*self.units[unit])
            elif padstack.regular_geom is not None:
                xvec, yvec = padstack.geom_select[padstack.regular_geom]('regular', via.x, via.y, rot_angle)
                xpad.append(xvec*self.units[unit])
                ypad.append(yvec*self.units[unit])
                clr_pad.append(self.shape_clr[via.net_name][0])

        if self.plot_flags['pads']:
            source = ColumnDataSource(dict(xcir=xcir, ycir=ycir, radii=radii,
                                            clr_cir=clr_cir))
            p.circle(x='xcir', y='ycir', radius='radii', color='clr_cir',
                        line_color='gray', source=source)
            source = ColumnDataSource(dict(xcir_anti=xcir_anti, ycir_anti=ycir_anti,
                                            radii_anti=radii_anti))
            p.circle(x='xcir_anti', y='ycir_anti', radius='radii_anti',
                        color=background_clr, line_color='gray', source=source)
        source = ColumnDataSource(dict(xpad=xpad, ypad=ypad,
                                        clr_pad=clr_pad))
        p.patches(xs='xpad', ys='ypad', color='clr_pad', fill_alpha=0,
                    line_color='gray', source=source)
        if self.plot_flags['pads']:
            source = ColumnDataSource(dict(xcir=xcir, ycir=ycir, radii=radii,
                                            clr_cir=clr_cir))
            p.circle(x='xcir', y='ycir', radius='radii', color='clr_cir',
                        fill_alpha=0, line_color='gray', source=source)
        source = ColumnDataSource(dict(x=x, y=y, clr=clr))
        p.patches(xs='x', ys='y', color='clr', fill_alpha=0,
                    line_color='gray', source=source)
        
        return p

    def _port_3d_geom(self, width, x_start, y_start, x_end, y_end):

        d = width/2
        if x_end - x_start == 0:
            return (np.array([x_start + d, x_end + d, x_end - d, x_start - d]),
                        np.array([y_start, y_end, y_end, y_start]))
        elif y_end - y_start == 0:
            return (np.array([x_start, x_end, x_end, x_start]),
                        np.array([y_start - d, y_end - d, y_end + d, y_start + d])) 

        m = (y_start - y_end)/(x_start - x_end)
        x_start_right = x_start + np.sqrt(d**2/(1 + 1/m**2))
        x_start_left = x_start - np.sqrt(d**2/(1 + 1/m**2))
        y_start_right = y_start - (1/m)*(x_start_right - x_start)
        y_start_left = y_start - (1/m)*(x_start_left - x_start)

        x_end_right = x_end + np.sqrt(d**2/(1 + 1/m**2))
        x_end_left = x_end - np.sqrt(d**2/(1 + 1/m**2))
        y_end_right = y_end - (1/m)*(x_end_right - x_end)
        y_end_left = y_end - (1/m)*(x_end_left - x_end)

        return (np.array([x_start_right, x_end_right, x_end_left, x_start_left]),
                np.array([y_start_right, y_end_right, y_end_left, y_start_left]))

    def plot_ports(self, p, layer, unit, *args):

        x, y = [], []
        x_3d, y_3d = [], []
        port_names = []
        name_xcoord, name_ycoord = [], []
        plus_xcoord, plus_ycoord, minus_xcoord, minus_ycoord = [], [], [], []
        margin_outline = self.port_outline_scaler*self.db_diag
        if self.ports_to_plot:
            ports_to_plot = [self.ports[port_name] for port_name in self.ports_to_plot]
        else:
            ports_to_plot = self.ports.values()
        for port in (port for port in ports_to_plot if layer in port.layers):
            x_top_left = (port.box_x1 - margin_outline)*self.units[unit]
            x_bot_right = (port.box_x2 + margin_outline)*self.units[unit]
            y_top_left = (port.box_y1 - margin_outline)*self.units[unit]
            y_bot_right = (port.box_y2 + margin_outline)*self.units[unit]

            x.append([x_top_left, x_top_left, x_bot_right, x_bot_right])
            y.append([y_top_left, y_bot_right, y_bot_right, y_top_left])

            name_xcoord.append((x_top_left + x_bot_right)/2)
            name_ycoord.append((y_top_left + y_bot_right)/2)
            port_names.append(port.name)
            # Find positive and negative node locations
            for pos_node in port.pos_nodes:
                plus_xcoord.append(pos_node.x*self.units[unit])
                plus_ycoord.append(pos_node.y*self.units[unit])
            for neg_node in port.neg_nodes:
                minus_xcoord.append(neg_node.x*self.units[unit])
                minus_ycoord.append(neg_node.y*self.units[unit])

            # If this is a 3D port add the width boxes
            if port.width is not None:
                xvec, yvec = self._port_3d_geom(port.width, port.pos_nodes[0].x,
                                                port.pos_nodes[0].y,
                                                port.neg_nodes[0].x, port.neg_nodes[0].y)
                x_3d.append(xvec*self.units[unit])
                y_3d.append(yvec*self.units[unit])
                
        source = ColumnDataSource(dict(x=x, y=y))
        p.patches(xs='x', ys='y', color='#3BED3B', fill_alpha=0,
                    line_color='#3BED3B', line_dash='dashed',
                    line_width=2, source=source)
        source = ColumnDataSource(dict(x=x_3d, y=y_3d))
        p.patches(xs='x', ys='y', color='#ff0000', fill_alpha=0,
                    line_color='#ff0000', line_dash='dashed',
                    line_width=2, source=source)
    
        source = ColumnDataSource(dict(name_xcoord=name_xcoord,
                                        name_ycoord=name_ycoord,
                                        port_names=port_names))
        p.text(x='name_xcoord', y='name_ycoord', text='port_names',
                    text_color='#3BED3B', text_font_style='bold',
                    text_align='center', text_baseline = 'middle',
                    source=source)
        source = ColumnDataSource(dict(plus_xcoord=plus_xcoord, plus_ycoord=plus_ycoord,
                                        pos=['+']*len(plus_xcoord)))
        p.text(x='plus_xcoord', y='plus_ycoord', text='pos', text_color='red',
                    text_font_style='bold', text_baseline = 'middle',
                    text_align='center', text_font_size = {'value': '28px'}, source=source)
        source = ColumnDataSource(dict(minus_xcoord=minus_xcoord, minus_ycoord=minus_ycoord,
                                        neg=['‒']*len(minus_xcoord)))
        p.text(x='minus_xcoord', y='minus_ycoord', text='neg', text_color='#3BED3B',
                    text_font_style='bold', text_baseline = 'middle',
                    text_align='center', source=source)

        return p

    def plot_components(self, p, layer, unit):

        if self.comps_to_plot:
            comps_to_plot = [(comp_name, self.connects[comp_name].part)
                                for comp_name in self.comps_to_plot]
        else:
            comps_to_plot = self.component_names(verbose=False)

        x, y = [], []
        xpin, ypin = [], []
        comp_names = []
        name_xcoord, name_ycoord = [], []
        for comp_name, part_name in (comp_to_plot for comp_to_plot in comps_to_plot
                                        if self.components[comp_to_plot[0]].start_layer == layer):
                comp_names.append(comp_name)
                xc = self.components[comp_name].xc
                yc = self.components[comp_name].yc
                rot_angle = self.components[comp_name].rot_angle
                name_xcoord.append(xc*self.units[unit])
                name_ycoord.append(yc*self.units[unit])
                xvec, yvec = self.parts[part_name].part_geom(xc, yc, rot_angle)

                if xvec is None and yvec is None:
                    continue
                else:
                    x.append(xvec*self.units[unit])
                    y.append(yvec*self.units[unit])

                for node_name in self.connects[comp_name].nodes:
                    xpin.append(self.nodes[node_name].x*self.units[unit])
                    ypin.append(self.nodes[node_name].y*self.units[unit])

        source = ColumnDataSource(dict(x=x, y=y))
        p.patches(xs='x', ys='y', color='yellow', fill_alpha=0.1,
                    line_color='#3BED3B', line_dash='dashed',
                    line_width=1, source=source)
        source = ColumnDataSource(dict(xcir=xpin, ycir=ypin))
        p.circle(x='xcir', y='ycir',
                    radius=self.node_radius_scaler*self.db_diag*self.units[unit],
                    color='#3BED3B', fill_alpha=0, line_color='#3BED3B',
                    source=source)
        source = ColumnDataSource(dict(name_xcoord=name_xcoord,
                                        name_ycoord=name_ycoord,
                                        comp_names=comp_names))
        p.text(x='name_xcoord', y='name_ycoord', text='comp_names',
                    text_color='#3BED3B', text_font_style='bold',
                    text_align='center', text_baseline = 'middle',
                    source=source)
        
        return p

    def plot_traces(self, p, layer, unit, background_clr):

        x, y = [], []
        clr = []
        xcir, ycir, radii, cir_clr = [], [], [], []
        for trace in (trace for trace in self.traces.values() if trace.layer == layer):
            x_start = self.nodes[trace.start_node].x
            y_start = self.nodes[trace.start_node].y
            x_end = self.nodes[trace.end_node].x
            y_end = self.nodes[trace.end_node].y
            xvec, yvec = trace.trace_geom(x_start, y_start, x_end, y_end)
            if xvec is None and yvec is None:
                continue
            x.append(xvec*self.units[unit])
            y.append(yvec*self.units[unit])
            clr.append(self.shape_clr[trace.rail][0])
            xcir.append(x_end*self.units[unit])
            ycir.append(y_end*self.units[unit])
            radii.append((trace.width/2)*self.units[unit])
            cir_clr.append(self.shape_clr[trace.rail][0])

        source = ColumnDataSource(dict(x=x, y=y, clr=clr))
        p.patches(xs='x', ys='y', color='clr', source=source)
        source = ColumnDataSource(dict(xcir=xcir, ycir=ycir,
                                        radii=radii, cir_clr=clr))
        p.circle(x='xcir', y='ycir', radius='radii',
                    color='cir_clr', source=source)
        
        return p
        
    def canvas(self, layer, background_clr, fname=None):

        #curdoc().theme = 'dark_minimal'
        fname = 'database_plot.html' if fname is None else fname
        output_file(os.path.join(self.path, fname))

        if self.x_range is None or self.y_range is None:
            p = figure(width=int(800*1.5), height=800, title=f'Layer: {layer}',
                        x_axis_location = 'above', match_aspect=True,
                        output_backend='webgl')
        else:
            p = figure(width=int(800*1.5), height=800, title=f'Layer: {layer}',
                        x_axis_location = 'above',
                        x_range=self.x_range, y_range=self.y_range,
                        match_aspect=True, output_backend='webgl')
        
        p.background_fill_color = background_clr
        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = None

        return p

    def plot_layer(self, layer, unit='mm', background_clr='black', fname=None):

        plot_items = {'traces': self.plot_traces,
                        'shapes' : self.plot_shapes,
                        'pads': self.plot_node_pads,
                        'vias': self.plot_vias,
                        'ports': self.plot_ports}

        p = self.canvas(layer, background_clr, fname)
        for item_name in plot_items.keys():
            if self.plot_flags[item_name]:
                p = plot_items[item_name](p, layer, unit, background_clr)

        if self.plot_flags['shapes']:
            p = self.plot_shapes(p, layer, unit, background_clr, fill_alpha=0)
        if self.plot_flags['components']:
            p = self.plot_components(p, layer, unit)

        p.add_tools(CrosshairTool(), BoxZoomTool(match_aspect=True))

        if self.x_range is None or self.y_range is None:
            self.x_range, self.y_range = p.x_range, p.y_range

        return p

    def prepare_plots(self, *layers, unit='mm', background_clr='black'):

        if not layers:
            layers_to_plot = self.layer_names(verbose=False)
        else:
            layers_to_plot = layers

        logger.info('\nUpdating plots on layers:')
        for layer in layers_to_plot:
            logger.info(f'\t{layer}')
            self.layer_plots[layer] = self.plot_layer(layer, unit, background_clr)

    def plot(self, *layers):

        if not layers:
            layers = self.layer_names(verbose=False)
        layers_to_plot = [self.layer_plots[layer] for layer in layers]
        show(column(layers_to_plot))

        for p in layers_to_plot:
            for model in p.select({'type': Model}):
                prev_doc = model.document
                model._document = None
                if prev_doc:
                    prev_doc.remove_root(model)


class Database(Plotter):

    logger_file_id = None
    logger_queue_id = None

    def __init__(self, db_path=None, q=None):

        super().__init__()
        self.path = str(Path(db_path).resolve().parent) if db_path is not None else None
        self.name = str(Path(db_path).name) if db_path is not None else None
        
        # Remove logger to avoid adding multiple loggers each time this class is instantiated
        if Database.logger_file_id is not None:
            try:
                logger.remove(Database.logger_file_id)
            except ValueError:
                pass
        if self.path is not None:
            Database.logger_file_id = logger.add(Path(self.path) / Path('thinkpi.log'), mode='w',
                                            format="[{time:MM-DD-YYYY HH:mm:ss}] {message}",
                                            level='INFO')
        if q is not None:
            self.q = q
            # Remove logger to avoid adding multiple loggers each time this class is instantiated
            if Database.logger_queue_id is not None:
                logger.remove(Database.logger_queue_id)
            Database.logger_queue_id = logger.add(
                            self.put,
                            format="[{time:MM-DD-YYYY HH:mm:ss}] [{level}] [{function}] {message}",
                            level="DEBUG"
                        )
    
        self.db_ver = None
        self.boxes = {}
        self.net_names = {}
        self.lines = None
        self.stackup = {}
        self.sinks = {}
        self.vrms = {}
        self.nodes = {}
        self.ports = {}
        self.shapes = {}
        self.shape_clr = {}
        self.vias = {}
        self.parts = {}
        self.components = {}
        self.connects = {}
        self.padstacks = defaultdict(dict)
        self.padstacks_in_design = set()
        self.traces = {}
        
        self.db_x_top_right = None
        self.db_y_top_right = None
        self.db_x_bot_left = None
        self.db_y_bot_left = None
        self.db_diag = None
        self.outline_scaler = None
        self.node_radius_scaler = 3e-4
        self.port_outline_scaler = 0.0003
        self.units = {'nm': 1e9, 'um': 1e6, 'mm': 1e3, 'cm': 1e1, 'm': 1, 
                        'mil': 39370.1, 'inch': 39.3701}
        self.x_range = None
        self.y_range = None
        self.layer_plots = {}
        self.load_flags = {'layers': True, 'nets': True, 'nodes': True,
                            'ports': True, 'shapes': True, 'padstacks': True,
                            'vias': True, 'components': True, 'traces': True,
                            'sinks': True, 'vrms': True, 'plots': True}
        
    def put(self, message):

        self.q.put(message)

    def __repr__(self):

        return (f'Path: {self.path}\n'
                f'Name: {self.name}\n'
                f'Version: {self.db_ver}\n'
                f'Size: ({self.db_x_bot_left*1e3:.3f}, '
                f'{self.db_y_bot_left*1e3:.3f}, '
                f'{self.db_x_top_right*1e3:.3f}, '
                f'{self.db_y_top_right*1e3:.3f}) mm')

    def __eq__(self, other):

        attrs = []
        try:
            self_attrs = [self.stackup, self.nodes, self.ports,
                            self.vias, self.parts, self.components,
                            self.connects, self.traces]
            other_attrs = [other.stackup, other.nodes, other.ports,
                            other.vias, other.parts, other.components,
                            other.connects, other.traces]

            for self_attr, other_attr in zip(self_attrs, other_attrs):
                for self_prop, other_prop in zip(self_attr.values(),
                                                other_attr.values()):
                    attrs.append(self_prop == other_prop)
            attrs.append(self.lines == other.lines)
            for self_pad_bylayer, other_pad_bylayer in zip(self.padstacks.values(),
                                                            other.padstacks.values()):
                for self_pad, other_pad in zip(self_pad_bylayer.values(),
                                                other_pad_bylayer.values()):
                    attrs.append(self_pad == other_pad)
            return all(attrs)
        except AttributeError:
            return False
        
    def version_handler(self, section):

        sections = {'nodes_start': {18: '* Node and Trace description lines',
                                    19: '* Node description lines',
                                    21: '* Node description lines',
                                    22: '* Node description lines'},
                    'nodes_end': {18: '* Via description lines',
                                  19: '* Trace description lines',
                                  21: '* Trace description lines',
                                  22: '* Trace description lines'},
                    'cuts': {18: '* Cutting Boundary description lines',
                             19: '* CuttingBoundary description lines',
                             21: '* CuttingBoundary description lines',
                             22: '* CuttingBoundary description lines'},
                    'layers_start': {18: '* Layer description lines',
                                    19: '* Layer description lines',
                                    21: '* Layer description lines',
                                    22: '* Layer description lines'},
                    'layers_end': {18: '* Conformal Layer description lines',
                                    19: '* ConformalLayer description lines',
                                    21: '* ConformalLayer description lines',
                                    22: '* ConformalLayer description lines'}}
                                
        return sections[section][self.db_ver]

    def find_overlap_vias(self, layer):
        '''Find overlapping vias on a specified layer.
        When two vias are detected to be overlapping,
        the one that transvers less layers is selected to be removed.

        :param layer: Layer name to detect overlapping vias
        :type layer: str
        :return: Names of the overlapping vias
        :rtype: list[str]
        '''

        @dataclass
        class Vias:

            vias: List[Via] = field(default_factory=list)
            x: List[float] = field(default_factory=list)
            y: List[float] = field(default_factory=list)
            r: List[float] = field(default_factory=list)

            def __iter__(self):

                return iter((self.vias, self.x, self.y, self.r))

        upper_vias = Vias()
        lower_vias = Vias()

        for via in self.vias.values():
            if via.padstack is None:
                continue
            if via.upper_layer == layer:
                try:
                    pad = self.padstacks[via.padstack][via.upper_layer]
                except KeyError:
                    if None in self.padstacks[via.padstack]:
                        pad = self.padstacks[via.padstack][None]
                    else:
                        first_found_layer = list(self.padstacks[via.padstack].keys())[0]
                        pad = self.padstacks[via.padstack][first_found_layer]
                upper_vias.r.append(pad.tsv_radius)
                upper_vias.vias.append(via)
                upper_vias.x.append(via.x)
                upper_vias.y.append(via.y)
            elif via.lower_layer == layer:
                try:
                    pad = self.padstacks[via.padstack][via.lower_layer]
                except KeyError:
                    if None in self.padstacks[via.padstack]:
                        pad = self.padstacks[via.padstack][None]
                    else:
                        first_found_layer = list(self.padstacks[via.padstack].keys())[0]
                        pad = self.padstacks[via.padstack][first_found_layer]
                lower_vias.r.append(pad.tsv_radius)
                lower_vias.vias.append(via)
                lower_vias.x.append(via.x)
                lower_vias.y.append(via.y)

        overlap_vias = []
        for via_data in [upper_vias, lower_vias]:
            vias = np.array(via_data.vias)
            xvias = np.array(via_data.x)
            yvias = np.array(via_data.y)
            rvias = np.array(via_data.r)
            zeros = np.zeros(len(vias))

            for rvia, via in zip(rvias, vias):
                dist = np.sqrt((xvias - via.x)**2 + (yvias - via.y)**2)
                overlap_via = vias[(dist < (rvias + rvia)) & (dist > zeros)]
                if overlap_via.any():
                    overlap_vias.append(via.name)

        if overlap_vias:
            logger.info(f'Overlapping vias are found on layer {layer}')
        return list(set(overlap_vias))
    
    def delete_overlap_vias(self, ignore_layers=None, save=True):
        '''Delete overlapping vias from all layers except
        from the layer names specified in ignore_layers.

        :param ignore_layers: Layer names to ignore when detecting
        and deleting overlapping vias, defaults to None
        :type ignore_layers: list[str], optional
        '''

        layers = self.layer_names(verbose=False)
        ignore_layers = [] if ignore_layers is None else ignore_layers

        logger.info('Checking for overlapping vias...')
        vias_to_delete = []
        for layer in layers:
            if layer not in ignore_layers:
                vias_to_delete += self.find_overlap_vias(layer)

        if vias_to_delete:
            logger.info('Deleting overlapping vias... ')
            line_gen = self.extract_block('* Via description lines',
                                        '* WirebondDefination description lines')
            for idx, line in line_gen:
                if 'Via' in line:
                    via_name = line.split('::')[0]
                    if via_name in vias_to_delete:
                        self.lines[idx] = f'* {line}'

            if save:
                self.save()
            
        logger.info('Done')

    def find_pwr_gnd_shorts(self):
        '''Finds and removes shorts between ground and power pins
        as a result of merging two databases with a connector circuit.
        If shorts are found and removed, the original database is overwritten
        with a database without the shorts.
        '''

        conn_pin_type = {}
        pins = [node for node in self.nodes.values() if node.type == 'pin']
        for pin in pins:
            if pin.rail is not None and 'BRD' in pin.name:
                conn_pin_type[f"PCB_{pin.name.split('!!')[1]}"] = (
                                    pin.rail, self.net_names[pin.rail][1]
                                )
            elif pin.rail is not None and 'PKG' in pin.name:
                conn_pin_type[f"PKG_{pin.name.split('!!')[1]}"] = (
                                    pin.rail, self.net_names[pin.rail][1]
                                )

        try:
            line_gen = self.extract_block('.PartialCkt Connector',
                                            '* Component description lines')
            short = False
            del_lines = []
            logger.info('Connector shorts:') 
            for line_num, line in line_gen:
                if line[:2] == 'V_' or line[:2] == 'L_':
                    split_line = line.split()
                    pkg_pin, pcb_pin = split_line[1], split_line[2]
                    if pkg_pin not in conn_pin_type or pcb_pin not in conn_pin_type:
                        continue
                    #if (conn_pin_type[pkg_pin][1] != 'signal'
                    #    and conn_pin_type[pcb_pin][1] != 'signal'
                    #    and conn_pin_type[pkg_pin][1] != conn_pin_type[pcb_pin][1]):
                    if conn_pin_type[pkg_pin][1] != conn_pin_type[pcb_pin][1]:
                        logger.info(f"\tBoard {conn_pin_type[pcb_pin][1]} "
                                f"{conn_pin_type[pcb_pin][0]} "
                                f"and package {conn_pin_type[pkg_pin][1]} "
                                f"{conn_pin_type[pkg_pin][0]} "
                                f"pin {pcb_pin.split('_')[1]}")
                        del_lines.append(line_num)
                        short = True
            for cnt, line_num in enumerate(del_lines):
                del self.lines[line_num - cnt]
            if short:
                self.save()
            else:
                logger.info('\tNone')
        except ValueError:
            logger.info('Connector circuit could not be found')

    def match_nets(self, nets_to_merge='VXBR*', layers=None):
    
        if layers is None:
            for layer in self.layer_names(verbose=False):
                if 'bco' in layer.lower():
                    layers = [layer]
                    break
                    
        # Define polygon shapes that are not ground or the nets to merge
        polygons_by_layer = defaultdict(list)
        for shape in self.shapes.values():
            if  (shape.net_name is not None
                    and 'vss' not in shape.net_name.lower()
                    and 'gnd' not in shape.net_name.lower()
                    and shape.layer in layers
                    and self.net_names[shape.net_name][0] # Check if the rail is enabled
                    and shape.radius is None):
                coords = [[x, y] for x, y in zip(shape.xcoords, shape.ycoords)]
                polygons_by_layer[shape.layer].append((mpltPath.Path(coords),
                                                       shape.net_name))
        
        # Add nodes coordinates
        points = {layer_name: defaultdict(list) for layer_name in layers}
        for node in self.nodes.values():
            if (node.rail is not None
                    and 'vss' not in node.rail.lower()
                    and 'gnd' not in node.rail.lower()
                    and node.layer in layers
                    and self.net_names[node.rail][0] # Check if the rail is enabled
                    and self.net_names[node.rail][1] == 'power'):
                points[node.layer][node.rail].append([node.x, node.y])

        merge_cand = defaultdict(list)
        for layer in layers:
            for rail, points_to_check in points[layer].items():
                for (poly, net_name) in polygons_by_layer[layer]:
                    if (poly.contains_points(np.array(points_to_check)).any()
                            and rail != net_name):
                        if rail in nets_to_merge:
                            merge_cand[rail].append(net_name)
                        else:
                            merge_cand[net_name].append(rail)

        # Extract the matched nets
        merge_map = {}
        for net_to_merge, nets in merge_cand.items():
            if net_to_merge in nets_to_merge:
                for to_net in nets:
                    if nets.count(to_net) == 1:
                        merge_map[net_to_merge] = to_net
                        logger.info(f'\t{net_to_merge} is merged with {to_net}')

        return merge_map
    
    def merge_nets(self, fname_db=None, nets_to_merge='VXBR*', save=True):

        def net_in_line(nets, line):

            for net in nets:
                if net in line:
                    return True
            return False
        
        nets_to_merge = self.rail_names(nets_to_merge, enabled=True, verbose=False)
        logger.info('Merging nets... ')
        net_map = self.match_nets(nets_to_merge)
        if not net_map:
            logger.info(f'Nets to merge are not found. \n'
                        f'Check if the nets are enabled and classified as power and try again.')
            return
        
        logger.info('Net merging map is created... ', end='')
        backup_lines = deepcopy(self.lines)

        for idx, line in enumerate(self.lines.copy()):
            if net_in_line(nets_to_merge, line):
                for from_net, to_net in net_map.items():
                    if from_net in line:
                        if 'Color' in line and '-> PowerNets' not in line:
                            self.lines[idx] = ''
                        else:
                            self.lines[idx] = line.replace(from_net, to_net)
                        break

        if save and fname_db is not None:
            self.save(fname_db)
            self.lines = backup_lines
        elif save:
            self.save(fname_db)
        logger.info('Merging is done')

        return Database(os.path.join(self.path, self.name
                                    if fname_db is None else fname_db))

    '''
    def match_nets(self, nets_to_merge='VXBR*',
                    radius=1e-3, fname=None):

        # Find rails
        rails = {rail: set() for rail in self.rail_names(find_nets=nets_to_merge,
                                                            enabled=True,
                                                            verbose=False)}
        
        # Find all nodes with these net names:
        nodes = [node for node in self.nodes.values() if node.rail in rails]

        # Find all the other nodes
        other_nodes = [node for node in self.nodes.values() 
                            if node.rail is not None
                            and node.rail not in rails
                            and self.net_names[node.rail][0]] # The third 'and' checks if the net is enabled

        # Seperate nodes by layers
        nodes_by_layer = defaultdict(list)
        x_by_layer = defaultdict(list)
        y_by_layer = defaultdict(list)
        for node in other_nodes:
            nodes_by_layer[node.layer].append(node)
            x_by_layer[node.layer].append(node.x)
            y_by_layer[node.layer].append(node.y)

        for layer in nodes_by_layer.keys():
            nodes_by_layer[layer] = np.array(nodes_by_layer[layer])
            x_by_layer[layer] = np.array(x_by_layer[layer])
            y_by_layer[layer] = np.array(y_by_layer[layer])

        for node in nodes:
            found_nodes = nodes_by_layer[node.layer][(np.sqrt((x_by_layer[node.layer] - node.x)**2
                                                + (y_by_layer[node.layer] - node.y)**2) < radius)]
            found_net_names = list(set([node.rail for node in found_nodes]))
            for cutoff in np.arange(0.9, 0, -0.1):
                match = get_close_matches(node.rail, found_net_names, n=1, cutoff=cutoff)
                if match:
                    rails[node.rail].add(match[0])
                    break
            
        # Save as .csv file
        if fname is None:
            fname = os.path.join(self.path, f"{self.name.split('.')[0]}_mergemap.csv")
        
        if isinstance(nets_to_merge, str):
            nets_to_merge = [nets_to_merge]

        #final_matches = [[net.replace('*', '').replace('?', '') for net in nets_to_merge]]
        final_matches = []
        for rail_name, rail_matches in rails.items():
            final_matches.append([rail_name] + list(rail_matches))

        pd.DataFrame(final_matches).sort_values(0).to_csv(fname,
                                                            header=False,
                                                            index=False)
    '''

    def nets_to_signals(self):

        line_gen = self.extract_block('.NetList',
                                      '.EndNetList')

        for idx, line in line_gen:
            if '->' in line:
                split_line = line.split(' -> ')
                split_sym = '::' if '::' in line else ' '
                self.lines[idx] = (split_line[0]
                                    + split_sym
                                    + ' '.join(split_line[1].split(split_sym)[1:]))

    def generate_padstack(self, padstack_fname=None, save=True, unit='m'):

        padstack_fname = f'{self.name.split(".")[0]}_padstack.csv' \
                            if padstack_fname is None else padstack_fname

        df_padstacks = []
        for padstack_name in self.padstacks_in_design:
            for layer, padstack in self.padstacks[padstack_name].items():
                if layer is not None and layer != 'DefaultLibLayer':
                    df_padstacks.append(padstack.df_props(self.stackup[layer].conduct, unit).fillna(''))
                else:
                    df_padstacks.append(padstack.df_props(unit=unit).fillna(''))

        # Fix pad and drill sizes
        for df_padstack in df_padstacks:
            via_dim = df_padstack['Name'][0][1:].split('_')
            try:
                via_dim = [int(dim) for dim in via_dim[:3]]
            except ValueError:
                continue
            via_dim.sort()
            df_padstack.at[0, f'Outer diameter [{unit}]'] = via_dim[0]*1e-6*self.units[unit]
            if via_dim[0] > 100:
                df_padstack.at[0, f'Plating thickness [{unit}]'] = 18e-6*self.units[unit]
            else:
                df_padstack.at[0, f'Plating thickness [{unit}]'] = ''
            if df_padstack['Regular shape'][0] == 'circle':
                df_padstack.at[0, f'Regular width [{unit}]'] = via_dim[1]*1e-6*self.units[unit]
                df_padstack.at[0, f'Regular height [{unit}]'] = via_dim[1]*1e-6*self.units[unit]
            if df_padstack['Anti shape'][0] == 'circle':
                df_padstack.at[0, f'Anti width [{unit}]'] = via_dim[1]*1e-6*self.units[unit]
                df_padstack.at[0, f'Anti height [{unit}]'] = via_dim[1]*1e-6*self.units[unit]
                
        df_padstacks = pd.concat(df_padstacks).sort_values(by=['Name', 'Layer']).reset_index(drop=True)
        if save:
            df_padstacks.to_csv(os.path.join(self.path, padstack_fname), index=False)

        return df_padstacks

    def generate_stackup(self, stackup_fname=None, save=True, unit='m'):

        stackup_fname = f'{self.name.split(".")[0]}_stackup.csv' \
                            if stackup_fname is None else stackup_fname

        layer_data = {'Layer Name': [], f'Thickness [{unit}]': [], 'Material': [],
                        'Conductivity [S/m]': [], 'Fill-in Dielectric': [],
                        'Er': [], 'Loss Tangent': []}
        props = {'name': 'Layer Name', 'thickness': f'Thickness [{unit}]',
                    'material': 'Material', 'conduct': 'Conductivity [S/m]',
                    'fillin_dielec': 'Fill-in Dielectric', 'perm': 'Er',
                    'loss_tangent': 'Loss Tangent'}
        for layer in self.stackup.values():
            for data_type, data in layer.__dict__.items():
                try:
                    if data_type == 'thickness':
                        data = data*self.units[unit]
                    layer_data[props[data_type]].append(data)
                except KeyError:
                    pass

        df_stackup = pd.DataFrame(layer_data).reset_index(drop=True).fillna('')
        if save:
            df_stackup.to_csv(os.path.join(self.path, stackup_fname), index=False)

        return df_stackup

    def get_comp_name(self, part_name):

        name = [comp.name for comp in self.connects.values()
                    if comp.part == part_name]

        return name

    def get_part_name(self, comp_name):

        return self.connects[comp_name].part
        
    def load_db(self):

        logger.info(f'Loading {os.path.join(self.path, self.name)}')
        with open(os.path.join(self.path, self.name), 'rt') as f:
            self.lines = f.readlines()
        logger.info(f'{self.lines[1]}')
        try:
            self.db_ver = int(re.findall(r'\d+\.', self.lines[1])[0].strip('.'))
        except IndexError:
            logger.error(f'{self.lines[1]}. Unsupported version.')

    def extract_block(self, start_block=None, end_block=None):

        if start_block is None:
            start_block = 0
        else:
            try:
                start_idx = self.lines.index(f'{start_block}\n') + 1
            except ValueError:
                start_idx = self.lines.index(f'{start_block}') + 1
        if end_block is None:
            end_idx = len(self.lines)
        else:
            try:
                end_idx = start_idx + self.lines[start_idx:].index(f'{end_block}\n')
            except ValueError:
                end_idx = start_idx + self.lines[start_idx:].index(f'{end_block}')

        for line_num in range(start_idx, end_idx):
            yield (line_num, self.lines[line_num])

    def load_sinks(self):

        line_gen = self.extract_block('* PdcElem description lines',
                                      '* ConstraintDisc description lines')
        for _, line in line_gen:
            if '.Sink ' in line and 'IsForDCDC = 1' not in line:
                sink_props = {}
                block = []
                try:
                    sink_props['nom_voltage'] = float(line.split('NominalVoltage = ')[1].split()[0])
                except IndexError:
                    sink_props['nom_voltage'] = 0
                try:
                    sink_props['current'] = float(line.split('Current = ')[1].split()[0])
                except IndexError:
                    sink_props['current'] = 0
                sink_props['model'] = line.split('Model = ')[1].split()[0]
                sink_props['name'] = line.split('Name = ')[1].split()[0].strip('"')
                
                while '.EndSink' not in line:
                    block.append(line.strip())
                    _, line = next(line_gen)
                block = ' '.join(block)
                pos_nodes = block[block.index('.Pin Name = "Positive Pin"'):]
                pos_nodes = pos_nodes[:pos_nodes.index('.EndPin')]
                pos_nodes = pos_nodes.split(' .Node Name = ')[1:]
                sink_props['pos_nodes'] = [self.nodes[node.split('::')[0]]
                                           for node in pos_nodes]

                neg_nodes = block[block.index('.Pin Name = "Negative Pin"'):]
                neg_nodes = neg_nodes[:neg_nodes.index('.EndPin')]
                neg_nodes = neg_nodes.split(' .Node Name = ')[1:]
                sink_props['neg_nodes'] = [self.nodes[node.split('::')[0]]
                                            for node in neg_nodes]
                
                # Find the center of the sink based on the positive and negative nodes locations
                if sink_props['pos_nodes'] and ['neg_nodes']:
                    sink_props['x_center'] = np.mean([node.x
                                                      for node in sink_props['pos_nodes']
                                                                + sink_props['neg_nodes']])
                    sink_props['y_center'] = np.mean([node.y
                                                      for node in sink_props['pos_nodes']
                                                                + sink_props['neg_nodes']])

                    self.sinks[sink_props['name']] = Sink(sink_props)
                else:
                    logger.info(f'\tSink {sink_props["name"]} is not connected')

    def load_vrms(self):

        line_gen = self.extract_block('* PdcElem description lines',
                                      '* ConstraintDisc description lines')
        for _, line in line_gen:
            if '.VRM ' in line:
                vrm_props = {}
                block = []
                try:
                    vrm_props['nom_voltage'] = float(line.split('NominalVoltage = ')[1].split()[0])
                except IndexError:
                    vrm_props['nom_voltage'] = 0
                try:
                    vrm_props['sense_voltage'] = float(line.split('SenseVoltage = ')[1].split()[0])
                except IndexError:
                    vrm_props['sense_voltage'] = 0
                try:
                    vrm_props['out_current'] = float(line.split('OutputCurrent = ')[1].split()[0])
                except IndexError:
                    vrm_props['out_current'] = 0
                vrm_props['name'] = line.split('Name = ')[1].split()[0].strip('"')

                while '.EndVRM' not in line:
                    block.append(line.strip())
                    _, line = next(line_gen)
                block = ' '.join(block)
                
                for prop_name, node_type in zip(['Positive Sense Pin', 'Negative Sense Pin',
                                                'Positive Pin', 'Negative Pin'],
                                                ['pos_sense_nodes', 'neg_sense_nodes',
                                                 'pos_nodes', 'neg_nodes']):
                    
                    nodes = block[block.index(f'.Pin Name = "{prop_name}"'):]
                    nodes = nodes[:nodes.index('.EndPin')]
                    nodes = nodes.split(' .Node Name = ')[1:]
                    vrm_props[node_type] = [self.nodes[node.split('::')[0]]
                                             for node in nodes]

                self.vrms[vrm_props['name']] = Vrm(vrm_props)

    def load_nodes(self):

        line_gen = self.extract_block(self.version_handler('nodes_start'),
                                      self.version_handler('nodes_end'))

        self.db_x_top_right = -np.inf
        self.db_y_top_right = -np.inf
        self.db_x_bot_left = np.inf
        self.db_y_bot_left = np.inf
        node_props = {}
        for _, line in line_gen:
            if line[0] == '+' and 'AbsoluteRotation' in line:
                self.nodes[node_props['name']].rotation = (
                    float(line.split('AbsoluteRotation = ')[1].split()[0].strip())
                )
                continue
            if line[:4] != 'Node':
                continue
            node_props['name'] = line.split('::')[0].strip() if '::' in line else line.split()[0].strip()
            node_props['type'] = 'pin' if '!!' in node_props['name'] else 'node'
            try:
                node_props['rail'] = line.split('::')[1].split()[0].strip()
            except IndexError:
                node_props['rail'] = None
            node_props['x'] = float(line.split('X = ')[1].split('mm')[0])*1e-3
            node_props['y'] = float(line.split('Y = ')[1].split('mm')[0])*1e-3
            node_props['layer'] = line.split('Layer = ')[1].split(' ')[0].strip()

            self.db_x_bot_left = min(self.db_x_bot_left, node_props['x'])
            self.db_y_bot_left = min(self.db_y_bot_left, node_props['y'])
            self.db_x_top_right = max(self.db_x_top_right, node_props['x'])
            self.db_y_top_right = max(self.db_y_top_right, node_props['y'])
            try:
                node_props['padstack'] = line.split('PadStack = ')[1].split(' ')[0].strip()
            except IndexError:
                node_props['padstack'] = None
            try:
                node_props['rotation'] = float(line.split('AbsoluteRotation = ')[1].strip())
            except IndexError:
                node_props['rotation'] = 0
            
            self.nodes[node_props['name']] = Node(node_props)

        self.db_diag = np.sqrt((self.db_x_bot_left - self.db_x_top_right)**2
                        + (self.db_y_bot_left - self.db_y_top_right)**2)
        self.outline_scaler = (-2.6236*self.db_diag + 1.07227)

    def add_ports(self, *ports):

        for port in ports:
            self.ports[port.name] = port

    def load_ports(self):

        line_gen = self.extract_block('.Port', '* Extraction Setting description lines')

        sections = []
        properties = {}
        for _, line in line_gen:
            if line == '\n':
                continue
            if '+' not in line:
                if sections:
                    sections = ' '.join(sections)
                    properties['port_name'] = sections.split()[0]
                    
                    if 'PositiveTerminal' in sections and 'NegativeTerminal' in sections:
                        pos_nodes = sections.split('PositiveTerminal')[1].split('NegativeTerminal')[0].strip()
                        neg_nodes = sections.split('NegativeTerminal')[1].strip()
                    elif 'PositiveTerminal' in sections:
                        pos_nodes = sections.split('PositiveTerminal')[1].strip()
                        neg_nodes = ''
                    elif 'NegativeTerminal' in sections:
                        neg_nodes = sections.split('NegativeTerminal')[1].strip()
                        pos_nodes = ''
                    else:
                        pos_nodes = ''
                        neg_nodes = ''

                    properties['pos_nodes'] = [self.nodes[pos_node.split('.')[1].split('::')[0]]
                                                for pos_node in pos_nodes.split() if pos_nodes]
                    properties['neg_nodes'] = [self.nodes[neg_node.split('.')[1].split('::')[0]]
                                                for neg_node in neg_nodes.split() if neg_nodes]
                    
                    self.ports[properties['port_name']] = Port(properties)

                sections = [line.strip()]
                try:
                    properties['ref_z'] = float(line.split('RefZ = ')[1].split()[0])
                except IndexError:
                    properties['ref_z'] = 50.0
                try:
                    properties['port_width'] = float(line.split('Width = ')[1].split('mm')[0])*1e-3
                except IndexError:
                    properties['port_width'] = None
            else:
                sections.append(line.strip('+').strip())
                
    def load_layers(self):

        props = {'thickness': lambda l: float(l.split('Thickness = ')[1].split('u')[0])*1e-6,
                    'material': lambda l: l.split('Material = ')[1].split()[0],
                    'freq': lambda l: float(l.split('Frequency = ')[1].split()[0]),
                    'conduct': lambda l: float(l.split('Conductivity = ')[1].split()[0]),
                    'fillin_dielec': lambda l: l.split('DielectricMaterial = ')[1].split()[0],
                    'perm': lambda l: float(l.split('Permittivity = ')[1].split()[0]),
                    'loss_tangent': lambda l: float(l.split('LossTangent = ')[1].split()[0]),
                    'shape': lambda l: l.split('Shape = ')[1].split()[0]
                    }

        line_gen = self.extract_block(self.version_handler('layers_start'),
                                        self.version_handler('layers_end'))
        
        found_props = {}
        for _, line in line_gen:
            if line[0] == '+':
                for prop_name, prop in props.items():
                    try:
                        found_props[prop_name] = prop(line)
                    except IndexError:
                        pass
            elif 'Patch' in line or '.TrapezoidalTraceAngle' in line:
                continue
            else:
                if found_props:
                    self.stackup[found_props['name']] = Layer(found_props)
                    found_props = {}
                if not found_props:
                    found_props['name'] = line.split(' ')[0]
                    for prop_name, prop in props.items():
                        try:
                            found_props[prop_name] = prop(line)
                        except IndexError:
                            found_props[prop_name] = None

    def _poly_circle(self, xc, yc, radius, angle_res=10):

        angles = np.linspace(0, 2*np.pi, int(360/angle_res))
        return xc + radius*np.cos(angles), yc + radius*np.sin(angles)

    def load_shapes(self):

        line_gen = self.extract_block('* Shape description lines', self.version_handler('cuts'))
        shape_nets = set()

        poly_prop = {'name': None, 'net_name': None, 'layer_name': None,
                    'polarity': None, 'xcoords': [], 'ycoords': [],
                    'radius': None, 'xc': None, 'yc': None}

        shape_to_layer = {layer.name.split('$')[1]:layer.name
                            for layer in self.stackup.values()
                            if '$' in layer.name}
        for idx, line in line_gen:
            if '.Shape' in line:
                shape_layer = line.split()[1].split('pkgshape')[0]
                shape_layer = shape_to_layer.get(shape_layer.split('$')[1], shape_layer)
                
                logger.info(f'\t{shape_layer}')
                continue
            if line[0] == '+':
                it = iter(line.split()[1:])
                for coord in it:
                    poly_prop['xcoords'].append(float(coord[:-2])*1e-3)
                    poly_prop['ycoords'].append(float(next(it)[:-2])*1e-3)
            else:
                if poly_prop['name'] is not None:
                    if poly_prop['name'][:3] == 'Box' and poly_prop['net_name'] is None:
                        self.boxes[poly_prop['name']] = (Shape(poly_prop), idx)
                    else:
                        self.shapes[poly_prop['name']] = Shape(poly_prop)
                    poly_prop = {'name': None, 'net_name': None, 'layer_name': None,
                                    'polarity': None, 'xcoords': [], 'ycoords': [],
                                    'radius': None, 'xc': None, 'yc': None}
                if 'Circle' in line:
                    if '::' in line:
                        poly_prop['name'] = line.split('::')[0]
                        poly_prop['net_name'] = line.split('::')[1].split()[0][:-1]
                        poly_prop['polarity'] = line.split('::')[1].split()[0][-1:]
                    else:
                        poly_prop['name'] = line.split()[0][:-1]
                        poly_prop['net_name'] = None
                        poly_prop['polarity'] = line.split()[0][-1]
                    poly_prop['layer'] = shape_layer
                    poly_prop['radius'] = float(line.split()[-1][:-2])*1e-3
                    poly_prop['yc'] = float(line.split()[-2][:-2])*1e-3
                    poly_prop['xc'] = float(line.split()[-3][:-2])*1e-3
                    poly_prop['xcoords'], poly_prop['ycoords'] = (
                                            self._poly_circle(poly_prop['xc'],
                                            poly_prop['yc'], poly_prop['radius'])
                                            )
                    self.shapes[poly_prop['name']] = Shape(poly_prop)

                    shape_nets.add(poly_prop['net_name'])
                    poly_prop = {'name': None, 'net_name': None, 'layer_name': None,
                                    'polarity': None, 'xcoords': [], 'ycoords': [],
                                    'radius': None, 'xc': None, 'yc': None}
                    continue
                if poly_prop['name'] is None and ('Polygon' in line or 'Box' in line):
                    if '::' in line:
                        poly_prop['name'] = line.split('::')[0]
                        poly_prop['net_name'] = line.split('::')[1].split()[0][:-1]
                        poly_prop['layer'] = shape_layer
                        poly_prop['polarity'] = line.split('::')[1].split()[0][-1:]
                    else:
                        poly_prop['name'] = line.split()[0][:-1]
                        poly_prop['net_name'] = None
                        poly_prop['layer'] = shape_layer
                        poly_prop['polarity'] = line.split()[0][-1]

                    re_exp = r' -?\ *[0-9]+\.?[0-9]*(?:[Ee]\ *[-+]?\ *[0-9]+)?mm'
                    it = iter(re.findall(re_exp, line))
                    for coord in it:
                        try:
                            poly_prop['xcoords'].append(float(coord[:-2])*1e-3)
                            poly_prop['ycoords'].append(float(next(it)[:-2])*1e-3)
                        except ValueError:
                            pass
                    if 'Box' in line:
                        poly_coords_x = [poly_prop['xcoords'][0],
                                            poly_prop['xcoords'][0] + poly_prop['xcoords'][1],
                                            poly_prop['xcoords'][0] + poly_prop['xcoords'][1],
                                            poly_prop['xcoords'][0]]
                        poly_coords_y = [poly_prop['ycoords'][0],
                                            poly_prop['ycoords'][0],
                                            poly_prop['ycoords'][0] + poly_prop['ycoords'][1],
                                            poly_prop['ycoords'][0] + poly_prop['ycoords'][1]]
                        poly_prop['xcoords'] = poly_coords_x
                        poly_prop['ycoords'] = poly_coords_y

                    shape_nets.add(poly_prop['net_name'])

    def load_nets(self, color_scheme='powersi'):

        non_nets = ['RiseTime', 'PowerNets', 'GroundNets', 'Color']
        line_gen = self.extract_block('.NetList', '.EndNetList')

        clr_cycle = cycle(Category20[20])
        net_type = 'signal'
        branch_unselected = (False, None)
        for _, line in line_gen:
            if '-> PowerNets' in line:
                net_type = 'power'
            if '-> GroundNets' in line:
                net_type = 'ground'
            if 'BranchUnselected' in line:
                branch_unselected = (True, line.split()[0].split('::')[0].strip())
            line = line.strip()
            if not line:
                continue
            if color_scheme == 'powersi':
                try:
                    clr = line.split('Color = ')[1].split()[0].lower().replace('0x', '#')
                except IndexError:
                    clr = '#282c34'
            elif color_scheme == 'thinkpi':
                clr = next(clr_cycle)
            
            if 'Unselected' in line:
                net_name = line.split()[0] if '->' in line else line.split('::')[0]
                current_clr = '#282c34'
                self.net_names[net_name] = (0, net_type)
            else:
                net_name = line.split()[0].split('||')[0]
                current_clr = clr
                if branch_unselected[0] and net_name.startswith(branch_unselected[1]):
                    self.net_names[net_name] = (0, net_type)
                else:
                    self.net_names[net_name] = (1, net_type)
            
            if net_name in non_nets:
                del self.net_names[net_name]
            else:
                self.shape_clr[net_name] = (current_clr, clr)
        self.shape_clr[None] = ('#282c34', '#282c34')

    def load_vias(self):

        via_prop = {}
        line_gen = self.extract_block('* Via description lines',
                                        '* WirebondDefination description lines')
        for _, line in line_gen:
            if line[0] == '*':
                continue
            if 'Via' in line:
                via_prop['name'] = line.split('::')[0]
                try:
                    via_prop['net_name'] = line.split('::')[1].split()[0]
                    via_prop['upper_node'] = line.split('UpperNode = ')[1].split('::')[0]
                    via_prop['upper_layer'] = self.nodes[via_prop['upper_node']].layer
                    via_prop['lower_node'] = line.split('LowerNode = ')[1].split('::')[0]
                    via_prop['lower_layer'] = self.nodes[via_prop['lower_node']].layer
                    via_prop['padstack'] = line.split('PadStack = ')[1].split()[0].strip()
                    self.padstacks_in_design.add(via_prop['padstack'])
                    via_prop['x'] = self.nodes[via_prop['upper_node']].x
                    via_prop['y'] = self.nodes[via_prop['upper_node']].y

                    self.vias[via_prop['name']] = Via(via_prop)
                except (IndexError, KeyError):
                    pass

    def load_padstacks(self):

        parse = PadstackParser(self.padstacks)
        phrases = {'.PadStackDef': parse.padstack_def,
                    '.PadDef': parse.pad_def,
                    'Regular Circle': parse.pad_shape,
                    'Anti Circle': parse.pad_shape,
                    'Regular Square': parse.pad_shape,
                    'Anti Square': parse.pad_shape,
                    'Regular Polygon': parse.polygon,
                    'Anti Polygon': parse.polygon,
                    '+': parse.polygon,
                    'Regular Box': parse.pad_shape,
                    'Anti Box': parse.pad_shape,
                    'Regular RoundedRect_X': parse.pad_shape,
                    'Anti RoundedRect_X': parse.pad_shape,
                    'Regular RoundedRect_Y': parse.pad_shape,
                    'Anti RoundedRect_Y': parse.pad_shape,
                    'Regular n-Poly': parse.pad_shape,
                    '.EndPadDef': parse.end_pad_def,
                    '.EndPadStackDef': parse.end_padstack_def}
        
        line_gen = self.extract_block('* PadStack collection description lines',
                                        '* CoupleLine description lines')

        for _, line in line_gen:
            if line == '\n':
                continue
            if 'Regular' in line or 'Anti' in line:
                phrase = ' '.join(line.split()[:2])
            else:
                phrase = line.split()[0]
            phrases[phrase](line)
    
    def load_components(self):

        parse = ComponentParser(self.parts, self.components, self.connects)
        line_gen = self.extract_block('* Component description lines',
                                        '.EndCompCollection')

        # Scan lines and group connects, components, and parts
        groups = {'.Part': [], '.Connect': [], '.Component': []}
        sections = []
        group_type = None
        for _, line in line_gen:
            if line == '\n' or line[0] == '*' or '.EndC' in line:
                if sections and group_type is not None:
                    groups[group_type].append(' '.join(sections))
                continue
            if '.Part' in line or '.Component' in line or '.Connect' in line:
                if sections and group_type is not None:
                    groups[group_type].append(' '.join(sections))
                sections = [line.strip()]
                group_type = line.split()[0]
            else:
                sections.append(line.strip('+').strip())

        for group_name, group in groups.items():
            for line in group:
                parse.item_select[group_name](line)

        # Find parts without outline and construct an outline box
        for part_name, part in self.parts.copy().items():
            if part.x_outline is None and part.y_outline is None:
                try:
                    comp_name = self.get_comp_name(part_name)[0]
                    comp_nodes = [self.nodes[node] for node in self.connects[comp_name].nodes]
                    x_top_left = sorted(comp_nodes, key=attrgetter('x'))[0].x
                    y_top_left = sorted(comp_nodes, key=attrgetter('y'))[-1].y
                    x_bot_right = sorted(comp_nodes, key=attrgetter('x'))[-1].x
                    y_bot_right = sorted(comp_nodes, key=attrgetter('y'))[0].y
                except (IndexError, KeyError):
                    continue
                x_length = x_bot_right - x_top_left
                y_length = y_top_left - y_bot_right
                diag_length = np.sqrt(x_length**2 + y_length**2)
                extend_diag = self.outline_scaler*diag_length/2
                extend_length = extend_diag/np.sqrt(2)
                if y_length > 0:
                    self.parts[part_name].x_outline = [x_length + extend_length]
                    self.parts[part_name].y_outline = [y_length + extend_length]
                else:
                    self.parts[part_name].x_outline = [y_length + extend_length]
                    self.parts[part_name].y_outline = [x_length + extend_length]

    def load_traces(self):

        props = {'name': lambda l, delim: l.split(delim)[0],
                    'rail': lambda l, delim: l.split(delim)[1].split()[0],
                    'start_node': lambda l, delim: l.split('StartingNode = ')[1].split(delim)[0].split()[0],
                    'end_node': lambda l, delim: l.split('EndingNode = ')[1].split(delim)[0].split()[0],
                    'width': lambda l, _: float(l.split('Width = ')[1].split('mm')[0])*1e-3}

        line_gen = self.extract_block('* Trace description lines',
                                        '* Via description lines')
        
        line_str = []
        properties = {}
        for _, line in line_gen:
            if line[0] == '+':
                line_str.append(line[1:].strip('\t').strip())
            else:
                if line_str:
                    line_str = ' '.join(line_str)
                    delim = '::' if '::' in line_str else ' '
                    for prop_name, prop_func in props.items():
                        try:
                            properties[prop_name] = prop_func(line_str, delim)
                        except IndexError:
                            properties[prop_name] = None

                    if properties['start_node'] is None:
                        line_str = []
                        properties = {}
                        continue
                    else:
                        properties['layer'] = self.nodes[properties['start_node']].layer
                    if delim == ' ':
                        properties['rail'] = None
                    self.traces[properties['name']] = Trace(properties)
                    line_str = []
                    properties = {}
                line_str.append(line.strip())

    def _find_ports_center(self):

        all_nodes = []
        for port in self.ports.values():
            pos_nodes = [self.nodes[node] for node in port.pos_nodes]
            neg_nodes = [self.nodes[node] for node in port.neg_nodes]
            port_nodes = pos_nodes + neg_nodes
            all_nodes += port_nodes
            port.x_center = (min(port_nodes, key=attrgetter('x')).x
                            + max(port_nodes, key=attrgetter('x')).x)/2
            port.y_center = (min(port_nodes, key=attrgetter('y')).y
                            + max(port_nodes, key=attrgetter('y')).y)/2

        # Find coordinates of the most top left and bottom right db area
        self.box_x1 = min(all_nodes, key=attrgetter('x')).x
        self.box_y1 = max(all_nodes, key=attrgetter('y')).y
        self.box_x2 = max(all_nodes, key=attrgetter('x')).x
        self.box_y2 = min(all_nodes, key=attrgetter('y')).y

    def find_comps(self, comp_names=None, verbose=True, obj=None):
        '''Find components based on wildcard search.

        :param comp_names: Wildcard lookup of components, defaults to None
        :type comp_names: str or a list of str, optional
        :param verbose: If True prints the found names, otherwise return the found components,
        defaults to True
        :type verbose: bool, optional
        :param obj: Any object containing searchable data by keys, defaults to None
        :type obj: dict
        :return: If verbose is False returns a list of component objects
        :rtype: :class:`speed.ComponetConnection()`
        '''

        obj = self.connects if obj is None else obj
        if comp_names is None:
            comps = list(obj.keys())
        else:
            if isinstance(comp_names, str):
                comp_names = [comp_names]
            comps = []
            for find_comp_name in comp_names:
                match = re.compile(f"^({find_comp_name.lower().replace('*', '.*').replace('?', '.?')})$")
                for comp_name, comp in obj.items():
                    if re.search(match, comp_name.lower()):
                        comps.append(comp)

        if verbose:
            for comp in comps:
                print(comp.name)
        else:
            return comps

    def report(self, nets, report_fname, cap_finder='C*'):
        '''Create a general report based on a loaded database.
        The report includes general information, as well as
        information about layers, ports, caps, and pins. 

        :param nets: Net names for which the report is created
        String can include wildcards such as '*' and '?'.
        :type nets: str or a list of str
        :param report_fname: Report file name
        :type report_fname: str
        :param cap_finder: Wildcard lookup of capacitors, defaults to 'C*'
        :type cap_finder: str or list of str, optional
        :return: Dictionary with all gathered information 
        :rtype: dict
        '''

        report_data = {}
        found_nets = self.rail_names(nets, verbose=False)

        with open(report_fname, 'wt', encoding="utf-8") as f:
            f.write('General Information\n')
            f.write(f"{'-'*len('General Information')}\n")
            f.write(f"{datetime.now().strftime('%m/%d/%Y %H:%M:%S')}\n")
            f.write(f"{os.path.join(self.path, self.name)}\n{self.lines[1]}")
            x = (self.db_x_top_right - self.db_x_bot_left)*1e3
            y = (self.db_y_top_right - self.db_y_bot_left)*1e3
            area = x*y
            f.write(f"Approximated area: x = {x:.3f} mm, "
                    f"y = {y:.3f} mm, area = {area:.3f} mm^2\n")

            f.write('\nLayers\n')
            f.write('------\n')
            for layer_name in self.layer_names(verbose=False):
                f.write(f'{layer_name}\n')

            # Find port information
            port_data = {'Name': [], 'Layer': [], 'Rail Name': [],
                        'Width [mm]': [], 'Ref Z [Ohm]': [],
                        'Positive Nodes': [], 'Negative Nodes': []}
            for port_name in self.port_names(verbose=False):
                try:
                    port_data['Layer'].append(self.ports[port_name].layers[0])
                except IndexError:
                    logger.info(f'Port {port_name} is not properly connected')
                    continue
                port_data['Name'].append(port_name)
                port_data['Rail Name'].append(self.ports[port_name].pos_rails[0])
                port_data['Width [mm]'].append('None' if self.ports[port_name].width is None else self.ports[port_name].width*1e3)
                port_data['Ref Z [Ohm]'].append(self.ports[port_name].ref_z)
                port_data['Positive Nodes'].append(int(len(self.ports[port_name].pos_nodes)))
                port_data['Negative Nodes'].append(int(len(self.ports[port_name].neg_nodes)))
                
            if port_data['Name']:
                f.write('\nPorts\n')
                f.write('-----\n')
                report_data['ports'] = pd.DataFrame(port_data)
                f.write(report_data['ports'].to_string(index=False))

            # Find cap information
            comps = self.find_comps(comp_names=cap_finder, verbose=False)
            cap_data = {'Name': [], 'Layer': [], 'Rail Name': [], 'Description': []}
            cap_by_type = defaultdict(list)
            cap_by_rail = defaultdict(list)
            for comp in comps:
                # Check that the component is connected
                if comp.nodes:
                    comp_rail = self.nodes[comp.nodes[0]].rail
                    comp_layer = self.nodes[comp.nodes[0]].layer
                else:
                    comp_rail = 'unknown'
                    comp_layer = 'unknown'
                if comp_rail in found_nets or comp_rail == 'unknown':
                    cap_data['Name'].append(comp.name)
                    cap_data['Layer'].append(comp_layer)
                    cap_data['Rail Name'].append(comp_rail)
                    cap_data['Description'].append(comp.part)
                    cap_by_type[comp.part].append(comp.name)
                    cap_by_rail[comp_rail].append(comp.name)

            if cap_data['Name']:
                report_data['caps'] = pd.DataFrame(cap_data)
                caps_count_by_type = {'Capacitor Type': [], 'Count': []}
                f.write('\n\nDecoupling Capacitors\n')
                f.write('---------------------\n')
                f.write(report_data['caps'].to_string(index=False))
                f.write('\n\nCounts by part type\n')
                f.write('-------------------\n')
                for cap_type, cap_names in cap_by_type.items():
                    f.write(f"{len(cap_names)}\t{cap_type} {' '.join(cap_names)}\n")
                    caps_count_by_type['Capacitor Type'].append(cap_type)
                    caps_count_by_type['Count'].append(len(cap_names))
                report_data['caps_count_by_type'] = pd.DataFrame(caps_count_by_type)

                caps_count_by_rail = {'Rail Name': [], 'Count': []}
                f.write('\nCounts by rail\n')
                f.write('--------------\n')
                for rail, cap_names in cap_by_rail.items():
                    f.write(f"{len(cap_names)}\t{rail} {' '.join(cap_names)}\n")
                    caps_count_by_rail['Rail Name'].append(rail)
                    caps_count_by_rail['Count'].append(len(cap_names))
                report_data['caps_count_by_rail'] = pd.DataFrame(caps_count_by_rail)

            # Find pin information
            pin_data = defaultdict(list)
            conn_ckts = self.find_comps(comp_names=['*U*', '*A*'], verbose=False)
            
            for conn_ckt in conn_ckts:
                for node_name in self.connects[conn_ckt.name].nodes:
                    if self.nodes[node_name].rail in found_nets:
                        pin_data[(self.nodes[node_name].rail,
                                    self.nodes[node_name].layer,
                                    conn_ckt.name,
                                    self.connects[conn_ckt.name].part)].append(self.nodes[node_name])

            sorted_pins = {'Pin #': [], 'Rail Name': [],
                            'Layer': [], 'Ref ID': [], 'Part Name': []}
            for pin_info, pins in pin_data.items():
                sorted_pins['Pin #'].append(len(pins))
                sorted_pins['Rail Name'].append(pin_info[0])
                sorted_pins['Layer'].append(pin_info[1])
                sorted_pins['Ref ID'].append(pin_info[2])
                sorted_pins['Part Name'].append(pin_info[3])

            if sorted_pins['Pin #']:
                f.write('\nPins\n')
                f.write('----\n')
                report_data['pins'] = pd.DataFrame(sorted_pins).sort_values('Rail Name').reset_index(drop=True)
                f.write(report_data['pins'].to_string(index=False))
                f.write('\n')

            # Find shapes area utilization
            poly_areas = defaultdict(int)
            for poly in self.shapes.values():
                if poly.net_name in found_nets:
                    poly_area = poly.area
                    if poly.polarity == '-':
                        poly_area = -poly_area
                    poly_areas[(poly.net_name, poly.layer)] += poly_area*1e6
                    
            sorted_poly = {'% Utilization': [], 'Rail Name': [], 'Layer': []}
            for poly_info, poly_area in poly_areas.items():
                sorted_poly['% Utilization'].append((poly_areas[poly_info]/area)*100)
                sorted_poly['Rail Name'].append(poly_info[0])
                sorted_poly['Layer'].append(poly_info[1])
            report_data['metal_util'] = pd.DataFrame(sorted_poly).sort_values('Rail Name').reset_index(drop=True)
            if sorted_poly['% Utilization']:
                f.write('\nMetal area utilization\n')
                f.write('----------------------\n')
                f.write(report_data['metal_util'].to_string(index=False))
                f.write('\n')

            # Find via information
            via_info = defaultdict(int)
            for via in self.vias.values():
                if via.net_name in found_nets:
                    via_info[(via.net_name, via.lower_layer, via.upper_layer)] += 1

            
            via_sorter = {'Count': [], 'Rail Name': [], 'Lower Layer': [], 'Upper Layer': []}
            for via, count in via_info.items():
                via_sorter['Count'].append(count)
                via_sorter['Rail Name'].append(via[0])
                via_sorter['Lower Layer'].append(via[1])
                via_sorter['Upper Layer'].append(via[2])
            report_data['vias'] = pd.DataFrame(via_sorter).sort_values('Rail Name').reset_index(drop=True)
            if via_sorter['Count']:
                f.write('\nVia count\n')
                f.write('---------\n')
                f.write(report_data['vias'].to_string(index=False))
                f.write('\n')

        return report_data

    def get_conn(self, side):
        '''Find connector object based on '*A*' or '*U*' reference designators.
        Second creterion is to find a component with the largest amount of pins.
        
        :param side: Accepts only 'bottom' (for package) or 'top' (for board) parameters.
        :type side: str
        :return: Connector object
        :rtype: :class:`speed.ComponetConnection()`
        '''

        layer_names = self.layer_names(verbose=False)
        if side.lower() == 'bottom':
            check_layer = layer_names[-1]
        elif side.lower() == 'top':
            check_layer = layer_names[0]
        else:
            raise ValueError("side can only accept 'bottom' or 'top' but got {side}.")
        comps = [(comp, len(comp.nodes))
                    for comp in self.find_comps(['*U*', '*A*'], verbose=False)
                    if comp.nodes
                    and comp.nodes[0] in self.nodes
                    and self.nodes[comp.nodes[0]].layer == check_layer]

        if comps:
            conn = max(comps, key=itemgetter(1))
            return conn[0]
        else:
            return None

    def rail_names(self, find_nets=None, enabled=None, verbose=True):

        if find_nets is None:
            nets = self.net_names
        else:
            if isinstance(find_nets, str):
                find_nets = [find_nets]
            nets = {}
            for net in find_nets:
                match = re.compile(f"^({net.lower().replace('*', '.*').replace('?', '.?')})$")
                for name, sel in self.net_names.items():
                    if re.search(match, name.lower()):
                        nets[name] = sel

        net_names = []
        if nets:
            for net_name, select in nets.items():
                if enabled is None:
                    net_names.append(net_name)
                    status = 'All net names:'
                elif enabled and select[0] == 1:
                    net_names.append(net_name)
                    status = 'Enabled net names:'
                elif not enabled and select[0] == 0:
                    net_names.append(net_name)
                    status = 'Disabled net names:'
        else:
            status = 'None found'

        if verbose:
            print(status)
            for net_name in net_names:
                print(f'\t{net_name}')
        else:
            return net_names
        
    def port_names(self, verbose=True):

        names = []
        for port_name in self.ports.keys():
            names.append(port_name)

        if verbose:
            print('Port names:')
            for name in names:
                print(f'\t{name}')
        else:
            return names

    def padstack_names(self, verbose=True):

        names = list(self.padstacks.keys())

        if verbose:
            print('Padstack names:')
            for name in names:
                print(f'\t{name}')
        else:
            return names

    def box_names(self, verbose=True):

        boxes = [box[0].name for box in self.boxes.values()]

        if verbose:
            print('Box names:')
            for box in boxes:
                print(f'\t{box}')
        else:
            return boxes

    def layer_names(self, verbose=True):

        signal_layers = []
        for layer in self.stackup.values():
            if layer.is_signal:
                signal_layers.append(layer.name)
        
        if verbose:
            print('Database signal layers:')
            for layer in signal_layers:
                print(f'\t{layer}')
        else:
            return signal_layers

    def component_names(self, verbose=True):

        comps = []
        for comp in self.connects.values():
            comps.append((comp.name, comp.part))

        if verbose:
            print('Component and part names:')
            for comp_name, part_name in comps:
                print(f'\t{comp_name}, {part_name}')
        else:
            return comps

    def save(self, fname=None):

        fname = self.name if fname is None else fname
        if not os.path.dirname(fname):
            fname = os.path.join(self.path, fname)

        with open(fname, 'wt') as f:
            f.writelines(self.lines)

    def load_data(self):

        load_sections = {'layers': self.load_layers, 'nets': self.load_nets,
                        'nodes': self.load_nodes, 'ports': self.load_ports,
                        'shapes': self.load_shapes, 'padstacks': self.load_padstacks,
                        'vias': self.load_vias, 'components': self.load_components,
                        'traces': self.load_traces, 'sinks': self.load_sinks,
                        'vrms': self.load_vrms, 'plots': self.prepare_plots
                    }
        
        self.load_db()
        for flag_name, to_load in self.load_flags.items():
            if to_load:
                logger.info(f'Loading {flag_name}... ')
                try:
                    load_sections[flag_name]()
                except ValueError:
                    logger.info('None found')
                    continue
                logger.info('Done')

    def load_material(self, fname):

        materials = defaultdict(dict)
        path = Path(fname)
        lines = path.read_text()
        lines = '\n' + lines.replace('Specific ', 'Specific_')
        idxs = [m.start() for m in re.finditer(r'\n\.\D', lines)]
        
        for start_idx, end_idx in zip(idxs[::2], idxs[1::2]):
            section = lines[start_idx:end_idx].split('\n')[1:]
            model_type = section[0].split()[0].replace('.', '').replace('Model', '')
            material_name = section[0].split()[1]
            materials[material_name][model_type] = {}
            headers = section[1][1:].split()
            for header in headers:
                materials[material_name][model_type][header.replace('_', ' ')] = []
            for data_line in section[2:]:
                for header, data in zip(headers, data_line.split()):
                    materials[material_name][model_type][header.replace('_', ' ')].append(data)

        return materials

    def save_material(self, fname, materials):

        with open(fname, 'wt') as f:
            for material_name, material_types in materials.items():
                for model_name, props in material_types.items():
                    f.write(f'.{model_name}Model {material_name}\n')
                    f.write(f"*{' '.join(list(props.keys()))}\n")
                    f.write(f'{pd.DataFrame(props).to_string(header=False, index=False)}\n')
                    f.write(f'.End{model_name}Model\n\n')

