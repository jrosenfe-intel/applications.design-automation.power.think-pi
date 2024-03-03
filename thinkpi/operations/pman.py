from pathlib import Path
from operator import itemgetter
import re
from collections import defaultdict

import numpy as np
from sklearn.cluster import KMeans
import pandas as pd
import matplotlib.path as mpltPath

from thinkpi.operations import speed as spd
from thinkpi.flows import tasks
from thinkpi import logger


class PortGroup():

    def __init__(self, ports_db, ports=None):

        if isinstance(ports_db, str):
            self.db = spd.Database(ports_db)
            self.db.load_data()
        else:
            self.db = ports_db

        self.ports = list(self.db.ports.values()) \
                            if ports is None else ports
        self.group_info = {}

    @property
    def num_ports(self):

        return (len(self.ports))

    def port_names(self, verbose=True):

        port_names = []
        for port in self.ports:
            port_names.append(port.name)

        if verbose:
            print('Port names:')
            for port_name in port_names:
                print(f'\t{port_name}')
        else:
            return port_names

    def _find_nodes(self, to_db):

        port_by_layer = defaultdict(list)
        for port in self.ports:
            port_by_layer[port.layers[0]].append(port)

        for ports in port_by_layer.values():
            layer = ports[0].layers[0]
            nodes = np.array([node for node in to_db.nodes.values()
                                if (node.layer.replace('PKG', '').replace('BRD', '')
                                    == layer.replace('PKG', '').replace('BRD', '')
                                    and node.rail is not None
                                    and to_db.net_names[node.rail][0]) # Check if the net is enabled
                            ]
                        )
            nodes_x = np.array([node.x for node in nodes])
            nodes_y = np.array([node.y for node in nodes])

            yield nodes_x, nodes_y, nodes, ports
            
    def copy(self, dx, dy, to_db=None,
                adj_win=(1e-5, 1e-5, 1e-5, 1e-5),
                ref_z=None, force=False):
        
        if to_db is None:
            to_db = self.db
        
        gen = self._find_nodes(to_db)
        coppied_ports = []
        for nodes_x, nodes_y, nodes, ports in gen:
            for port in ports:
                coppied_ports.append(
                        port.cart_copy(dx, dy, (nodes_x, nodes_y, nodes),
                                        adj_win, ref_z, force)
                    )

        return PortGroup(to_db, coppied_ports)

    def rotate_copy(self, x_src, y_src, x_dst, y_dst, rot_angle,
                        to_db=None,
                        adj_win=(1e-5, 1e-5, 1e-5, 1e-5),
                        ref_z=None, force=False):
        
        if to_db is None:
            to_db = self.db

        gen = self._find_nodes(to_db)
        coppied_ports = []
        for nodes_x, nodes_y, nodes, ports in gen:
            for port in ports:
                coppied_ports.append(
                        port.rotate_copy(x_src, y_src, x_dst, y_dst,
                                        rot_angle, (nodes_x, nodes_y, nodes),
                                        adj_win, ref_z, force)
                    )

        return PortGroup(to_db, coppied_ports)

    def mirror_copy(self, x_src, y_src, x_dst, y_dst,
                        to_db=None,
                        adj_win=(1e-5, 1e-5, 1e-5, 1e-5),
                        ref_z=None, force=False):

        if to_db is None:
            to_db = self.db

        gen = self._find_nodes(to_db)
        coppied_ports = []
        for nodes_x, nodes_y, nodes, ports in gen:
            for port in ports:
                coppied_ports.append(
                        port.mirror_copy(x_src, y_src, x_dst, y_dst,
                                        (nodes_x, nodes_y, nodes),
                                        adj_win, ref_z, force)
                    )

        return PortGroup(to_db, coppied_ports)

    def array_copy(self, x_src, y_src,
                    x_horz, y_vert,
                    nx, ny,
                    to_db=None,
                    adj_win=(1e-5, 1e-5, 1e-5, 1e-5),
                    ref_z=None, force=False
                    ):

        coppied_ports = []
        dx = x_horz - x_src
        dy = y_vert - y_src
        if to_db is None:
            to_db = self.db
            cnt_start = 1
        else:
            cnt_start = 0
        for n_vert in range(ny + 1):
            for n_horiz in range(cnt_start, nx + 1):
                coppied_ports += self.copy(dx*n_horiz, dy*n_vert,
                                                to_db,
                                                adj_win, ref_z,
                                                force).ports
            cnt_start = 0

        return PortGroup(to_db, coppied_ports)

    def _is_forced_nodes(self, nodes):

        for node in nodes:
            if 'tpi' in node.name:
                return True
        return False

    def _nodes_in_box(self, x1, y1, x2, y2, nodes: np.array):

        nodes_x, nodes_y, nodes = nodes

        return nodes[(nodes_x >= x1)
                        & (nodes_x <= x2)
                        & (nodes_y >= y1)
                        & (nodes_y <= y2)]

    def _poly_contains(self, polygons, xp, yp):

        for polygon in polygons:
            if polygon.contains_point((xp, yp)):
                return True
        
        return False

    def _create_3D_port(self, port_props, x_center, y_center, layer):

        # Find all shapes on the grounds layer
        shapes = [shape for shape in self.db.shapes.values()
                    if shape.layer == layer
                    and shape.polarity == '+'
                    and ('vss' in shape.net_name.lower()
                    or 'gnd' in shape.net_name.lower())]
        # Define all found shapes
        polygons = []
        for shape in shapes:
            coords = [[x, y] for x, y in zip(shape.xcoords, shape.ycoords)]
            polygons.append(mpltPath.Path(coords))
        
        # Find the closest positive node to the cluster centroid
        pnodes_dist = []
        for pos_node in port_props['pos_nodes']:
            pnodes_dist.append(
                                (np.sqrt((pos_node.x - x_center)**2
                                + (pos_node.y - y_center)**2),
                                pos_node)
                        )

        pnodes_dist = sorted(pnodes_dist, key=itemgetter(0))

        for node_dist, node in pnodes_dist:
            # Store the positive node with the shortest distance to the centroid
            port_props['pos_nodes'] = [node]
            x_p, y_p = port_props['pos_nodes'][0].x, port_props['pos_nodes'][0].y

            # Find the two closest negative nodes to the positive node from above
            nnodes_dist = []
            for neg_node in port_props['neg_nodes']:
                nnodes_dist.append(
                                    (np.sqrt((neg_node.x - x_p)**2
                                    + (neg_node.y - y_p)**2),
                                    neg_node)
                            )
            min_dist = min(nnodes_dist, key=itemgetter(0))
            x_n1, y_n1 = min_dist[1].x, min_dist[1].y
            #dist = sorted(nnodes_dist, key=itemgetter(0))
            #x_n1, y_n1 = dist[0][1].x, dist[0][1].y
           
            
            # Find the next ground node closest to the first found above
            nnodes_dist = []
            for neg_node in port_props['neg_nodes']:
                nnodes_dist.append(
                                    (np.sqrt((neg_node.x - x_n1)**2
                                    + (neg_node.y - y_n1)**2),
                                    neg_node)
                            )
            nnodes_dist = sorted(nnodes_dist, key=itemgetter(0))

            if len(nnodes_dist) > 1:
                #x_n2, y_n2 = dist[1][1].x, dist[1][1].y
                
                # Use second node since first node is the same as the node above
                x_n2, y_n2 = nnodes_dist[1][1].x, nnodes_dist[1][1].y

                # Find line slopes m of the negative and positive nodes found above
                try:
                    m_n = (y_n1 - y_n2)/(x_n1 - x_n2)
                    m_p = -1/m_n # Perpendicular to the negative line slope

                    # Find intersaction point between the positive node line and negative node line
                    # This will be the new negative node for the 3D port
                    x_i = (y_n1 - m_n*x_n1 - y_p + m_p*x_p)/(m_p - m_n)
                    y_i = m_p*x_i + y_p - m_p*x_p
                except ZeroDivisionError:
                    if x_n1 == x_n2:
                        x_i = x_n1
                        y_i = y_p
                    else: # that means m_p == m_n
                        x_i = x_p
                        y_i = y_n1

                # Check if the new node is within some ground polygon
                if self._poly_contains(polygons, x_i, y_i):
                    break
                else:
                    x_i, y_i = None, None
                    new_node = nnodes_dist[0][1]
            else:
                x_i, y_i = None, None
                new_node = nnodes_dist[0][1]
        
        # Create a new ground node at (x_i, y_i) if needed
        if x_i is not None and y_i is not None:
            node_props = {}
            node_props['name'] = f'{nnodes_dist[0][1].name}_tpi{spd.Node.idx}'
            spd.Node.idx += 1
            node_props['type'] = 'node'
            node_props['rail'] = nnodes_dist[0][1].rail
            node_props['x'], node_props['y'] = x_i, y_i
            node_props['layer'] = nnodes_dist[0][1].layer
            node_props['rotation'] = nnodes_dist[0][1].rotation
            node_props['padstack'] = None

            new_node = spd.Node(node_props)
            self.db.nodes[new_node.name] = new_node
        port_props['neg_nodes'] = [new_node]
        
        # A heuristic approach to calculate 3D port width
        # by taking 1/3 of the distance between positive and negative nodes as the length
        # The recommended width of a 3D port is W/L = 0.5 to 2
        # For C4 bumps we will use a ratio of W/L = 2
        port_props['port_width'] = (1/3)*np.sqrt(
                                (port_props['pos_nodes'][0].x - port_props['neg_nodes'][0].x)**2
                                + (port_props['pos_nodes'][0].y - port_props['neg_nodes'][0].y)**2
                            )*2

        return port_props

    def reduce_ports(self, layer, num_ports, select_ports=None):
        '''Reduce given ports on a given layer down to num_ports
        number of ports. The original ports that are reduced will be
        removed and replaced by the reduced ports.

        :param layer: Layer on which ports are reduced
        :type layer: str
        :param num_ports: Reduced number of ports
        :type num_ports: int
        :param select_ports: Select which port names should be included
        in the reduction. It is possible to use wildcards, defaults to None
        :type select_ports: str, optional
        :return: New database object with the reduced ports
        :rtype: :class:`pman.PortGroup()`
        '''

        if select_ports is None:
            # Only keep ports on the given layer
            ports = np.array([port for port in self.db.ports.values()
                                if port.layers[0] == layer]
                        )
        else:
            # Only keep ports on the given layer
            ports = np.array([port for port in self.db.find_comps(select_ports,
                                                                    False,
                                                                    self.db.ports
                                                                )
                                if port.layers[0] == layer]
                        )

        if num_ports >= len(ports):
            logger.warning(f'Number of ports on layer {layer} '
                    f'to reduce ({num_ports}), is greater than '
                    f'or equal to the existing number of ports ({len(ports)}). '
                    f'Reduction cannot be performed.')
            return self
        elif num_ports == 0:
            logger.warning(f'Port reduction will not be performed on layer {layer}')
            return self
        df = pd.DataFrame({'x': np.array([port.x_center for port in ports]),
                            'y': np.array([port.y_center for port in ports])})
        kmeans = KMeans(n_clusters=num_ports, init='k-means++', n_init=1, random_state=0).fit(df)
        labels = kmeans.predict(df)

        group_info = {}
        port_props = {}
        new_ports = []
        for port_num in range(num_ports):
            grouped_ports = ports[labels == port_num]
            port_names = []
            pos_nodes = []
            neg_nodes = []
            for port in grouped_ports:
                port_names.append(port.name)
                pos_nodes += port.pos_nodes
                neg_nodes += port.neg_nodes
                del self.db.ports[port.name]

            if len(grouped_ports) == 1:
                port_props['port_name'] = grouped_ports[0].name
            else:
                port_props['port_name'] = f'group{spd.Port.idx}_x{len(grouped_ports)}'
                spd.Port.idx += 1
            group_info[port_props['port_name']] = port_names
            port_props['pos_nodes'] = pos_nodes
            port_props['neg_nodes'] = neg_nodes
            port_props['port_width'] = grouped_ports[0].width
            port_props['ref_z'] = grouped_ports[0].ref_z
            new_ports.append(spd.Port(port_props))

        new_group = PortGroup(self.db, self.auto_reorder(new_ports))
        new_group.group_info = group_info
        return new_group

    def auto_copy(self, to_db, force=False):

        # Detect if databases are boards, packages, or merged
        # This is done in order to detect the socket side
        side = 'bottom'
        conn_src = self.db.get_conn(side) # Package database if not None
        if conn_src is None:
            side = 'top'
            conn_src = self.db.get_conn(side) # Board or merged databse is detected

        # Find same pin in both databases
        if conn_src is None:
            logger.warning(f'Cannot find connector circuits on top or bottom '
                           f'in the source {self.db} layout.\n'
                           f'Aborting auto copy operation.')
            return
        #node_src = self.db.nodes[skt_conn.nodes[0]]
        #pin_src = node_src.name.split('!!')[1]
        #all_pins_src = [node.split('!!')[1] for node in skt_conn.nodes]
        pins_to_nodes_src = {node.split('!!')[1]: node for node in conn_src.nodes}

        # Find connector in the to_db
        conn_dst = to_db.get_conn(side)
        if conn_dst is None:
            logger.warning(f'Cannot find connector circuits on top or bottom '
                           f'in the destination {to_db} layout.\n'
                           f'Aborting auto copy operation.')
            return

        #all_pins_dst = [node.split('!!')[1] for node in conn_dst.nodes]
        pins_to_nodes_dst = {node.split('!!')[1]: node for node in conn_dst.nodes}

        # Find a common pin name between source and destination
        node_dst = None
        for pin_src, node_src in pins_to_nodes_src.items():
            if pin_src in pins_to_nodes_dst:
                node_src = self.db.nodes[node_src]
                node_dst = to_db.nodes[pins_to_nodes_dst[pin_src]]
                break
        if node_dst is None:
            logger.warning('Unable to auto copy due to connector mismatch')
            return
    
        '''
        to_db_conn = None
        comps = to_db.find_comps(['*U*', '*A*'], verbose=False)
        if comps is None:
            logger.warning(f'Cannot find connector circuits on top or bottom '
                           f'in the destination {to_db.name} layout.\n'
                           f'Aborting auto copy operation.')
            return
        for comp in comps:
            if skt_conn.name in comp.name or len(skt_conn.nodes) == len(comp.nodes):
                to_db_conn = comp
                break

        if to_db_conn is None:
            logger.warning('Unable to auto copy due to connector mismatch.')
            return
        '''
        
        logger.info(f'Connector alignment: source {conn_src.name}, destination {conn_dst.name}')

        dx = node_dst.x - node_src.x
        dy = node_dst.y - node_src.y
        rot_angle = node_dst.rotation - node_src.rotation

        logger.info(f'Pin alignment: source {node_src.name}, destination {node_dst.name}')
        logger.info(f'dx = {dx*1e3:.3f} mm, dy = {dy*1e3:.3f} mm, '
                f'Rotation = {rot_angle} deg')
        if rot_angle == 0:
            return self.copy(dx, dy, to_db, force=force)
        else:
            return self.rotate_copy(node_src.x, node_src.y,
                                        node_dst.x, node_dst.y,
                                        rot_angle, to_db,
                                        force=force)
        
        '''
        node_dst = None
        to_db_pins = [to_db.nodes[node] for node in to_db_conn.nodes]
        for node in to_db_pins:
            if (node.type == 'pin'
                    and node.name.split('!!')[1] == pin_src
                    and node.layer.replace('PKG', '').replace('BRD', '')
                        == node_src.layer.replace('PKG', '').replace('BRD', '')):
                node_dst = node
                break
        
           
        # Calculate Cartesian difference and rotation angle
        if node_dst is None:
            logger.warning('Unable to auto copy due to pin map mismatch.')
        else:    
            dx = node_dst.x - node_src.x
            dy = node_dst.y - node_src.y
            rot_angle = node_dst.rotation - node_src.rotation

            logger.info(f'Pin alignment: source {node_src.name}, destination {node_dst.name}')
            logger.info(f'dx = {dx*1e3:.3f} mm, dy = {dy*1e3:.3f} mm, '
                    f'Rotation = {rot_angle} deg')
            if rot_angle == 0:
                return self.copy(dx, dy, to_db, force=force)
            else:
                return self.rotate_copy(node_src.x, node_src.y,
                                            node_dst.x, node_dst.y,
                                            rot_angle, to_db,
                                            force=force)
        '''
            
    def auto_port_comp(self, layer, comp_find, net_name=None, ref_z=50):

        comps = self.db.find_comps(comp_names=comp_find, verbose=False)
        nets = self.db.rail_names(find_nets=net_name, enabled=True, verbose=False)

        # Find all components connected to the specified net name and layer
        port_comp = {}
        for comp in comps:
            if comp.name not in self.db.components or not self.db.connects[comp.name].nodes:
                logger.warning(f'Component {comp.name} does not have nodes defined')
            elif self.db.nodes[self.db.connects[comp.name].nodes[0]].layer == layer:
                pos_nodes = []
                neg_nodes = []
                for node_name in comp.nodes:
                    if self.db.nodes[node_name].rail in nets:
                        pos_nodes.append(self.db.nodes[node_name])
                    elif (self.db.nodes[node_name].rail is not None
                            and (self.db.nodes[node_name].rail.lower().startswith('vss')
                            or self.db.nodes[node_name].rail.lower().startswith('gnd'))):
                        neg_nodes.append(self.db.nodes[node_name])

                if pos_nodes and neg_nodes:
                    port_comp[comp.name] = (pos_nodes, neg_nodes)

        new_ports = []
        port_props = {}
        for port_name, (pos_nodes, neg_nodes) in port_comp.items():
            port_props['port_name'] = port_name
            port_props['port_width'] = None
            port_props['ref_z'] = ref_z
            port_props['pos_nodes'] = pos_nodes
            port_props['neg_nodes'] = neg_nodes
            new_ports.append(spd.Port(port_props))
            logger.info(f'Port placed on component {port_name} on layer {layer}')
        
        return PortGroup(self.db, self.auto_reorder(new_ports))

    def auto_vrm_ports(self, layer, net_name=None, find_comps='*L*', ref_z=50):
        '''Automatically place ports at VRMs phase locations.

        :param layer: Layer name on which the VRMs are placed
        :type layer: str
        :param net_name: Net name(s) to which the VRMs are attached
        :type net_name: str or list[str]
        :param find_comps: Search string that can include wildcards
        to find the inductors of the repective VRMs, defaults to '*L*'
        :type find_comps: str, optional
        :param ref_z: Port reference impedance, defaults to 50 
        where the VRMs are placed, defaults to False
        :type ref_z: float, optional
        :return: A new database object with placed ports
        :rtype: :class:`pman.PortGroup()`
        '''

        vrm_db = tasks.PdcTask(self.db)
        return vrm_db.place_vrms(layer=layer, net_name=net_name,
                                    find_comps=find_comps,
                                    ref_z=ref_z,
                                    only_ports=True)

    def sinks_to_ports(self, ref_z=50, suffix=None):
        '''Converts sinks to ports using the same nodes.
        The existing sinks are preserved in the database.

        :param ref_z: Port reference impedance in Ohm, defaults to 50
        :type ref_z: int, optional
        :param suffix: Suffix to add to the sink original name, defaults to None
        :type suffix: str, optional
        :return: A new database object with placed ports
        :rtype: :class:`pman.PortGroup()`
        '''

        return PortGroup(self.db, self.auto_reorder([sink.to_port(ref_z, suffix)
                                   for sink in self.db.sinks.values()]))
    
    def vrms_to_ports(self, ref_z=50, suffix=None):
        '''Converts VRMs to ports using the same nodes.
        The existing VRMs are preserved in the database.

        :param ref_z: Port reference impedance in Ohm, defaults to 50
        :type ref_z: int, optional
        :param suffix: Suffix to add to the sink original name, defaults to None
        :type suffix: str, optional
        :return: A new database object with placed ports
        :rtype: :class:`pman.PortGroup()`
        '''

        return PortGroup(self.db, self.auto_reorder([vrm.to_port(ref_z, suffix)
                                   for vrm in self.db.vrms.values()]))
    
    def vrms_sense_to_ports(self, ref_z=50, suffix=None):
        '''Converts vrm's sense point (if defined) to ports using the same nodes.
        The existing VRM's sense points are preserved in the database.

        :param ref_z: Port reference impedance in Ohm, defaults to 50
        :type ref_z: int, optional
        :param suffix: Suffix to add to the sink original name, defaults to None
        :type suffix: str, optional
        :return: A new database object with placed ports
        :rtype: :class:`pman.PortGroup()`
        '''

        new_ports = []
        for vrm in self.db.vrms.values():
            port = vrm.sense_to_port(ref_z, suffix)
            if port is not None:
                new_ports.append(port)
        return PortGroup(self.db, new_ports)

    def boxes_to_ports(self, ref_z=50, port3D=False):
        '''Converts box elements, created in PowerSi, into ports.

        :param ref_z: Port reference impedance, defaults to 50
        :type ref_z: int, optional
        :param port3D: If True the ports are created for 3D extraction, defaults to False
        :type port3D: bool, optional
        :return: New database object with the added ports
        :rtype: :class:`pman.PortGroup()`
        '''

        if not self.db.boxes:
            logger.warning('Boxes do not exist in this layout. Operation is aborted.')
            return PortGroup(self.db, self.db.ports)
        
        new_ports = []
        for box_name in self.db.box_names(verbose=False):
            nodes = np.array([node for node in self.db.nodes.values()
                            if node.layer == self.db.boxes[box_name][0].layer])
            nodes_x = np.array([node.x for node in nodes])
            nodes_y = np.array([node.y for node in nodes])
            x1 = self.db.boxes[box_name][0].xcoords[0]
            y1 = self.db.boxes[box_name][0].ycoords[0]
            x2 = self.db.boxes[box_name][0].xcoords[2]
            y2 = self.db.boxes[box_name][0].ycoords[2]
            nodes_in_box = self._nodes_in_box(x1, y1, x2, y2,
                                            (nodes_x, nodes_y, nodes)
                                        )
            
            pos_nodes = defaultdict(list)
            neg_nodes = []
            for node in nodes_in_box:
                # Check if a node's rail is not None or that the net is not enabled
                # If so, ignore the node and continue to the next node
                if node.rail is None or not self.db.net_names[node.rail][0]:
                    continue
                elif 'vss' in node.rail.lower() or 'gnd' in node.rail.lower():
                    neg_nodes.append(node)
                else:
                    pos_nodes[node.rail].append(node)

            pwr_nodes_count = [(rail, len(nodes)) for rail, nodes in pos_nodes.items()]
            try:
                pwr_nodes = max(pwr_nodes_count, key=itemgetter(1))
            except ValueError:
                continue

            port_props = {}
            port_props['port_name'] = box_name
            port_props['port_width'] = None
            port_props['ref_z'] = ref_z 
            port_props['pos_nodes'] = pos_nodes[pwr_nodes[0]]
            port_props['neg_nodes'] = neg_nodes

            if port3D:
                if len(port_props['neg_nodes']) < 2:
                    # Find negetive nodes closest to the centroid of the box
                    xbox_center, ybox_center = (x1 + x2)/2, (y1 + y2)/2

                    neg_nodes = np.array([node for node in self.db.nodes.values()
                                            if node.rail is not None
                                                and node.layer == self.db.boxes[box_name][0].layer
                                                and ('vss' in node.rail.lower()
                                                or 'gnd' in node.rail.lower())])
                    nnodes_dist = []
                    for neg_node in neg_nodes:
                        nnodes_dist.append(
                                            (np.sqrt((neg_node.x - xbox_center)**2
                                            + (neg_node.y - ybox_center)**2),
                                            neg_node)
                                    )
                    dist = sorted(nnodes_dist, key=itemgetter(0))
                    port_props['neg_nodes'] = [dist[0][1], dist[1][1]]

                    '''
                    port_props['neg_nodes'] = np.array([node for node in nodes
                                                    if node.rail is not None
                                                    and ('vss' in node.rail.lower()
                                                    or 'gnd' in node.rail.lower())])
                    '''
    
                x_pos_center = [node.x for node in port_props['pos_nodes']]
                x_pos_center = np.mean(x_pos_center)
                y_pos_center = [node.y for node in port_props['pos_nodes']]
                y_pos_center = np.mean(y_pos_center)
                port_props = self._create_3D_port(port_props,
                                                    x_pos_center, y_pos_center,
                                                    port_props['pos_nodes'][0].layer)

            if port_props is None:
                logger.warning(f'Cannot create a port from {box_name}. '
                      f'Increase box size to include more ground nodes.')
            else:
                new_ports.append(spd.Port(port_props))

        # Comment out boxes from the database
        for idx in [box[1] for box in self.db.boxes.values()]:
            self.db.lines[idx - 1] = f'* {self.db.lines[idx - 1]}'
        #boxes_idx = sorted([box[1] for box in self.db.boxes.values()])
        #del self.db.lines[boxes_idx[-2]-1:boxes_idx[-1]]

        return PortGroup(self.db, self.auto_reorder(new_ports))

    def transfer_socket_ports(self, to_db, from_db_side, to_db_side, suffix=None):
        '''Copies socket ports from a database to another database.
        For example, board top socket ports are copied to the corresponding
        bottom of the package. The copy is done based on pin names, ensuring
        accurate port allocation on each side.

        :param to_db: Database where ports are coppied to
        :type to_db: :class:`speed.Database()`
        :param from_db_side: Accepts only 'bottom' (for package) or 'top' (for board) parameters.
        :type side: str
        :param to_db_side: Accepts only 'bottom' (for package) or 'top' (for board) parameters.
        :type side: str
        :param suffix: Suffix to add to each coppied port, defaults to None
        :type suffix: str, optional
        :return: Database with the coppied ports
        :rtype: :class:`pman.PortGroup()`
        '''

        suffix = '' if suffix is None else f'_{suffix}'
        # Find ports only on the connector pins of the from_db database
        from_db_conn = self.db.get_conn(from_db_side)
        from_db_ports = []
        for port in self.db.ports.values():
            for pnode in port.pos_nodes:
                if pnode.name in from_db_conn.nodes:
                    from_db_ports.append(port)
                    break
        
        # Find pins by pin name in the to_db database
        to_db_conn = to_db.get_conn(to_db_side)
        pin_map = {node_name.split('!!')[1]: to_db.nodes[node_name]
                            for node_name in to_db_conn.nodes}

        new_ports = []
        for port in from_db_ports:
            new_pos_nodes = []
            new_neg_nodes = []
            for pnode in port.pos_nodes:
                if pnode.type == 'pin':
                    try:
                        new_pos_nodes.append(pin_map[pnode.name.split('!!')[1]])
                    except KeyError:
                        pass
            for nnode in port.neg_nodes:
                if nnode.type == 'pin':
                    try:
                        new_neg_nodes.append(pin_map[nnode.name.split('!!')[1]])
                    except KeyError:
                        pass

            props = {'port_name': f'{port.name}{suffix}',
                    'port_width': port.width,
                    'ref_z': port.ref_z,
                    'pos_nodes': new_pos_nodes,
                    'neg_nodes': new_neg_nodes}
            new_ports.append(spd.Port(props))
        
        return PortGroup(to_db, new_ports)
        
    def auto_port_conn(self, num_ports, side, net_name, ref_z=50):
        '''Automatically places selected number of ports using socket pins.
        The ports are placed on the enabled power pin rails.
        If several power rails are enabled, the number of ports for each rail
        is proportionally determined based on the number of pins.

        :param num_ports: Total number of ports
        :type num_ports: int
        :param side: Accepts only 'bottom' (for package) or 'top' (for board) parameters.
        :type side: str
        :param ref_z: Port reference impedance, defaults to 50
        :type ref_z: int, optional
        :return: New database object with the added ports
        :rtype: :class:`pman.PortGroup()`
        '''

        conn_ckt = self.db.get_conn(side)
        if conn_ckt is None:
            logger.warning(f'Layout does not have a connector on the {side} side. '
                           f'Socket ports will not be placed.')
            return self
        else:
            logger.info(f'{num_ports} socket ports will be placed on {conn_ckt.name} '
                        f'({len(conn_ckt.nodes)} pins)')

        # Find connector power and ground nodes by rail
        conn_nodes = defaultdict(list)
        gnd_nodes = []
        enabled_nets = [netname for netname, (enabled, net_type) in self.db.net_names.items()
                        if enabled and net_type == 'power' and netname == net_name]
        for node_name in conn_ckt.nodes:
            layer = self.db.nodes[node_name].layer
            rail = self.db.nodes[node_name].rail
            node = self.db.nodes[node_name]
            if rail is None:
                continue
            if rail in enabled_nets and node.type == 'pin':
                conn_nodes[(layer, rail)].append(node)
            if rail.lower().startswith('vss') or rail.lower().startswith('gnd'):
                gnd_nodes.append(node)

        # Count total number of nodes
        node_count = [len(conn_node) for conn_node in conn_nodes.values()]
        node_count = np.sum(node_count)

        result = self
        for nodes_info, pwr_nodes in conn_nodes.items():
            result = result.auto_port(layer=nodes_info[0],
                                        net_name=net_name,
                                        #num_ports=int(np.ceil(num_ports*(len(pwr_nodes)/node_count))),
                                        num_ports=num_ports,
                                        ref_z=ref_z,
                                        nodes_to_use=pwr_nodes + gnd_nodes,
                                        prefix='skt')
            result.add_ports(save=False)

        return result

    def auto_port(self, layer, net_name, num_ports, area=None,
                    ref_z=50, port3D=False, nodes_to_use=None,
                    prefix=None, verbose=True):

        if area is None:
            x1 = self.db.db_x_bot_left
            y1 = self.db.db_y_bot_left
            x2 = self.db.db_x_top_right
            y2 = self.db.db_y_top_right
        else:
            x1, y1, x2, y2 = area
        prefix = '' if prefix is None else f'{prefix}_'

        all_nodes = self.db.nodes.values() if nodes_to_use is None else nodes_to_use
        nets = self.db.rail_names(find_nets=net_name, enabled=True, verbose=False)
        
        new_ports = []
        for net in nets:
            # Find power nodes
            nodes = np.array([node for node in all_nodes
                                if node.layer == layer
                                and node.rail is not None
                                and node.rail == net])
            pwr_nodes_x = np.array([node.x for node in nodes])
            pwr_nodes_y = np.array([node.y for node in nodes])
            pwr_nodes_in_box = self._nodes_in_box(x1, y1, x2, y2,
                                                (pwr_nodes_x, pwr_nodes_y, nodes)
                                            )
            pwr_nodes_x = np.array([node.x for node in pwr_nodes_in_box])
            pwr_nodes_y = np.array([node.y for node in pwr_nodes_in_box])

            # Find ground nodes
            nodes = np.array([node for node in all_nodes
                        if node.layer == layer
                        and node.rail is not None
                        and (node.rail.lower().startswith('vss')
                            or node.rail.lower().startswith('gnd'))]
                    )
            gnd_nodes_x = np.array([node.x for node in nodes])
            gnd_nodes_y = np.array([node.y for node in nodes])
            gnd_nodes_in_box = self._nodes_in_box(x1, y1, x2, y2,
                                                (gnd_nodes_x, gnd_nodes_y, nodes)
                                            )
            gnd_nodes_x = np.array([node.x for node in gnd_nodes_in_box])
            gnd_nodes_y = np.array([node.y for node in gnd_nodes_in_box])

            df = pd.DataFrame({'x': pwr_nodes_x,
                                'y': pwr_nodes_y})
            n_data = len(pwr_nodes_in_box)
            
            if n_data == 0:
                if verbose:
                    logger.warning(f'Cannot find net {net} to place ports. '
                                f'Check if {net} is enabled and classified as power or ground.')
                continue
            if num_ports > n_data:
                if verbose:
                    logger.warning(f'Number of ports {num_ports} '
                        f'exceed the number of nodes {n_data}.\n'
                        f'Setting number of ports to {n_data}.')
                num_ports = n_data
            kmeans = KMeans(n_clusters=num_ports, init='k-means++', n_init=1, random_state=0).fit(df)
            x_center, y_center = kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1]
            labels = kmeans.predict(df)

            port_props = {}
            for port_num in range(num_ports):
                port_props['port_width'] = None
                port_props['ref_z'] = ref_z 
                port_props['pos_nodes'] = list(pwr_nodes_in_box[labels == port_num])
                port_props['port_name'] = f"{prefix}{port_props['pos_nodes'][0].rail}_{spd.Port.idx}"
                spd.Port.idx += 1 

                # Find negative nodes nearby each positive node
                gnd_nodes = []
                for pos_node in port_props['pos_nodes']:
                    gnd_radius = 0.15e-3
                    found_gnd_nodes = []
                    while not found_gnd_nodes and gnd_radius < 5e-3:
                    #while len(found_gnd_nodes) <= 1 and gnd_radius < 5e-3:
                        found_gnd_nodes = list(gnd_nodes_in_box[(np.sqrt((gnd_nodes_x - pos_node.x)**2
                                        + (gnd_nodes_y - pos_node.y)**2) < gnd_radius)])
                        gnd_radius *= 2
                    gnd_nodes += found_gnd_nodes

                # Eliminate duplicate gnd nodes
                port_props['neg_nodes'] = [self.db.nodes[node_name]
                                            for node_name in set([node.name for node in gnd_nodes])
                                            if self.db.net_names[self.db.nodes[node_name].rail][0]] # Condition checks the rail is enabled
                
                if port3D:
                    port_props = self._create_3D_port(port_props, x_center[port_num], y_center[port_num],
                                                        layer)

                if port_props is not None:
                    new_ports.append(spd.Port(port_props))
                else:
                    port_props = {}
        
        return PortGroup(self.db, self.auto_reorder(new_ports))
    
    def auto_reorder(self, ports):

        '''
        x_center, y_center = [], []
        for port in ports:
            x_center.append(port.x_center)
            y_center.append(port.y_center)

        # Find bins on the y axis
        bins = np.linspace(min(y_center), max(y_center),
                           int((max(y_center) - min(y_center))/0.001e-3))
        it = iter(bins)
        pair_bins = []
        for bin in it:
            try:
                pair_bins.append((bin, next(it)))
            except StopIteration:
                pass
        
        bin_ports = defaultdict(list)
        # Bin ports into the buckets
        for port in ports:
            for idx, (bot_range, top_range) in enumerate(pair_bins):
                if bot_range <= port.y_center <= top_range:
                    bin_ports[idx].append(port)
                    #break

        # Sort bin_ports by keys
        bin_ports = dict(sorted(bin_ports.items(), reverse=True))

        ordered_ports = []
        for bin_port in bin_ports.values():
            ports_per_bin = [(port, port.x_center) for port in bin_port]
            ports_per_bin = sorted(ports_per_bin, key=itemgetter(1))
            ordered_ports += [port for (port, _) in ports_per_bin]

        return ordered_ports
        '''
        
        if not ports:
            return ports
        
        x_center, y_center = [], []
        for port in ports:
            x_center.append(port.x_center)
            y_center.append(port.y_center)

        # Find top left anchor point which is minimum x and maximum y
        x_anchor, y_anchor = min(x_center), max(y_center)

        # Reorder ports by distance to the anchor point
        ordered_ports = []
        for port in ports:
            ordered_ports.append((np.sqrt((x_anchor - port.x_center)**2
                                         + (y_anchor - port.y_center)**2),
                                    port)
                            )
        
        ordered_ports = sorted(ordered_ports, key=itemgetter(0))
        
        return [port[1] for port in ordered_ports]
               
    def add_ports(self, fname=None, save=True):

        if not self.ports:
            return
        
        for port in self.ports:
            self.db.ports[port.name] = port
            if self._is_forced_nodes(port.pos_nodes):
                for node in port.pos_nodes:
                    self.db.nodes[node.name] = node
            if self._is_forced_nodes(port.neg_nodes):
                for node in port.neg_nodes:
                    self.db.nodes[node.name] = node

        self.update_ports(fname, save)

    def update_ports(self, fname=None, save=False):

        # Delete port section from the database and then start a new one
        try:
            port_loc = self.db.lines.index('.Port\n')
            idx_start = port_loc
            idx_end = self.db.lines.index('.EndPort\n') + 1
            del self.db.lines[idx_start:idx_end]
            raise ValueError
        except ValueError:
            port_loc = self.db.lines.index('* Port description lines\n') + 1
            self.db.lines.insert(port_loc, '.Port\n')
            self.db.lines.insert(port_loc + 1, '.EndPort\n')
            port_loc += 1

        forced_nodes = []
        # Add new ports and existing ports if any to the database
        for port in reversed(list(self.db.ports.values())):
            width = '' if port.width is None else f' Width = {port.width*1e3:.3f}mm'
            new_port = [f'{port.name} RefZ = {port.ref_z}{width}']
            if port.pos_nodes:
                new_port.append('+ PositiveTerminal ')
                for node in port.pos_nodes:
                    new_port.append(f'+ $Package.{node.name}::{node.rail}')
                    if 'tpi' in node.name:
                        forced_nodes.append(node)
            if port.neg_nodes:
                new_port.append('+ NegativeTerminal ')
                for node in port.neg_nodes:
                    new_port.append(f'+ $Package.{node.name}::{node.rail}')
                    if 'tpi' in node.name:
                        forced_nodes.append(node)

            for new_line in reversed(new_port):
                self.db.lines.insert(port_loc, f'{new_line}\n')

        node_loc = self.db.lines.index(
                        self.db.version_handler('nodes_start') + '\n'
                    ) + 1
        for node in forced_nodes:
            new_node = (f'{node.name}::{node.rail} X = {node.x*1e3}mm '
                        f'Y = {node.y*1e3}mm Layer = {node.layer} '
                        f'AbsoluteRotation = {node.rotation}\n')
            self.db.lines.insert(node_loc, new_node)

        if save:
            self.db.save(fname)

    def status(self, verbose=True):

        report = []
        for port in self.ports:
            if port.pos_nodes and port.neg_nodes:
                report.append(f'{port.name} is placed between '
                            f'{port.pos_rails[0]} and {port.neg_rails[0]} '
                            f'on layer {port.layers[0]} at '
                            f'({port.x_center*1e3:.3f} mm, '
                            f'{port.y_center*1e3:.3f} mm)')
                if verbose:
                    logger.info(report[-1])
                if self._is_forced_nodes(port.pos_nodes):
                    report.append(f'{port.name} positive nodes '
                                f'are added to the layout')
                    if verbose:
                        logger.info(report[-1])
                if self._is_forced_nodes(port.neg_nodes):
                    report.append(f'{port.name} negative nodes '
                            f'are added to the layout')
                    if verbose:
                        logger.info(report[-1])
            elif port.pos_nodes:
                report.append(f'{port.name} has no ground nodes. '
                        f'Placement has failed. '
                        f'Positive nodes are connected at '
                        f'({port.x_center*1e3:.3f} mm, '
                        f'{port.y_center*1e3:.3f} mm)')
                if verbose:
                    logger.warning(report[-1])
            elif port.neg_nodes:
                report.append(f'{port.name} has no power nodes. '
                        f'Placement has failed. '
                        f'Negative nodes are connected at '
                        f'({port.x_center*1e3:.3f} mm, '
                        f'{port.y_center*1e3:.3f} mm)')
                if verbose:
                    logger.warning(report[-1])
            else:
                report.append(f'{port.name} has no power nor ground nodes. '
                            f'Port placement has failed.')
                if verbose:
                    logger.warning(report[-1])

        return report

    def export_port_info(self, ports_fname=None, names_only=False):

        ports_fname = f'{self.db.name.split(".")[0]}_ports.csv' \
                            if ports_fname is None else ports_fname

        if ports_fname is None:
            ports_fname = Path(self.db.path) / Path(f'{Path(self.db.name).stem}_portinfo.csv')

        if names_only:
            port_info = {'Port Name': [], 'VRM/Sink': []}
            for port in self.db.ports.values():
                port_info['Port Name'].append(port.name)
                if 'vr' in port.name.lower():
                    port_info['VRM/Sink'].append('vrm')
                else:
                    port_info['VRM/Sink'].append('sink')
            df_ports = pd.DataFrame(port_info)
        else:
            df_ports = []
            for port in self.db.ports.values():
                props = port.df_props()
                if props is not None:
                    df_ports.append(props)
            df_ports = pd.concat(df_ports).reset_index(drop=True)

        df_ports.to_csv(ports_fname, index=False)
        return df_ports

    def import_port_info(self, ports_fname, fname=None, save=True):

        updated_ports = {}
        port_info = pd.read_csv(ports_fname)
        for _, row in port_info.iterrows():
            new_port = self.db.ports[row['Name']]
            new_port.ref_z = float(row['Ref Z'])
            if not pd.isnull(row['Width']):
                new_port.width = float(row['Width'])
            if not pd.isnull(row['New name']):
                new_port.name = row['New name']
                updated_ports[row['New name']] = new_port
            else:
                updated_ports[row['Name']] = new_port
    
        self.db.ports = updated_ports
        self.update_ports(fname, save)
