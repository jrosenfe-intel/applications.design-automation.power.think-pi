import os
import shutil
from typing import List
from copy import copy
from operator import itemgetter, attrgetter
from collections import defaultdict
import re
import subprocess
from pathlib import Path
from random import shuffle
import time
import glob
from threading import Thread
from threading import Event

import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import matplotlib.path as mpltPath
from PIL import ImageChops, Image
from scipy import interpolate
from dataclasses import dataclass
from sklearn.metrics import mean_squared_error
import skrf as rf
from scipy.interpolate import interp1d

from thinkpi.tools import hspice_deck
from thinkpi.tools import hspice
from thinkpi.tools import idem
from thinkpi.operations import loader as ld
from thinkpi.operations import speed as spd
from thinkpi.flows.tcl import Tcl
from thinkpi.flows.simplis_cmds import SimplisCommands
from thinkpi.operations import pman as pm
from thinkpi.config import thinkpi_conf as cfg
from thinkpi import _thinkpi_path, logger


class TasksBase:

    cmds = []

    def __init__(self, db_fname=None):
        
        if isinstance(db_fname, str):
            self.db = spd.Database(db_fname)
            self.db.load_data()
        else:
            self.db = db_fname

        self.tcl = Tcl(self.db)
        self.pwr_nets = None
        self.gnd_nets = None
        self.db_new_name = None
        self.exec_paths = self.find_exec_paths()

    def find_exec_paths(self):

        exec_paths = defaultdict(list)

        # Find all Cadence sigrity tools
        p = Path('C:/Cadence')
        for path in list(p.glob('Sigrity*')):
            exec_paths['sigrity'].append(str(path / Path('tools')
                                                    / Path('bin')
                                                    / Path('powersi.exe')))
        exec_paths['sigrity'] = sorted(exec_paths['sigrity'], reverse=True)
            
        # Find all Simplis tools
        p = Path('C:/Program Files')
        for path in list(p.glob('SIMetrix*')):
            exec_paths['simplis'].append(str(path / Path('bin64')
                                                    / Path('SIMetrix.exe')))
        exec_paths['simplis'] = sorted(exec_paths['simplis'], reverse=True)

        # Find all Hspice tools
        p = Path('C:/Synopsys')
        for path in list(p.glob('Hspice*')):
            exec_paths['hspice'].append(str(path / Path('win64')))
        exec_paths['hspice'] = sorted(exec_paths['hspice'], reverse=True)

        # Find all IdEM tools
        p = Path('C:/Program Files (x86)')
        for path in list(p.glob('CST Studio Suite*')):
            exec_paths['idem'].append(str(path / Path('AMD64')))
        exec_paths['idem'] = sorted(exec_paths['idem'], reverse=True)

        return exec_paths

    def export_stackup_padstack(self, stackup_fname=None,
                                padstack_fname=None):

        # Export stackup file using tcl commands
        stackup = self.tcl.generate_stackup(stackup_fname)

        # Export padstack file
        padstack = self.tcl.generate_padstack(padstack_fname)

        return stackup, padstack

    def select_nets(self, pwr_nets=None, gnd_nets=None):

        self.pwr_nets = self.db.rail_names(verbose=False, find_nets=pwr_nets, enabled=True)
        self.gnd_nets = self.db.rail_names(verbose=False, find_nets=gnd_nets, enabled=True)

        logger.info('\nPower nets selected:')
        for pwr_net in self.pwr_nets:
            logger.info(f'\t{pwr_net}')
        logger.info('\nGround nets selected:')
        for gnd_net in self.gnd_nets:
            logger.info(f'\t{gnd_net}')

    def apply_stackup(self, stackup_fname, material_fname=None):
        """Apply the provided stackup csv file to the layout file and save it

        :param stackup_fname: Stackup csv file name
        :type stackup_fname: str
        :param material_fname: Material txt file name, defaults to None
        :type material_fname: str or None, optional
        """    

        TasksBase.cmds += [
            '' if material_fname is None else self.tcl.import_material(material_fname),
            self.tcl.setup_stackup(stackup_fname)
        ]

    def apply_padstack(self, padstack_fname, material_fname=None):
        """Apply the provided padstack csv file to the layout file and save it

        :param padstack_fname: Padstack csv file name
        :type padstack_fname: str
        :param material_fname: Material txt file name, defaults to None
        :type material_fname: str or None, optional
        """        

        TasksBase.cmds += [
            '' if material_fname is None else self.tcl.import_material(material_fname),
            self.tcl.setup_padstack(padstack_fname)
        ]

    def preprocess(self, stackup_fname=None, padstack_fname=None,
                    material_fname=None, default_conduct=None,
                    cut_margin=1e-3, db_fname=None, delete_unused_nets=False,
                    pads_to_shapes=None):
        '''Preprocess a database before performing 2D extraction or a PowerDC simulation.

        :param stackup_fname: File name with the stackup information
        :type stackup_fname: str
        :param padstack_fname: File name with the padstack information
        :type padstack_fname: str
        :param material_fname: File name with the material information, defaults to None
        :type material_fname: None or str, optional
        :param default_conduct: Conductivity in S/m that is assumed for copper.
        This should be provided when a material file is not available, defaults to None
        :type default_conduct: None or float, optional
        :param cut_margin: Margin to leave around nets of interest in Meters
        when cut is performed. If 0 is provided no cut is performed, defaults to 1 mm
        :type cut_margin: float, optional
        :param db_fname: File name of processed database.
        If not provided the original database will be overwritten, defaults to None
        :type db_fname: None or str, optional
        :param delete_unused_nets: If True deletes unused nets from the database, defaults to False
        :type delete_unused_nets: bool, optional
        :param pads_to_shapes: If True, performs pads to shapes conversion.
        If None, will perforam pads to shapes conversion only if it is a package layout,
        defaults to None
        :type pads_to_shapes: None or bool, optional
        '''

        if db_fname is not None:
            self.db.name = os.path.basename(db_fname)
        # Assign all nets to signals.
        # Later only selected nets will be assigned to power or ground
        self.db.nets_to_signals()
        self.db.save()

        if ((pads_to_shapes is None
                and 'surface' in self.db.layer_names(verbose=False)[0]
                and 'base' in self.db.layer_names(verbose=False)[-1])
            or pads_to_shapes):
            pads_to_shapes = self.tcl.pads_to_shapes(0.0001)
        else:
            pads_to_shapes = ''

        TasksBase.cmds += [
                        '' if stackup_fname is None else self.tcl.setup_stackup(stackup_fname),
                        '' if padstack_fname is None else self.tcl.setup_padstack(padstack_fname),
                        '' if material_fname is None else self.tcl.import_material(material_fname),
                        self.tcl.disable_all_nets(),
                        self.tcl.enable_nets(*self.pwr_nets),
                        self.tcl.classify_as_power(*self.pwr_nets),
                        self.tcl.cut_by_nets(cut_margin, *self.pwr_nets) if cut_margin > 0 else '',
                        self.tcl.enable_nets(*self.gnd_nets),
                        self.tcl.classify_as_ground(*self.gnd_nets),
                        self.tcl.color_nets('darkgreen', *self.gnd_nets),
                        self.tcl.delete_disabled_nets() if delete_unused_nets else '',
                        self.tcl.traces_to_shape(*(self.pwr_nets + self.gnd_nets)),
                        pads_to_shapes,
                        self.tcl.shape_process(),
                        self.tcl.split_nets(*(self.pwr_nets + self.gnd_nets)),
                        self.tcl.disable_all_components(),
                        self.tcl.auto_special_voids(),
                        self.tcl.default_via_conduct(default_conduct)
                                if default_conduct is not None else '',
                        #self.tcl.find_shorts()
                    ]

    def update_stackup(self, fname):

        TasksBase.cmds.append(self.tcl.setup_stackup(fname))

    def auto_setup_stackup(self, fname, dielec_thickness=None,
                            metal_thickness=None, core_thickness=None,
                            conduct=None, dielec_material=None,
                            metal_material=None, core_material=None,
                            fillin_dielec_material=None, er=None,
                            loss_tangent=None, unit='m'):
        '''Automatically prefills stackup information based on user input
        and saves it as .csv file.

        :param fname: File name of the output satckup .csv file
        :type fname: str
        :param dielec_thickness: Dielectric layers thickness in meters, defaults to None
        :type dielec_thickness: None or float, optional
        :param metal_thickness: Metal layers thickness in meters, defaults to None
        :type metal_thickness: None or float, optional
        :param core_thickness: Core layer thickness (for package) in meters, defaults to None
        :type core_thickness: None or float, optional
        :param conduct: Metal conductivity in S/m, defaults to None
        :type conduct: None or float, optional
        :param dielec_material: Name of dielectric material, defaults to None
        :type dielec_material: None or str, optional
        :param metal_material: Name of metal material, defaults to None
        :type metal_material: None or str, optional
        :param core_material: Name of core material (for package), defaults to None
        :type core_material: None or str, optional
        :param fillin_dielec_material: Name of fill-in dielectric material, defaults to None
        :type fillin_dielec_material: None or str, optional
        :param er: Material permittivity, defaults to None
        :type er: float, optional
        :param loss_tangent: Material loss tangent, defaults to None
        :type loss_tangent: float, optional
        '''

        TasksBase.cmds.append(self.tcl.auto_setup_stackup(fname, dielec_thickness,
                                                            metal_thickness, core_thickness,
                                                            conduct, dielec_material,
                                                            metal_material, core_material,
                                                            fillin_dielec_material,
                                                            er, loss_tangent, unit
                                                        )
                        )

    def update_padstack(self, fname):

        TasksBase.cmds.append(self.tcl.setup_padstack(fname))

    def auto_setup_padstack(self, fname, db_type, brd_plating=None,
                            pkg_gnd_plating=None, pkg_pwr_plating=None,
                            conduct=None, material=None,
                            innerfill_material=None, outer_thickness=None,
                            outer_coating_material=None, unit='m'):
        '''Automatically prefills padstack information based on user input
        and saves it as .csv file.

        :param fname: File name of the output padstack .csv file 
        :type fname: str or None
        :param db_type: The type of the database. Can only be 'board', 'brd', 'package', or 'pkg'
        :type db_type: str
        :param brd_plating: Board Plating thickness in meters. If not provided, uses the original value in the database.
        :type brd_plating: None or float, optional
        :param pkg_gnd_plating: Package ground PTH plating thickness in meters. If not provided, uses the original value in the database.
        :type pkg_gnd_plating: None or float, optional
        :param pkg_pwr_plating: Package power PTH plating thickness in meters. If not provided, uses the original value in the database.
        :type pkg_pwr_plating: None or float, optional
        :param conduct: Metal conductivity in S/m. If not provided defaults
        to 3.4e7 S/m for a board and to 4.31e7 S/m for a package, defaults to None
        :type conduct: None or float, optional
        :param material: Pad material, defaults to None
        :type material: None or str, optional
        :param innerfill_material: PTH inner-fill material name, defaults to None
        :type innerfill_material: None or str, optional
        :param outer_thickness: PTH outer thickness in meters.
        Typically used for FIVR inductor power and ground PTHs, defaults to None
        :type outer_thickness: None or float, optional
        :param outer_coating_material: PTH outer coating material name.
        Typically used for FIVR magnetic inductor power PTHs, defaults to None
        :type outer_coating_material: None or str, optional
        :param unit: The unit of the given parameters (excluding conductivity), defaults to 'm'
        :type unit: str, optional
        '''

        TasksBase.cmds.append(self.tcl.auto_setup_padstack(fname, db_type, brd_plating,
                                                            pkg_gnd_plating, pkg_pwr_plating,
                                                            conduct, material,
                                                            innerfill_material,
                                                            outer_thickness,
                                                            outer_coating_material,
                                                            unit
                                                    )
                        )
        
    def connector_res_ind(self, pin_res, pin_ind):
        '''Modify and update pin resistance and inductance of a connector between two layouts.

        :param pin_res: Resistance of a single pin in Ohm.
        If None, no modification of pin resistance is done.
        :type pin_res: float or None
        :param pin_ind: Self inductance of a pin in Henry.
        If None, no modification of pin inductance is done.
        :type pin_ind: float or None
        '''

        try:
            line_gen = self.db.extract_block('.PartialCkt Connector',
                                            '* Component description lines')
             
            for line_num, line in line_gen:
                if line[:2] == 'V_' or line[:2] == 'L_':
                    split_line = line.split()
                    if pin_ind is not None:
                        split_line[0] = f'L_{split_line[0][2:]}'
                        split_line[3] = str(pin_ind)
                    if pin_res is not None:
                        split_line[6] = str(pin_res)
                    self.db.lines[line_num] = ' '.join(split_line) + '\n'
        except ValueError:
            logger.warning('Connector circuit could not be found')

    def merge(self, top_db, pin_res, merged_db_name=None):

        self.db_new_name = merged_db_name

        # Find connector circuit of bottom db
        bot_conn_ckt = self.db.get_conn('top')
        # Find connector circuit of top db
        top_conn_ckt = top_db.db.get_conn('bottom')
        logger.warning(f'\nBottom database component {bot_conn_ckt.name} '
                f'({len(bot_conn_ckt.nodes)} pins) will connect to '
                f'top database {top_conn_ckt.name} ({len(top_conn_ckt.nodes)} pins)')

        TasksBase.cmds += [self.tcl.merge_db(
                                        os.path.join(top_db.db.path, top_db.db.name),
                                        bot_conn_ckt.name, top_conn_ckt.name,
                                        pin_res),
                            self.tcl.disable_all_components(),
                            self.tcl.classify_as_ground(*top_db.db.rail_names(find_nets='vss*',
                                                                              enabled=True,
                                                                              verbose=False,
                                                                            )
                                                    )
                        ]

    def cut_area(self, cut_margin=3):
        '''Cutting layout area based on selected nets defined by :method:`tasks.TasksBase.select_nets()`.

        :param cut_margin: Increase the margin around the cutting area
        in percentage. If 0 is given no cut is performed, defaults to 3%
        :type cut_margin: float, optional
        '''

        if cut_margin == 0:
            return ''
        
        cut_margin = cut_margin/100
        # Find all shape coords of the selected power nets on all layers
        xmin, ymin = np.inf, np.inf
        xmax, ymax = -np.inf, -np.inf

        # Check all shapes
        for shape in self.db.shapes.values():
            if shape.net_name in self.pwr_nets:
                xmin = min(xmin, min(shape.xcoords))
                ymin = min(ymin, min(shape.ycoords))
                xmax = max(xmax, max(shape.xcoords))
                ymax = max(ymax, max(shape.ycoords))
        # TODO: Check all vias

        xmin = xmin*(1 - cut_margin) if xmin > 0 else xmin*(1 + cut_margin)
        ymin = ymin*(1 - cut_margin) if ymin > 0 else ymin*(1 + cut_margin)
        xmax = xmax*(1 + cut_margin) if xmax > 0 else xmax*(1 - cut_margin)
        ymax = ymax*(1 + cut_margin) if ymax > 0 else ymax*(1 - cut_margin)

        return self.tcl.cut_by_area(xmin, ymin, xmax, ymax, 'outside')

    def create_tcl(self, flow, tcl_fname=None, add_cmds=None):

        if add_cmds is None:
            add_cmds = []
        TasksBase.cmds = [self.tcl.open(os.path.join(self.db.path, self.db.name)),
                            self.tcl.update_workflow(flow[0], flow[1]),
                            *TasksBase.cmds,
                            *add_cmds,
                            self.tcl.save(self.db_new_name),
                            self.tcl.close()]
        
        tcl_fname = self.tcl.create_tcl(tcl_fname, *TasksBase.cmds)
        TasksBase.cmds = []

        logger.info(f'TCL file is created and saved {tcl_fname}')
        return tcl_fname
    
    def _print_tcl_lines(lines):

        for line in lines:
            if '--' in line:
                line = line.split('--')[1]
            line = line.strip(' ')
            if 'WARNING' in line:
                logger.warning(line)
            elif 'ERROR' in line or 'failed' in line:
                logger.error(line)
            else:
                logger.info(line)
    
    def stream_log(self, event, tcl_fname):

        # Detect the newly log file name
        start_time = time.time()
        path = Path(tcl_fname).parent
        
        def find_log_file():
            while True:
                try:
                    log_fname = max(path.glob(f'{Path(self.db.name).stem}*.log'),
                                    key=os.path.getctime)
                    if log_fname.stat().st_mtime > start_time:
                        return log_fname
                except ValueError:
                    time.sleep(1)

        # Monitor for modifications and print log file content
        last_line = 0
        stop_thread = False
        log_fname = find_log_file()
        while not stop_thread:
            if event.is_set():
                stop_thread = True
            try:
                mod_time = Path(log_fname).stat().st_mtime
            except FileNotFoundError:
                log_fname = find_log_file()

            if  mod_time > start_time:
                start_time = time.time() #mod_time
                lines = Path(log_fname).read_text().split('\n')
                #logger.info(lines[last_line:-1])
                #_print_tcl_lines(lines[last_line:-1])
                for line in lines[last_line:-1]:
                    if '--' in line:
                        line = line.split('--')[1]
                    line = line.strip(' ')
                    if 'WARNING' in line:
                        logger.warning(line)
                    elif 'ERROR' in line or 'failed' in line:
                        logger.error(line)
                    else:
                        logger.info(line)
                last_line = len(lines)
            time.sleep(1)

        # Finally, check if tcl file was successfully executed
        if 'sigrity::close document' in lines[-2]:
            logger.info('TCL file was executed successfully\n')
            return True
        else:
            logger.error('--> TCL file failed to execute correctly\n')
            return False

    def run_tcl(self, tcl_fname, exec_path):
        '''Runs tcl script and check if it ran successfully.

        :param tcl_fname: Name of the tcl file to run
        :type tcl_fname: str
        :param exec_path: path to Cadence executable
        :type exec_path: str
        '''

        if Path(tcl_fname).parent == Path('.'):
            tcl_fname = str(Path(self.db.path) / Path(tcl_fname))

        # create the event
        event = Event()
        # create and configure a new thread
        thread = Thread(target=self.stream_log, args=(event, tcl_fname))
        # start the new thread
        thread.start()

        logger.info(f'Cadence tool version: {exec_path}')
        logger.info(f'Running {tcl_fname}, Please wait... ')
        cmd = f'{exec_path} -b -tcl {tcl_fname}'.split()
        #cmd.append(os.path.join(self.db.path, tcl_fname))
        run_result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        logger.info('Done\n')

        # stop the worker thread
        event.set()
        # wait for the new thread to finish
        thread.join()

        # Check status of the .tcl file run
        # self._check_tcl_run(os.path.join(self.db.path, tcl_fname))
        # Clean tcl command stack
        TasksBase.cmds = []

    def save_layout_views(self, path=None, zoom=False):
        '''Saves all layer view images in .png format.
        Before saving, it zooms in based on the dimension of each layer.
        Images are saved in a folder called layer_views.
        If it does not exist the folder will be created.

        :param path: Path where to save all the images, defaults to None.
        If None is provided the database location is used.
        :type path: str, optional
        :param zoom: If True will zoom on the layout area, defaults to False
        :type zoom: bool, optional
        '''
        # Zooming only works in PowerDC version 2022 and beyond

        path = self.db.path if path is None else path
        path = os.path.abspath(path)
        path = os.path.join(path, 'layer_views')
        if not os.path.isdir(path):
            os.makedirs(path)

        # Find zoom window for each layer

        # Inital dict
        coords_per_layer = {}
        for layer_name in self.db.layer_names(verbose=False):
            coords_per_layer[layer_name] = {'xmin': np.inf, 'xmax': -np.inf,
                                        'ymin': np.inf, 'ymax': -np.inf}

        # Collect all coords of all planes and nodes on each layer
        # Scan all shapes
        if zoom:
            for shape in self.db.shapes.values():
                coords_per_layer[shape.layer]['xmin'] = min(coords_per_layer[shape.layer]['xmin'],
                                                            min(shape.xcoords))
                coords_per_layer[shape.layer]['xmax'] = max(coords_per_layer[shape.layer]['xmax'],
                                                            max(shape.xcoords))
                coords_per_layer[shape.layer]['ymin'] = min(coords_per_layer[shape.layer]['ymin'],
                                                            min(shape.ycoords))
                coords_per_layer[shape.layer]['ymax'] = max(coords_per_layer[shape.layer]['ymax'],
                                                            max(shape.ycoords))

            # Scan all nodes
            for node in self.db.nodes.values():
                coords_per_layer[node.layer]['xmin'] = min(coords_per_layer[node.layer]['xmin'],
                                                            node.x)
                coords_per_layer[node.layer]['xmax'] = max(coords_per_layer[node.layer]['xmax'],
                                                           node.x)
                coords_per_layer[node.layer]['ymin'] = min(coords_per_layer[node.layer]['ymin'],
                                                          node.y)
                coords_per_layer[node.layer]['ymax'] = max(coords_per_layer[node.layer]['ymax'],
                                                            node.y)
    

        TasksBase.cmds.append(self.tcl.update_workflow('PowerDC', 'IRDropAnalysis'))
        for layer_name, coords, in coords_per_layer.items():
            if zoom:
                TasksBase.cmds.append(self.tcl.save_layout_view(path, layer_name,
                                                                (coords['xmin'],
                                                                coords['ymin'],
                                                                coords['xmax'],
                                                                coords['ymax']))
                                )
            else:
                TasksBase.cmds.append(self.tcl.save_layout_view(path, layer_name,
                                                                None)
                                )
    
    def crop_layout_views(self, path=None):
        '''Automatically crops the boarders of each image.

        :param path: Path where images are located, defaults to None.
        If None is provided the database location is used.
        :type path: str, optional
        '''

        path = os.path.join(self.db.path, 'layer_views') if path is None else path
        path = os.path.abspath(path)

        for pic_fname in glob.glob(os.path.join(path, '*.png')):
            im = Image.open(pic_fname)
            bg_im = Image.new(im.mode, im.size, 'black')
            diff = ImageChops.difference(im, bg_im)
            bbox = diff.getbbox()
            if bbox:
                crop_im = im.crop((bbox[0] + 1, bbox[1] + 1,
                                    bbox[2] - 1, bbox[3] - 1))
                bg_im = Image.new(crop_im.mode, crop_im.size, 'black')
                diff = ImageChops.difference(crop_im, bg_im)
                crop_im = crop_im.crop(diff.getbbox())
                crop_im.save(pic_fname)
            else:
                logger.warning(f'Image {pic_fname} has no content')


class ClarityTask(TasksBase):

    def __init__(self, db_fname):
        
        super().__init__(db_fname)

    def place_ports(self, pwr_net, num_ports,
                    ref_z=1, sw_ports='VXBR*', from_boxes=False):
        '''Automatically place ports on the output plane and the switching nodes.
        The width of the 3D ports is calculated to approximately maintain a ratio of 2
        between width and length.

        :param pwr_net: Name of the output plane net
        :type pwr_net: str
        :param num_ports: The required number of ports on the output plane
        :type num_ports: int
        :param ref_z: The required reference impedance of the ports, defaults to 1
        :type ref_z: int, optional
        :param sw_ports: The keyowrd to find switching nodes, defaults to 'VXBR*'
        :type sw_ports: str, optional
        :param from_boxes: Specifies how to create the output plane ports.
        If False, ports are placed randomally based on the number provided,
        otherwise, boxes placed in the database are used to placed the ports, defaults to False
        :type from_boxes: bool, optional
        '''

        layer = self.db.layer_names(verbose=False)[0]
        ind_ports = pm.PortGroup(self.db)

        if from_boxes:
            ind_ports = ind_ports.boxes_to_ports(port3D=True)
        else:
            ind_ports = ind_ports.auto_port(layer, pwr_net, num_ports,
                                            ref_z=ref_z, port3D=True)
    
        for idx, port in enumerate(ind_ports.ports, 1):
            port.name = f'Vout{idx}'
        ind_ports.add_ports(save=False)

        sw_nets = ind_ports.db.rail_names(sw_ports, enabled=True, verbose=False)
        for idx, sw_net in enumerate(sw_nets, 1):
            ind_ports = ind_ports.auto_port(layer, sw_net, 1,
                                            ref_z=ref_z, port3D=True)
            ind_ports.ports[0].name = f'SW{idx}'
            ind_ports.add_ports(save=False)

    def setup_clarity_sim1(self, delete_below_layer='Signal$2b',
                           sim_temp=110,
                            sol_freq=1e9, fmin=0, fmax=1e9,
                            magnetic=True, sw_freq=90e6,
                            order=0, void_size=1e-6
                        ):
        '''Create tcl commands to setup Calrity 3D extraction simulation.

        :param delete_below_layer: Layer name below which all layers are deleted
        , defaults to 'Signal$2b'
        :type delete_below_layer: str, optional
        :param sim_temp: Simulation temperature, defaults to 110
        :type sim_temp: int, optional
        :param sol_freq: Frequency at which an adaptive solution is performed,
        typically set to maximum frequency, defaults to 1e9
        :type sol_freq: float, optional
        :param fmin: Minimum frequency of interest, defaults to 0
        :type fmin: float, optional
        :param fmax: Maximum frequency of interest, defaults to 1e9
        :type fmax: float, optional
        :param magnetic: If True designates that package inductor is using magnetic material,
        otherwise assumed an air core package inductor, defaults to True
        :type magnetic: bool, optional
        :param sw_freq: Switching frequency of the FIVR, defaults to 90e6
        :type sw_freq: float, optional
        :param order: Basis function order used to represent electric field.
        Can accept 0 or 1, defaults to 0
        :type order: int, optional
        :param void_size: Voide size in Meters. Void smaller than the provided size
        will be filled and ignored during meshing, defaults to 1e-6
        :type void_size: float, optional
        '''

        layers = list(self.db.stackup.keys())
        layers_to_delete = layers[layers.index(delete_below_layer)+1:]              
        
        TasksBase.cmds += [
                            self.tcl.delete_layers(*layers_to_delete),
                            self.tcl.enforce_cuasality(),
                            self.tcl.enable_debye_model() if magnetic else '',
                            self.tcl.setup_3d_freq(sol_freq, fmin, fmax, sw_freq, magnetic),
                            self.tcl.setup_3d_solver(order),
                            self.tcl.set_global_temp(sim_temp),
                            self.tcl.setup_3d_passivity(),
                            self.tcl.set_output_format(),
                            self.tcl.setup_3d_voids(void_size),
                            self.tcl.setup_poly_simplification()
        ]
        
    def setup_clarity_sim2(self, num_cores=2, mesh='XMesh'):
        """
        Setup Clarity simulation resources, deletes input rail on the top surface,
        and sets simulation volume box.

        :param num_cores: Number of cores to use to run the 3D extraction
        crossing over input rail, defaults to 2
        :type num_cores: int, optional
        :param mesh: Defines which algorithem is used for meshing.
        Can only accept 'XMesh' or 'DMesh'. Recommended to use XMesh for large rails.
        For example, layout area > 10x10 mm^2 and number of port > 100.
        XMesh is a massively distributed meshing technology that can be
        distributed to multiple CPUs. It is applied during the initial mesh generation. 
        XMesh shows significant performance improvement when extracting large domains.
        XMesh or DMesh can be used if layout is relatively small, i.e., a single core.,
        defaults to 'XMesh'
        :type mesh: str, optional
        """

        db_z = 2*(sum([layer.thickness for layer in self.db.stackup.values()]))
        db_y = 0.5*(self.db.db_y_top_right - self.db.db_y_bot_left)
        db_x = 0.5*(self.db.db_x_top_right - self.db.db_x_bot_left)

        TasksBase.cmds += [self.tcl.setup_resources(num_cores),
                            self.tcl.setup_3d_geometry(db_x, db_y, db_z, mesh)]


    def delete_metal(self, input_rail, fname_db=None, save=True):
        '''Deletes and removes vias and shapes of a specific net only on the top layer.

        :param input_rail: Name of the input rail to the FIVR.
        This rail will be removed from the surface layer to avoid ports
        crossing over input rail, defaults to 'VCCIN'
        :type input_rail: str, optional
        :param fname_db: File name to save the new layout
        with the metal removed, defaults to None
        :type fname_db: str, optional
        '''

        top_layer = self.db.layer_names(verbose=False)[0]
        # Find vias and shapes of "input_rail" in order to delete them
        vias = [via.name for via in self.db.vias.values()
                    if via.net_name == input_rail
                    and via.upper_layer == top_layer]
        shapes = [shape.name for shape in self.db.shapes.values()
                    if shape.net_name == input_rail
                    and shape.layer == top_layer]
        traces = [trace.name for trace in self.db.traces.values()
                    if trace.rail == input_rail
                    and trace.layer == top_layer]
        nodes = [node.name for node in self.db.nodes.values()
                    if node.rail == input_rail
                    and node.layer == top_layer
                    and node.type == 'pin']

        # Remove nodes from any component it is connected to
        # This will allow the nodes to be deleted
        line_gen = self.db.extract_block('* Component description lines',
                                        '.EndCompCollection')
        for idx, line in line_gen:
            try:
                if line.split('$Package.')[1].split('::')[0] in nodes:
                    self.db.lines[idx] = f'* {line}'
            except IndexError:
                pass
        
        if save:
            self.db.save(fname_db)

        return [self.tcl.delete_shapes(*shapes) if shapes else '',
                self.tcl.delete_traces(*traces) if traces else '',
                self.tcl.delete_vias(*vias) if vias else '',
                self.tcl.delete_nodes(*nodes) if nodes else '']


class PsiTask(TasksBase):

    def __init__(self, db_fname):
        
        super().__init__(db_fname)

    def setup_psi_sim(self, sim_temp=100, start_freq=0, end_freq=1e9):

        TasksBase.cmds += [self.tcl.set_output_format(),
                        self.tcl.set_global_temp(sim_temp),
                        self.tcl.enable_DC_point(),
                        self.tcl.set_sim_freq(start_freq, end_freq)
                ]


class PdcTask(TasksBase):
    '''This class handles all tasks related to PowerDC setup and report generation
    and processing. It inherits from the base class :class:`tasks.TasksBase()`

    :param TasksBase: Base class that handles all common tasks operations of the different flows
    :type TasksBase: :class:`tasks.TasksBase()`
    '''

    def __init__(self, db_fname=None):
        '''Initializes the generated object.

        :param db_fname: File name or an object of the layout, defaults to None
        :type db_fname: str or :class:`speed.Database()`, optional
        '''
        
        super().__init__(db_fname)

    def export_ldo_setup(self, fname=None):
        '''Generate .csv file with the database LDO information.
        This file can be updated by the user in order to modify the LDO setup.
        It can then be used to modify LDO setup in the database by :method:`tasks.PdcTask.import_ldo_setup()`

        :param fname: CSV file name of the exported LDO setup, defaults to None.
        If not given, a file name is constructed from the database name followed by ``_ldosetup``.
        :type fname: str, optional
        '''

        fname = os.path.join(self.db.path,
                    f"{self.db.name.split('.')[0]}_ldosetup.csv") if fname is None else fname
        
        data = {'LDO Name': [], 'Sink Name': [],
                'Sink Nominal Voltage [V]': [],
                'VRM Name': [],
                'VRM Nominal Voltage [V]': [],
                'Sense Voltage [V]': [], 'Output Current [A]': [],
                'Conversion Rate [%]': []}
        aliases = {'NominalVoltage': 'VRM Nominal Voltage [V]',
                    'SenseVoltage': 'Sense Voltage [V]',
                    'OutputCurrent': 'Output Current [A]',
                    'DCDCUsedConvertRate': 'Conversion Rate [%]'}
        
        line_gen = self.db.extract_block('* PdcElem description lines',
                                        '* ConstraintDisc description lines')
        
        for _, line in line_gen:
            if '.DCDC' in line:
                dcdc_name = line.split('Name = ')[1].split()[0].strip('"')
                input_sink = line.split('In = ')[1].split()[0]
                output_vrm = line.split('Out = ')[1].split()[0].strip()
    
                data['LDO Name'].append(dcdc_name)
                data['Sink Name'].append(input_sink)
                data['VRM Name'].append(output_vrm)
            elif '.Sink' in line and 'IsForDCDC = 1' in line:
                if 'NominalVoltage' in line:
                    data['Sink Nominal Voltage [V]'].append(
                        float(line.split('NominalVoltage = ')[1].split()[0])
                    )
                else:
                    data['Sink Nominal Voltage [V]'].append(0)
            elif '.VRM' in line and 'IsForDCDC = 1' in line:
                for prop, alias in aliases.items():
                    if prop in line:
                        prop_value = float(line.split(f'{prop} = ')[1].split()[0])
                    else:
                        prop_value = 100 if alias == 'DCDCUsedConvertRate' else 0
                    data[alias].append(prop_value)

        df = pd.DataFrame(data)
        df.insert(1, 'New LDO name', ['']*len(df))
        df.insert(3, 'New sink name', ['']*len(df))
        df.insert(6, 'New VRM name', ['']*len(df))
        df.to_csv(fname, index=False)

        return df

    def import_ldo_setup(self, fname):
        '''Import .csv file and update database with the updated LDO setup parameters.
        The template of this file can be generated by :method:`tasks.PdcTask.export_ldo_setup()`.

        :param fname: CSV file name that contains the modified LDO setup parameters
        :type fname: str
        '''

        ldo_data = pd.read_csv(fname).fillna('').to_dict(orient='list')

        for prev_name, new_name in zip(['LDO Name', 'Sink Name', 'VRM Name'],
                                          ['New LDO name', 'New sink name', 'New VRM name']):
            for idx, new in enumerate(ldo_data[new_name]):
                if new != '':
                    ldo_data[prev_name][idx] = new

        line_gen = self.db.extract_block('* PdcElem description lines',
                                        '* ConstraintDisc description lines')
        
        ldo_idx, vrm_idx, sink_idx = 0, 0, 0
        for idx_line, line in line_gen:
            if '.DCDC' in line:
                self.db.lines[idx_line] = (f".DCDC Name = \"{ldo_data['LDO Name'][ldo_idx]}\" "
                                        f"In = {ldo_data['Sink Name'][ldo_idx]} "
                                        f"Out = {ldo_data['VRM Name'][ldo_idx]}\n"
                                    )
                ldo_idx += 1
            elif '.Sink' in line and 'IsForDCDC = 1' in line:
                self.db.lines[idx_line] = (f".Sink NominalVoltage = {ldo_data['Sink Nominal Voltage [V]'][sink_idx]} "
                                        f"Model = 1 IsForDCDC = 1 "
                                        f"Name = \"{ldo_data['Sink Name'][sink_idx]}\"\n"
                                    )
                sink_idx += 1
            elif '.VRM' in line and 'IsForDCDC = 1' in line:
                self.db.lines[idx_line] = (f".VRM NominalVoltage = {ldo_data['VRM Nominal Voltage [V]'][vrm_idx]} "
                                        f"SenseVoltage = {ldo_data['Sense Voltage [V]'][vrm_idx]} "
                                        f"OutputCurrent = {ldo_data['Output Current [A]'][vrm_idx]} "
                                        f"IsForDCDC = 1 "
                                        f"DCDCUsedConvertRate = {ldo_data['Conversion Rate [%]'][vrm_idx]} "
                                        f"Name = \"{ldo_data['VRM Name'][vrm_idx]}\"\n"
                                    )
                vrm_idx += 1

    def export_vrm_setup(self, fname=None):
        '''Generate .csv file with the database VRM names and related information.
        This file can be updated by the user in order to modify the VRM setup.
        It can then be used to modify VRM setup in the database by :method:`tasks.PdcTask.import_vrm_setup()`

        :param fname: File name of the exported VRM setup, defaults to None.
        If not given, a file name is constructed from the database name followed by ``_vrmsetup``.
        :type fname: str, optional
        '''
        
        if fname is None:
            fname = Path(self.db.path) / Path(f'{Path(self.db.name).stem}_vrmsetup.csv')
        
        data = {'Name = ': [], 'NominalVoltage = ': [],
                'OutputCurrent = ': [], 'SenseVoltage = ': [],
                '"Positive Sense Pin" .Node Name = ': [],
                '"Negative Sense Pin" .Node Name = ': []}

        line_gen = self.db.extract_block('* PdcElem description lines',
                                        '* ConstraintDisc description lines')
        for _, line in line_gen:
            if '.VRM ' in line and 'IsForDCDC = 1' not in line:
                block = []
                while '.EndVRM' not in line:
                    block.append(line.strip())
                    _, line = next(line_gen)
                block = ' '.join(block)
                for key in data.keys():
                    try:
                        data[key].append(block.split(key)[1].split()[0].strip('"'))
                    except IndexError:
                        data[key].append(None)

        df = pd.DataFrame(data)
        df.insert(1, 'New name', ['']*len(df))
        df.columns = ['Name', 'New name', 'Nominal Voltage [V]', 'Output Current [A]',
                        'Sense Voltage [V]', 'Positive Sense Pin',
                        'Negative Sense Pin']
        df.to_csv(fname, index=False)

        return df

    def export_sink_setup(self, fname=None):
        '''Generate .csv file with the database sink names and related information.
        This file can be updated by the user in order to modify the sinks setup.
        It can then be used to modify sinks setup in the database by :class:`tasks.PdcTask.import_sink_setup()`

        :param fname: File name of the exported sink setup, defaults to None.
        If not given, a file name is contructed from the database name followed by ``_sinksetup``.
        :type fname: str, optional
        '''
        
        if fname is None:
            fname = Path(self.db.path) / Path(f'{Path(self.db.name).stem}_sinksetup.csv')
        
        data = {'Name = ': [], 'NominalVoltage = ': [],
                'Current = ': [], 'Model = ': []}
        num_to_name = {'1': 'Equal voltage', '2': 'Equal current', '3': 'Unequal current'}

        line_gen = self.db.extract_block('* PdcElem description lines',
                                      '* ConstraintDisc description lines')
        for _, line in line_gen:
            if '.Sink ' in line and 'IsForDCDC = 1' not in line:
                block = []
                while '.EndSink' not in line:
                    block.append(line.strip())
                    _, line = next(line_gen)
                block = ' '.join(block)
                for key in data.keys():
                    try:
                        data[key].append(block.split(key)[1].split()[0].strip('"'))
                        if key == 'Model = ':
                            data[key].append(num_to_name[data[key].pop()])
                    except IndexError:
                        data[key].append(None)

        df = pd.DataFrame(data)
        df.insert(1, 'New name', ['']*len(df))
        df.columns = ['Name', 'New name', 'Nominal Voltage [V]', 'Current [A]', 'Model']
        df.to_csv(fname, index=False)

        return df

    def import_vrm_setup(self, fname, ignore_sense_points=False):
        '''Import .csv file and update database with the updated VRM setup parameters.
        The template of this file can be generated by :method:`tasks.PdcTask.export_vrm_setup()`.

        :param fname: File name that contains the modified VRM setup parameters
        :type fname: str
        :param ignore_sense_points: If True will ignore to import the sense points, defaults to False
        :type ignore_sense_points: bool, optional
        '''

        # Remove all occurances of positive and negative sense pins
        # so the new ones can be added
        if not ignore_sense_points:
            start_idx = self.db.lines.index('* PdcElem description lines\n') + 1
            new_lines = self.db.lines[:start_idx]
            line_gen = self.db.extract_block('* PdcElem description lines')
            for line_num, line in line_gen:
                if 'Positive Sense Pin' in line or 'Negative Sense Pin' in line:
                    while '.EndPin' not in line:
                        line_num, line = next(line_gen)
                else:
                    new_lines.append(line)
            self.db.lines = new_lines

        vrm_data = pd.read_csv(fname)

        # Import and populate VRM data
        data = defaultdict(dict)
        for index, row in vrm_data.iterrows():
            data[row['Name']]['new_name'] = row['New name']
            data[row['Name']]['nominal_voltage'] = row['Nominal Voltage [V]']
            data[row['Name']]['output_current'] = row['Output Current [A]']
            data[row['Name']]['sense_voltage'] = row['Sense Voltage [V]']
            data[row['Name']]['pos_sense_pin'] = row['Positive Sense Pin']
            data[row['Name']]['neg_sense_pin'] = row['Negative Sense Pin']

        line_gen = self.db.extract_block('* PdcElem description lines')
        for line_num, line in line_gen:
            if '.VRM ' in line:
                vrm_name = line.split('Name = ')[1].split()[0].strip('"')
                if vrm_name not in data:
                    continue

                updated_vrm_name = data[vrm_name]['new_name'] \
                                        if data[vrm_name]['new_name'] != '' \
                                        else vrm_name
                new_line = (f".VRM NominalVoltage = {data[vrm_name]['nominal_voltage']} "
                            f"SenseVoltage = {data[vrm_name]['sense_voltage']} "
                            f"OutputCurrent = {data[vrm_name]['output_current']} "
                            f'Name = "{updated_vrm_name}"\n')
                self.db.lines[line_num] = new_line
                if not ignore_sense_points:
                    new_lines = ['.Pin Name = "Positive Sense Pin"\n',
                                    f".Node Name = {data[vrm_name]['pos_sense_pin']}\n" \
                                                    if not pd.isna(data[vrm_name]['pos_sense_pin']) else '',
                                    '.EndPin\n',
                                    '.Pin Name = "Negative Sense Pin"\n',
                                    f".Node Name = {data[vrm_name]['neg_sense_pin']}\n" \
                                                    if not pd.isna(data[vrm_name]['neg_sense_pin']) else '',
                                    '.EndPin\n']
                    new_lines.reverse()
                    for new_line in new_lines:
                        self.db.lines.insert(line_num + 1, new_line)
            
    def import_sink_setup(self, fname):
        '''Import .csv file and update database with the updated sink setup parameters.
        The template of this file can be generated by :method:`tasks.PdcTask.export_sink_setup()`.

        :param fname: csv file name that contains the modified sink setup parameters
        :type fname: str
        '''

        sink_data = pd.read_csv(fname).fillna('')

        model_to_num = {
		    'Equal voltage': 1,
		    'Equal current': 2,
		    'Unequal current': 3
	    }
        data = defaultdict(dict)
        for index, row in sink_data.iterrows():
            data[row['Name']]['new_name'] = row['New name']
            data[row['Name']]['nominal_voltage'] = row['Nominal Voltage [V]']
            data[row['Name']]['current'] = row['Current [A]']
            data[row['Name']]['model'] = model_to_num[row['Model']]

        line_gen = self.db.extract_block('* PdcElem description lines',
                                      '* ConstraintDisc description lines')
        for line_num, line in line_gen:
            if '.Sink ' in line:
                sink_name = line.split('Name = ')[1].split()[0].strip('"')
                if sink_name not in data:
                    continue

                updated_sink_name = data[sink_name]['new_name'] \
                                        if data[sink_name]['new_name'] != '' \
                                        else sink_name
                new_line = (f".Sink NominalVoltage = {data[sink_name]['nominal_voltage']} "
                            f"Current = {data[sink_name]['current']} "
                            f"Model = {data[sink_name]['model']} "
                            f'Name = "{updated_sink_name}"\n')
                self.db.lines[line_num] = new_line

    def auto_copy_sinks(self, to_db, dx=None, dy=None):
        '''Copy sinks from source database to destination database.
        When dx and dy are left None, fully automatic copy is performed
        based on the pin field differences between the two databases.
        Alternatively, when dx and dy are provided, 
        semi-automatic copy is performed based on the x-axis and y-axis deltas.

        :param to_db: The database to which the sinks are copied
        :type to_db: :class:`speed.Database()`
        :param dx: Destionation minus the source of the
        x coordinate in meters, defaults to None
        :type dx: float, optional
        :param dy: Destionation minus the source of the
        y coordinate in meters, defaults to None
        :type dy: float, optional
        :return: Database with the coppied ports
        :rtype: :class:`pman.PortGroup()`
        '''

        if dx is None or dy is None:
            if self.db.get_conn('bottom') is None:
                logger.info(f'Socket circuit cannot be found at the bottom of the layout.\n'
                            f'Automatic copy is aborted.\n'
                            f'Use semi-manul approach by providing dx and dy differences.')
                return

        self.export_sink_setup(Path(self.db.path) / Path('sink_setup.csv'))

        # Save pre-existing ports in both databases
        existing_src_ports = self.db.ports
        self.db.ports = {}
        existing_dst_ports = to_db.ports
        to_db.ports = {}

        # Convert sinks to ports and then auto copy them
        db_ports = pm.PortGroup(self.db)
        db_ports = db_ports.sinks_to_ports()
        db_ports.add_ports(save=False)
        if dx is None or dy is None:
            db_sinks = db_ports.auto_copy(to_db)
        else:
            db_sinks = db_ports.copy(dx, dy, to_db)
        updated_ports_name = []
        for port in db_sinks.ports:
            port.name = '_'.join(port.name.split('_')[:-1])
            updated_ports_name.append(port)
        db_sinks.ports = updated_ports_name
        db_sinks.add_ports(save=False)

        # Convert coppied ports back to sinks
        db_sinks = PdcTask(db_sinks.db)
        db_sinks.ports_to_sinks()
        db_sinks.import_sink_setup(Path(self.db.path) / Path('sink_setup.csv'))
        db_sinks.db.prepare_plots(db_sinks.db.layer_names(verbose=False)[0])
        db_sinks.db.plot(db_sinks.db.layer_names(verbose=False)[0])
        
        # Restore pre-existing ports
        self.db.ports = existing_src_ports
        to_db.ports = existing_dst_ports
        db_sinks.db.ports = existing_dst_ports
        db_sinks = pm.PortGroup(db_sinks.db)
        db_sinks.add_ports(save=False)
        
        return db_sinks

    def auto_copy_vrms(self, to_db, dx=None, dy=None,
                       dx_sense=None, dy_sense=None):
        '''Copy vrms and their corresponding sense points (if exists)
        from source database to destination database.
        When dx and dy or dx_sense and dy_sense, are left None,
        fully automatic copy is performed based on the pin field
        differences between the two databases.
        Alternatively, when dx and dy, or dx_sense and dy_sense are provided, 
        semi-automatic copy is performed based on the x-axis and y-axis deltas.

        :param to_db: The database to which the sinks are copied
        :type to_db: :class:`speed.Database()`
        :param dx: Destionation minus the source of the
        x coordinate in meters, defaults to None
        :type dx: float, optional
        :param dy: Destionation minus the source of the
        y coordinate in meters, defaults to None
        :type dy: float, optional
        :param dx_sense: Destionation minus the source of the
        x coordinate of a sense point in meters, defaults to None
        :type dx_sense: float, optional
        :param dy_sense: Destionation minus the source of the
        y coordinate of a sense point in meters, defaults to None
        :type dy_sense: float, optional
        :return: Database with the coppied ports
        :rtype: :class:`pman.PortGroup()`
        '''

        if dx_sense is None:
            dx_sense = dx
        if dy_sense is None:
            dy_sense = dy

        if dx is None or dy is None:
            if self.db.get_conn('bottom') is None:
                logger.info(f'Socket circuit cannot be found at the bottom of the layout.\n'
                            f'Automatic copy is aborted.\n'
                            f'Use semi-manul approach by providing dx and dy differences.')
                return

        #self.export_vrm_setup(os.path.join(self.db.path, 'vrm_setup.csv'))

        # Save pre-existing ports in both databases
        existing_src_ports = self.db.ports
        self.db.ports = {}
        existing_dst_ports = to_db.ports
        to_db.ports = {}

        # Convert vrms and sense points to ports and then auto copy them
        db_ports = pm.PortGroup(self.db)

        db_sense_ports = db_ports.vrms_sense_to_ports(suffix='')
        if dx_sense is None or dy_sense is None:
            to_db_sense_ports = db_sense_ports.auto_copy(to_db)
        else:
            to_db_sense_ports = db_sense_ports.copy(dx_sense,
                                                    dy_sense,
                                                    to_db)
        sense_ports = {'_'.join(sp.name.split('_')[:-1]): sp
                       for sp in to_db_sense_ports.ports}

        db_ports = db_ports.vrms_to_ports()
        if dx is None or dy is None:
            to_db_vrms = db_ports.auto_copy(to_db)
        else:
            to_db_vrms = db_ports.copy(dx, dy, to_db)
        updated_ports_name = []
        for port in to_db_vrms.ports:
            port.name = '_'.join(port.name.split('_')[:-1])
            updated_ports_name.append(port)
        to_db_vrms.ports = updated_ports_name
        to_db_vrms.add_ports(save=False)
        
        # Convert coppied ports back to vrms
        to_db_vrms = PdcTask(to_db_vrms.db)
        to_db_vrms.ports_to_vrms(sense_points=sense_ports)

        self.export_vrm_setup(os.path.join(self.db.path, 'vrm_setup_src.csv'))
        to_db_vrms.export_vrm_setup(os.path.join(self.db.path, 'vrm_setup_dst.csv'))
        vrm_setup_src = pd.read_csv(os.path.join(self.db.path, 'vrm_setup_src.csv'))
        vrm_setup_dst = pd.read_csv(os.path.join(self.db.path, 'vrm_setup_dst.csv'))
        vrm_setup_src['Positive Sense Pin'] = vrm_setup_dst['Positive Sense Pin']
        vrm_setup_src['Negative Sense Pin'] = vrm_setup_dst['Negative Sense Pin']
        vrm_setup_src.to_csv(os.path.join(self.db.path, 'vrm_setup.csv'))
        (Path(self.db.path) / Path('vrm_setup_src.csv')).unlink()
        (Path(self.db.path) / Path('vrm_setup_dst.csv')).unlink()

        to_db_vrms.import_vrm_setup(os.path.join(self.db.path, 'vrm_setup.csv'))
        to_db_vrms.db.prepare_plots(to_db_vrms.db.layer_names(verbose=False)[0])
        to_db_vrms.db.plot(to_db_vrms.db.layer_names(verbose=False)[0])

        # Restore pre-existing ports
        self.db.ports = existing_src_ports
        to_db.ports = existing_dst_ports
        to_db_vrms.db.ports = existing_dst_ports
        to_db_vrms = pm.PortGroup(to_db_vrms.db)
        to_db_vrms.add_ports(save=False)

        return to_db_vrms

    def ports_to_sinks(self, port_fname=None, suffix=None):
        '''Uses ports to define sinks for PowerDC simulation.
        The existing ports are preserved in the database.

        :param port_fname: File name of the .csv file specifying port VRM/Sink assignment, defaults to None
        :type port_fname: str, optional
        :param suffix: Suffix to add to the sink name derived from the port name, defaults to None
        :type suffix:: str, optional
        '''

        if port_fname is None:
            use_ports = list(self.db.ports.values())
        else:
            port_assign = pd.read_csv(port_fname)
            use_ports = [self.db.ports[port_name]
                         for port_name, port_assign_to in zip(port_assign['Port Name'], port_assign['VRM/Sink'])
                         if not pd.isna(port_assign_to) and port_assign_to.lower() == 'sink'
                    ]

        self.place_sinks(layer=None, net_name=None,
                        num_sinks=None, use_ports=use_ports,
                        suffix=suffix)
        
        return [f'Sink {port.name}_{suffix} is placed between '
                f'{port.pos_rails[0]} and {port.neg_rails[0]} '
                f'at ({port.x_center:.3f} mm, {port.y_center:.3f} mm)'
                    for port in use_ports]

    def place_sinks(self, layer, net_name, num_sinks,
                    area=None, create_ports=False, ref_z=10,
                    use_ports=False, suffix=None, nodes_to_use=None):
        '''Automatically place sinks in the database based on the provided parameters.

        :param layer: Layer name on which the sinks are placed
        :type layer: str
        :param net_name: Net name to which the sinks are attached
        :type net_name: str
        :param num_sinks: Number of required sinks
        :type num_sinks: int
        :param area: Selected area where the sinks are placed, defaults to None.
        If not provided the entire databse area is used.
        :type area: tuple(float, float, float, float), optional
        :param create_ports: If True indicates to also create ports in the database 
        where the sinks are placed, defaults to False
        :type create_ports: bool, optional
        :param ref_z: Port reference impedance in Ohm, defaults to 10
        :type ref_z: float, optional
        :param use_ports: If True, indicating to use the existing ports
        to create the sinks, defaults to False
        :type use_ports: bool, optional
        :param suffix: Add suffix to the sink name, defaults to None
        :type suffix: str or None, optional
        :param nodes_to_use: Nodes to use to connect the sinks to, defaults to None
        :type nodes_to_use: list or None, optional
        :return: If ports are created a new database object is returned,
        otherwise nothing is returned
        :rtype: :class:`pman.PortGroup()`
        '''

        suffix = '' if suffix is None else f'_{suffix}'
    
        if not use_ports:
            db_ports = pm.PortGroup(self.db)
            db_ports = db_ports.auto_port(layer=layer, net_name=net_name,
                                            num_ports=num_sinks, area=area,
                                            ref_z=ref_z, nodes_to_use=nodes_to_use)
            sinks = db_ports.ports
        else:
            sinks = use_ports

        # Place sinks
        line_num = self.db.lines.index('* PdcElem description lines\n') + 1
        for sink in reversed(sinks):
            block = [f'.Sink NominalVoltage = 0 Current = 0 '
                    f'Model = 2 Name = "{sink.name}{suffix}"']
            block.append('.Pin Name = "Positive Pin"')
            for pos_node in sink.pos_nodes:
                block.append(f'.Node Name = {pos_node.name}::{pos_node.rail}')
            block.append('.EndPin')
            block.append('.Pin Name = "Negative Pin"')
            for neg_node in sink.neg_nodes:
                block.append(f'.Node Name = {neg_node.name}::{neg_node.rail}')
            block.append('.EndPin')
            block.append('.SinkCurrentSource')
            block.append('.EndSinkCurrentSource')
            block.append('.EndSink\n')
            for line_in_block in reversed(block):
                self.db.lines.insert(line_num, f'{line_in_block}\n')

        if not use_ports:
            db_ports.add_ports(save=create_ports)
            db_ports.db.prepare_plots(layer)
            db_ports.db.plot(layer)

        if create_ports:
            return db_ports

    def ports_to_vrms(self, port_fname=None, sense_points=None, suffix=None):

        if port_fname is None:
            port_vrms = list(self.db.ports.values())
        else:
            port_assign = pd.read_csv(port_fname).to_dict(orient='list')
            port_vrms = [self.db.ports[port_name]
                         for port_name, port_assign_to in zip(port_assign['Port Name'], port_assign['VRM/Sink'])
                         if not pd.isna(port_assign_to) and port_assign_to.lower() == 'vrm'
                    ]
            
        suffix = '' if suffix is None else f'_{suffix}'
        
        line_num = self.db.lines.index('* PdcElem description lines\n') + 1
        for vrm in reversed(port_vrms):
            block = [f'.VRM NominalVoltage = 0 SenseVoltage = 0 '
                        f'OutputCurrent = 0 Name = "{vrm.name}{suffix}"']
            block.append('.Pin Name = "Positive Pin"')
            for pos_node in vrm.pos_nodes:
                block.append(f'.Node Name = {pos_node.name}::{pos_node.rail}')
            block.append('.EndPin')
            block.append('.Pin Name = "Negative Pin"')
            for neg_node in vrm.neg_nodes:
                block.append(f'.Node Name = {neg_node.name}::{neg_node.rail}')
            block.append('.EndPin')
            block.append('.Pin Name = "Positive Sense Pin"')
            if sense_points is not None and vrm.name in sense_points:
                for pos_node in sense_points[vrm.name].pos_nodes:
                    block.append(f'.Node Name = {pos_node.name}::{pos_node.rail}')
            block.append('.EndPin')
            block.append('.Pin Name = "Negative Sense Pin"')
            if sense_points is not None and vrm.name in sense_points:
                for neg_node in sense_points[vrm.name].neg_nodes:
                    block.append(f'.Node Name = {neg_node.name}::{neg_node.rail}')
            block.append('.EndPin')
            block.append('.EndVRM\n')
            
            for line_in_block in reversed(block):
                self.db.lines.insert(line_num, f'{line_in_block}\n')

        return [f'VRM {port.name}{suffix} is placed between '
                f'{port.pos_rails[0]} and {port.neg_rails[0]} '
                f'at ({port.x_center:.3f} mm, {port.y_center:.3f} mm)'
                    for port in port_vrms]
        
    def place_vrms(self, layer, net_name=None, find_comps='*L*',
                    create_ports=False, only_ports=False, ref_z=10):
        '''Automatically place VRMs based on the provided parameters.

        :param layer: Layer name on which the VRMs are placed
        :type layer: str
        :param net_name: Net name to which the VRMs are attached.
        Can also use wildcard
        :type net_name: str or list[str]
        :param find_comps: Search string that can include wildcards
        to find the inductors of the repective VRMs, defaults to '*L*'
        :type find_comps: str, optional
        :param create_ports: if True indicates to also create ports in the database 
        where the VRMs are placed, defaults to False
        :type create_ports: bool, optional
        :param only_ports: if True indicates to only create ports
        without placing the VRMs.
        In this case, the value of 'create_ports' does not matter, defaults to False
        :type only_ports: bool, optional
        :param ref_z: Port reference impedance in Ohm, defaults to 10
        :type ref_z: float, optional
        :return: If ports are created, create_ports is True or only_ports is True,
        a new database object is returned, otherwise nothing is returned
        :rtype: :class:`pman.PortGroup()`
        '''

        # Find inductor components connected to a given net
        other_nodes = defaultdict(list)
        pos_nodes = defaultdict(list)
        rail_names_found = set()
        nets = self.db.rail_names(find_nets=net_name, enabled=True, verbose=False)
        for ind_comp in self.db.find_comps(find_comps, verbose=False):
            for node_name in ind_comp.nodes:
                if (self.db.nodes[node_name].layer == layer
                    and self.db.nodes[node_name].rail is not None
                    and self.db.nodes[node_name].rail in nets):
                    rail_names_found.add(self.db.nodes[node_name].rail)
                    pos_nodes[ind_comp.name].append(self.db.nodes[node_name])
                    for node in ind_comp.nodes:
                        if not self.db.nodes[node].rail in nets:
                            #and self.db.nodes[node].rail is not None):
                            other_nodes[ind_comp.name].append(
                                        (self.db.nodes[node].rail,
                                        np.sqrt((self.db.nodes[node].x
                                                - pos_nodes[ind_comp.name][0].x)**2
                                        + (self.db.nodes[node].y
                                            - pos_nodes[ind_comp.name][0].y)**2))
                                    )

        for net in nets:
            if net not in rail_names_found:
                logger.warning(f'Cannot find inductor(s) connected to net {net}. '
                               f'Ports cannot be placed.')
            else:
                logger.info(f'Placing ports on net {net}')
        if not other_nodes:
            logger.warning('Cannot find inductors or nets connected to the inductors')
            return
        
        # Find maximum distance between indcutor power node and other nodes
        # This is required for 4 terminal inductors that are used for TLVR
        # But also works for 2 terminal inductors
        rail_ind = defaultdict(list)
        for ind_name, dist in other_nodes.items():
            max_dist = max(dist, key=itemgetter(1))
            rail_ind[max_dist[0]].append(ind_name)

        # Find components on layer that are not the inductors found in the previous step
        comps_on_layer = [comp for comp in self.db.connects.values()
                            if self.db.connects[comp.name].nodes
                            and self.db.components.get(comp.name, False)
                            and self.db.components[comp.name].start_layer == layer
                            and comp.name not in pos_nodes]
        
        # Find negative pins located on the components that connect to the inductors
        neg_nodes = defaultdict(list)
        self.comps_by_rail = defaultdict(list)
        for comp in comps_on_layer:                   
            for comp_node in comp.nodes:
                node_rail = self.db.nodes[comp_node].rail
                if node_rail is None:
                    continue
                if node_rail in rail_ind:
                    self.comps_by_rail[pos_nodes[rail_ind[node_rail][0]][0].rail].append(comp.name)
                    for node in comp.nodes:
                        if (self.db.nodes[node].rail is not None
                            and ('gnd' in self.db.nodes[node].rail.lower()
                                or 'vss' in self.db.nodes[node].rail.lower())
                            and self.db.net_names[self.db.nodes[node].rail][0]): # Last condition checks the rail is enabled
                            neg_nodes[rail_ind[node_rail][0]].append(self.db.nodes[node])
                    break

        # The following addresses the case when database is immature
        # and power MOSFETs are missing
        # Find all ground nodes on the layer:
        x_neg_nodes, y_neg_nodes = [], []
        all_nnodes = []
        for node in self.db.nodes.values():
            if (node.layer == layer
                and node.rail is not None
                and ('gnd' in node.rail.lower()
                    or 'vss' in node.rail.lower())):
                all_nnodes.append(node)
                x_neg_nodes.append(node.x)
                y_neg_nodes.append(node.y)

        neg_points = np.array([x_neg_nodes, y_neg_nodes]).T
        all_nnodes = np.array(all_nnodes)
        
        # Check if neg_nodes is empty for each inductor
        # If it is empty use the ground nodes under the outline of the inductor
        for ind_name in pos_nodes.keys():
            if ind_name not in neg_nodes:
                xc, yc = self.db.components[ind_name].xc, self.db.components[ind_name].yc
                rot_angle = self.db.components[ind_name].rot_angle
                ind_part = self.db.parts[self.db.connects[ind_name].part]
                x_outline, y_outline = ind_part.part_geom(xc, yc, rot_angle)
                coords = [[x, y] for x, y in zip(x_outline, y_outline)]
                polygon = mpltPath.Path(coords)
                points_within = polygon.contains_points(neg_points)
                neg_nodes[ind_name] = list(all_nnodes[points_within])

        # Create VRM ports
        new_ports = []
        port_props = {}
        ind_rail = {}
        for rail, ind_names in rail_ind.items():
            for ind_name in ind_names:
                ind_rail[ind_name] = rail
        for idx, (ind_name, pnodes) in enumerate(pos_nodes.items(), 1):
            ind_pos_rail = pnodes[0].rail
            try:
                phase = re.findall(r'(PH\w+)_?[0-9]*', ind_rail[ind_name])[0]
            except (TypeError, IndexError): # Catch when inductor rail is None or net name does have phase in it
                phase = None
            port_props['port_name'] = f'VRM_{ind_pos_rail}_{phase}' if phase \
                                        else f'VRM_{ind_pos_rail}_PH{idx}'
            port_props['port_width'] = None
            port_props['ref_z'] = ref_z
            port_props['pos_nodes'] = pnodes
            port_props['neg_nodes'] = neg_nodes[ind_name]
            new_ports.append((port_props['port_name'], spd.Port(port_props)))

        # Sort ports by name
        new_ports = sorted(new_ports, key=itemgetter(0), reverse=False)
        new_ports = [port for (port_name, port) in new_ports]
        
        if not only_ports:
            # Place VRMs
            line_num = self.db.lines.index('* PdcElem description lines\n') + 1
            for vrm in new_ports:
                block = [f'.VRM NominalVoltage = 0 SenseVoltage = 0 '
                            f'OutputCurrent = 0 Name = "{vrm.name}"']
                block.append('.Pin Name = "Positive Pin"')
                for pos_node in vrm.pos_nodes:
                    block.append(f'.Node Name = {pos_node.name}::{pos_node.rail}')
                block.append('.EndPin')
                block.append('.Pin Name = "Negative Pin"')
                for neg_node in vrm.neg_nodes:
                    block.append(f'.Node Name = {neg_node.name}::{neg_node.rail}')
                block.append('.EndPin')
                block.append('.Pin Name = "Positive Sense Pin"')
                block.append('.EndPin')
                block.append('.Pin Name = "Negative Sense Pin"')
                block.append('.EndPin')
                block.append('.EndVRM\n')
                for line_in_block in reversed(block):
                    self.db.lines.insert(line_num, f'{line_in_block}\n')

            db_vrms = pm.PortGroup(self.db, new_ports)
            db_vrms.add_ports(save=create_ports)
            db_vrms.db.prepare_plots(layer)
            db_vrms.db.plot(layer)

            if create_ports:
                return db_vrms
        else:
            return pm.PortGroup(self.db, new_ports)

    def pdc_setup(self, sim_temp=100, shape_process=False):
        '''Creates tcl commands to setup PowerDC simulation.

        :param sim_temp: Simulation temperature, defaults to 25
        :type sim_temp: float, optional
        '''

        # Search for smb layer to delete it
        smb_layer_name = None
        for layer_name in self.db.stackup.keys():
            if 'smb' in layer_name:
                smb_layer_name = layer_name
                break

        TasksBase.cmds += [self.tcl.delete_layers(smb_layer_name) \
                                        if smb_layer_name is not None else '',
                            self.tcl.bypass_confirmation(),
                            self.tcl.add_nodes_to_pads(),
                            self.tcl.set_global_temp(sim_temp),
                            self.tcl.setup_constraints(),
                            self.tcl.save_pdc_results(),
                            self.tcl.shape_process() if shape_process else ''
                ]
        
        connectors = [connector.name for connector in self.db.find_comps('*ConnectorCkt*', verbose=False)]
        if connectors:
            TasksBase.cmds.append(self.tcl.enable_components(*connectors))

    def sink_heatmaps(self, xml_data, sink_map_file, report_name):

        _, results = self._load_xml(xml_data)
        sink_results = results['sinks'][['Name', 'ActualVoltage',
                        'PositivePinVoltageAvg',
                        'NegativePinVoltageAvg']]
        sink_results.set_index('Name', drop=True, inplace=True)
        #sink_results.to_csv(r'..\thinkpi_test_db\DMR\temp_data.csv')

        heatmaps = ld.Waveforms()
        #heatmaps.load_waves(r'..\thinkpi_test_db\DMR\temp_data.csv')
        heatmaps.heatmap_vec(
            port_map_file=sink_map_file,
            vec_file=sink_results,
            heatmap_fname=report_name
        )
        

    def _dict_str_to_float(self, d):
        '''Converts string values in a dictionary to float if possible.

        :param d: Any one level dictionary
        :type d: dict
        :return: Dictionary with strings convereted to floats if possible
        :rtype: dict
        '''

        new_dict = {}
        for key, val in d.items():
            try:
                new_dict[key] = float(val)
            except ValueError:
                    new_dict[key] = val

        return new_dict
    
    def _load_xml(self, xml_fname):
        """Loads and parses xml file.

        :param xml_fname: xml File name
        :type xml_fname: str
        :return: Parsed raw data
        :rtype: dict[pandas.DataFrame]
        """        

        tree = ET.parse(xml_fname)
        root = tree.getroot()

        data_xpaths = {'plane_current_density': './GlobalPlaneCurrentDensity/*',
                        'via_current': './GlobalViaCurrentResults/*',
                        'power_loss': './PowerLoss/*',
                        'sinks': './SINKResults/SINK',
                        'sink_pin_voltages': './SINKResults/SINK/TopologyPlot',
                        'vrms': './VRMResults/*',
                        'via_temperature': './ThermalGlobalViaTemperatureResults/*',
                        'plane_temperature': './ThermalGlobalPlaneTemperatureResults/*'
                    }
                        
        raw_data = {}
        for data_type, xpath in data_xpaths.items():
            extracted_data = root.findall(xpath)
            extracted_data = [self._dict_str_to_float(details.attrib) for details in extracted_data]
            if extracted_data:
                raw_data[data_type] = pd.DataFrame.from_dict(extracted_data)

        # Combine all sinks data
        raw_data['sinks'] = pd.concat([raw_data['sinks'], raw_data['sink_pin_voltages']], axis=1)
        del raw_data['sink_pin_voltages']
       
        return root, raw_data
    
    def _load_raw_results(self, xml_fname, dist_path=None):
        """Loads and parses raw xml and txt simulation files.

        :param xml_fname: xml File name
        :type xml_fname: str
        :param dist_path: Distribution folder path, defaults to None
        :type dist_path: None or str, optional
        :return: Parsed raw data
        :rtype: tuple[dict, dict, dict]
        """        

        root, raw_data = self._load_xml(xml_fname)

        # Extract pin data (if exists) assuming there might be more then 1 connector
        pins_data = {}
        for connector in self.db.find_comps('*ConnectorCkt*', verbose=False):
            pins_xpath = f'./OTHERResults/OTHERCIRCUIT/[@Name="{connector.name}"]/*'
            pins_info_xpath = f'./OTHERResults/OTHERCIRCUIT/[@Name="{connector.name}"]/Pin/Map/*'

            extracted_data = root.findall(pins_xpath)
            extracted_data = [self._dict_str_to_float(details.attrib) for details in extracted_data]
            pins = pd.DataFrame.from_dict(extracted_data)
            extracted_data = root.findall(pins_info_xpath)
            extracted_data = [self._dict_str_to_float(details.attrib) for details in extracted_data]
            pins_info = pd.DataFrame.from_dict(extracted_data)

            pins_data[connector.name] = pd.merge(pins, pins_info,
                                                left_index=True,
                                                right_index=True)
        
        for conn_name, pins in pins_data.copy().items():
            pins = pins.rename(columns={'Name_x': 'PinName',
                                        'Name_y': 'NodeName'} 
                            )
            pins['ActualCurrent'] = pins['ActualCurrent'].abs()*1000
            pins['ActualVoltage'] *= 1000
            pins_data[conn_name] = pins
        
        raw_data['via_current']['ActualCurrent'] = (
            raw_data['via_current']['ActualCurrent'].abs()*1000
        )
        raw_data['plane_current_density']['ActualMaxCurrentDensity'] /= 1e6

        volt_dist = None
        if dist_path is not None:
            volt_dist = {'Layer Name': [], 'Min. Voltage [mV]': [],
                        'Max. Voltage [mV]': [], 'Spread [mV]': []}
            for dist_fname in glob.glob(os.path.join(dist_path, 'Voltage_*.txt')):
                with open(dist_fname, 'rt') as f:
                    dist = f.read()
                data = re.findall(r'-?[0-9]?\.[0-9]*[E, e][+, -][0-9]{2}', dist)
                data = np.array(data, dtype=float)*1000
                volt_dist['Layer Name'].append(dist.split('!Metal Layer: ')[1].split('\n')[0])
                if data.any():
                    volt_dist['Max. Voltage [mV]'].append(max(data))
                    volt_dist['Min. Voltage [mV]'].append(min(data))
                    volt_dist['Spread [mV]'].append(max(data) - min(data))
                else:
                    volt_dist['Max. Voltage [mV]'].append(None)
                    volt_dist['Min. Voltage [mV]'].append(None)
                    volt_dist['Spread [mV]'].append(None)

        return raw_data, pins_data, volt_dist
    
    def dc_gradient(self, xml_fname, pwr_nets, cell_sizes, report_fname, top_layer_only=True):
        """Calculates DC gradient within the given cell sizes.
        Additionally, finds minimum and maximum voltages for a given power net.
        For each power net, Excel file is generated with the DC gradients
        for each cell size in seperate tabs.
        Finally, the grid with the DC gradients is plotted for each cell size.

        :param xml_fname: XML file name with the simulated data
        :type xml_fname: str
        :param pwr_nets: Power net names to perform the analysis.
        Can also include wildcards.
        :type pwr_nets: list[str]
        :param cell_sizes: The required cell sizes to calculate the DC gradients 
        :type cell_sizes: list[tuple]
        :param report_fname: Excel report name.
        Note that Thinkpi will add '_{net_name}_{layer_name}' to each name.
        :type report_fname: str
        :param top_layer_only: If True generates report for only the top layer,
        otherwise for all layers, defaults to True
        :type top_layer_only: bool, optional
        """        

        # Find enabled nets
        net_names = self.db.rail_names(find_nets=pwr_nets,
                                       enabled=True, verbose=False)
        logger.info('DC gradient analysis is performed on:')
        for net_name in net_names:
            logger.info(f'\t{net_name}')
        
        # Extract raw data
        logger.info('Loading and parsing XML file... ')
        tree = ET.parse(xml_fname)
        root = tree.getroot()
        
        # Arrange data
        nodes_by_net = defaultdict(list)
        xcoords_by_net = defaultdict(list)
        ycoords_by_net = defaultdict(list)
        volt_by_net = defaultdict(list)

        # top_layer = self.db.layer_names(verbose=False)[0]
        # if '$' not in top_layer:
        #     top_layer = self.db.layer_names(verbose=False)[1]

        if '$' in self.db.layer_names(verbose=False)[0]:
            layers = self.db.layer_names(verbose=False)
        else:
            layers = self.db.layer_names(verbose=False)[1:]
        if top_layer_only:
            layers = [layers[0]]
        for layer in layers:
            for data in [r'.//MapNode', r'.//Node']:
                extracted_data = root.findall(data)
                all_nodes = [self._dict_str_to_float(details.attrib) for details in extracted_data]
                for node in all_nodes:
                    for net_name in net_names:
                        if node['Name'].split('::')[1] == net_name and node['LayerName'] == layer:
                            nodes_by_net[node['Name'].split('::')[1]].append(node)
                            xcoords_by_net[node['Name'].split('::')[1]].append(node['PosX'])
                            ycoords_by_net[node['Name'].split('::')[1]].append(node['PosY'])
                            volt_by_net[node['Name'].split('::')[1]].append(node['ActualVoltage'])
                            break

            logger.info('Done')
            all_plot_grids = defaultdict(list)
            plot_min_max = {'vmin_x': [], 'vmin_y': [], 'min_volt': [],
                            'vmax_x': [], 'vmax_y': [], 'max_volt': []}
            for net_name in net_names:
                nodes = np.array(nodes_by_net[net_name])
                xcoords = np.array(xcoords_by_net[net_name])
                ycoords = np.array(ycoords_by_net[net_name])
                volts = np.array(volt_by_net[net_name])

                if not nodes.any():
                    logger.warning(f'No data is found for net {net_name} layer {layer}')
                    continue
                # Calculate total Vmin, Vmax, and spread
                nodes_volt = [(node['Name'].split('::')[0], volt, node['PosX'], node['PosY'])
                                for node, volt in zip(nodes, volts)]
                min_node, min_volt, min_x, min_y = min(nodes_volt, key=itemgetter(1))
                max_node, max_volt, max_x, max_y = max(nodes_volt, key=itemgetter(1)) 
                logger.info(f'Net {net_name} on layer {layer}')
                logger.info(f'\tVmin ({min_node}) '
                            f'= {min_volt:.3f} V, '
                            f'Vmax ({max_node}) '
                            f'= {max_volt:.3f} V, '
                            f'Spread = {(max_volt - min_volt)*1e3:.3f} mV')
                plot_min_max['vmin_x'].append(min_x)
                plot_min_max['vmin_y'].append(min_y)
                plot_min_max['min_volt'].append(f'Vmin = {min_volt:.3f} V')
                plot_min_max['vmax_x'].append(max_x)
                plot_min_max['vmax_y'].append(max_y)
                plot_min_max['max_volt'].append(f'Vmax = {max_volt:.3f} V')

                # Add artificial coordinates on the periphery of each bump pad
                # That will ensure to include the bump voltage even if only part of the bump 
                # is enclosed by the cell border
                num_pts = 36
                periph_xcoords, periph_ycoords, periph_volts = [], [], []
                for xcoord, ycoord, volt, node in zip(xcoords, ycoords, volts, nodes):
                    pad_name = self.db.nodes[node['Name'].split('::')[0]].padstack
                    try:
                        pad_radius = self.db.padstacks[pad_name][layer].regular_dim[0]
                    except KeyError:
                        periph_xcoords.append(xcoord)
                        periph_ycoords.append(ycoord)
                        periph_volts.append(volt)
                        continue
                    periph_xcoords += list(xcoord + np.cos(np.linspace(0, 360, num_pts)*(np.pi/180))*pad_radius)
                    periph_ycoords += list(ycoord + np.sin(np.linspace(0, 360, num_pts)*(np.pi/180))*pad_radius)
                    periph_volts += [volt]*num_pts

                xcoords = np.array(periph_xcoords)
                ycoords = np.array(periph_ycoords)
                volts = np.array(periph_volts)

                # Scan and find DC voltage gradients in each cell
                results = {}
                for (dx, dy) in cell_sizes:
                    plot_grid = {'x': [], 'y': [], 'w': [], 'h': [], 'grad': []}
                    min_x, min_y = np.min(xcoords), np.min(ycoords)
                    max_x, max_y = np.max(xcoords), np.max(ycoords)

                    # Cell coordinates
                    xsteps = list(np.arange(min_x - 2*pad_radius, max_x + dx, dx))
                    ysteps = list(np.arange(min_y - 2*pad_radius, max_y + dy, dy))

                    dc_grad = {'(Xbot_left, Ybot_left, Xtop_right, Ytop_right) [mm]': [],
                               'Vdc_min [V]': [], 'Vdc_max [V]': [], 'Vdc_grad [mV]': []}
                    grid = pd.DataFrame(columns=[f'({xbot_left*1e3:.3f}, {xtop_right*1e3:.3f})'
                                                for (xbot_left, xtop_right) in zip(xsteps[:-1], xsteps[1:])],
                                        index=[f'({ybot_left*1e3:.3f}, {ytop_right*1e3:.3f})'
                                                for (ybot_left, ytop_right) in list(zip(ysteps[:-1], ysteps[1:]))[::-1]])

                    for (ybot_left, ytop_right) in zip(ysteps[:-1], ysteps[1:]):
                        for (xbot_left, xtop_right) in zip(xsteps[:-1], xsteps[1:]):
                            dc_spread = volts[(xcoords >= xbot_left)
                                                & (xcoords <= xtop_right)
                                                & (ycoords >= ybot_left)
                                                & (ycoords <= ytop_right)
                                        ]
                            if dc_spread.size == 0:
                                continue
                            dc_grad['(Xbot_left, Ybot_left, Xtop_right, Ytop_right) [mm]'].append(
                                                    f'({xbot_left*1e3:.3f}, {ybot_left*1e3:.3f}, '
                                                    f'{xtop_right*1e3:.3f}, {ytop_right*1e3:.3f})'
                                            )
                            dc_grad['Vdc_min [V]'].append(round(np.min(dc_spread), 3))
                            dc_grad['Vdc_max [V]'].append(round(np.max(dc_spread), 3))
                            dc_grad['Vdc_grad [mV]'].append(round((np.max(dc_spread)
                                                                   - np.min(dc_spread))*1e3, 3))

                            plot_grid['x'].append((xtop_right + xbot_left)/2)
                            plot_grid['y'].append((ytop_right + ybot_left)/2)
                            plot_grid['w'].append(xtop_right - xbot_left)
                            plot_grid['h'].append(ytop_right - ybot_left)
                            plot_grid['grad'].append(f"{dc_grad['Vdc_grad [mV]'][-1]} mV")

                            grid.at[f'({ybot_left*1e3:.3f}, {ytop_right*1e3:.3f})',
                                    f'({xbot_left*1e3:.3f}, {xtop_right*1e3:.3f})'] = dc_grad['Vdc_grad [mV]'][-1]

                    all_plot_grids[f'{dx*1e3}x{dy*1e3}mm'].append(plot_grid)
                    results[f'{dx*1e3}x{dy*1e3}mm'] = (pd.DataFrame(dc_grad).sort_values('Vdc_grad [mV]',
                                                                                        ascending=False),
                                                        grid)

                fname = report_fname.replace(Path(report_fname).suffix,
                                             f'_{net_name}_{layer}{Path(report_fname).suffix}')
                with pd.ExcelWriter(fname) as writer:
                    for cell_size, result in results.items():
                        result[0].to_excel(writer, sheet_name=cell_size, index=False)
                        result[1].to_excel(writer, sheet_name=cell_size,
                                           startrow=0, startcol=len(result[0].columns) + 1)

            self.db.plot_grad_grid(all_plot_grids, plot_min_max, layer)

    def parse_sim_results(self, xml_fname, pwr_net, gnd_net,
                            dist_path=None, report_fname=None,
                            plot_ground=True, plot_scale=1, save=True,
                            raw_data=None, pins_data=None, volt_dist=None):
        '''Parsing and creating report for PowerDC simulation results based on xml file
        that is saved at the end of the simulation. Additionally,
        .txt files with voltage distributions are used.

        :param xml_fname: xml File name
        :type xml_fname: str
        :param pwr_net: Name of the power net for which the results are obtained
        :type pwr_net: str
        :param gnd_net: Name of the corresponding ground net
        :type gnd_net: str
        :param dist_path: Distribution folder path, defaults to None
        :type dist_path: str, optional
        :param report_fname: Report file name.
        If not given, database name is used with a _pdcreport suffix, defaults to None
        :type report_fname: str, optional
        :param plot_ground: If pins exist and True plots ground pins, defaults to True
        :type plot_ground: bool, optional
        :param plot_scale: Scaling multiplier to the phyiscal sizer of the pins, defaults to 1
        :type plot_scale: int, optional
        :param save: If True saves xlsx file as a report,
        otherwise returns the report as a dict, defaults to True
        :type save: bool, optional
        :param raw_data: Loaded and parsed data from the xml file, defaults to None
        :type raw_data: dict, optional
        :param pins_data: If pins exist, all pin currents per connector, defaults to None
        :type pins_data: dict, optional
        :param volt_dist: Minimum, maximum, and range of voltage distribution per layer, defaults to None
        :type volt_dist: dict, optional
        :return: If save is False, dictionary with pandas dataframes with the relevant results
        :rtype: dict[DataFrame]
        '''

        if report_fname is None:
            if self.db is None:
                report_fname = 'pdc_report.xlsx'
            else:
                report_fname = f'{os.path.join(self.db.path, self.db.name).split(".")[0]}_pdcreport.xlsx'

        if raw_data == None:
            raw_data, pins_data, volt_dist = self._load_raw_results(xml_fname, dist_path)
        
        extract_data = {'vrms': ['Name', 'NominalVoltage',
                                    'SenseVoltage', 'OutputNominalVoltage',
                                    'OutputCurrent', 'ActualCurrent'],
                        'sinks': ['Name', 'NominalVoltage', 'ActualVoltage',
                                    'PositivePinVoltageAvg',
                                    'NegativePinVoltageAvg',
                                    'Current']}
        results = {}

        # Sinks and VRMs
        for data_type, details in extract_data.items():
            results[data_type] = raw_data[data_type][details]

        # Power loss
        results['power_loss_summary'] = raw_data['power_loss'].iloc[0:6]
        results['power_loss_per_component'] = raw_data['power_loss'][raw_data['power_loss']['Name'].str.contains('Component', regex=False)].reset_index(drop=True)
        data_wo_components = raw_data['power_loss'][~raw_data['power_loss']['Name'].str.contains('Component', regex=False)]
        results['power_loss_per_layer'] = data_wo_components[data_wo_components['Name'].str.contains('$', regex=False)].reset_index(drop=True)
        results['power_loss_per_net'] = data_wo_components[~data_wo_components['Name'].str.contains('$', regex=False)].reset_index(drop=True)
        results['power_loss_per_net'] = results['power_loss_per_net'].iloc[6:].reset_index(drop=True)

        # Maximum via current and plane density per layer per net
        via_current = raw_data['via_current']
        plane_density = raw_data['plane_current_density']

        table_via_pwr, table_via_gnd = {}, {}
        table_plane_pwr, table_plane_gnd = {}, {}
        for layer_name in results['power_loss_per_layer']['Name']:
            via_max_current_pwr = via_current[((via_current['StartLayer'] == layer_name)
                                                | (via_current['EndLayer'] == layer_name))
                                                & (via_current['NetName'] == pwr_net)] 
            if not via_max_current_pwr.empty:
                via_max_current_pwr.reset_index(drop=True)
                via_max_current_pwr = via_max_current_pwr.loc[via_max_current_pwr['ActualCurrent'].idxmax()]
                table_via_pwr[layer_name] = via_max_current_pwr['ActualCurrent']

            via_max_current_gnd = via_current[((via_current['StartLayer'] == layer_name)
                                                | (via_current['EndLayer'] == layer_name))
                                                & (via_current['NetName'] == gnd_net)]
            if not via_max_current_gnd.empty:
                via_max_current_gnd.reset_index(drop=True)
                via_max_current_gnd = via_max_current_gnd.loc[via_max_current_gnd['ActualCurrent'].idxmax()]
                table_via_gnd[layer_name] = via_max_current_gnd['ActualCurrent']

            plane_max_density_pwr = plane_density[(plane_density['LayerName'] == layer_name)
                                                    & (plane_density['NetName'] == pwr_net)]
            if not plane_max_density_pwr.empty:
                plane_max_density_pwr.reset_index(drop=True)
                plane_max_density_pwr = plane_max_density_pwr.loc[plane_max_density_pwr['ActualMaxCurrentDensity'].idxmax()]
                table_plane_pwr[layer_name] = plane_max_density_pwr['ActualMaxCurrentDensity']

            plane_max_density_gnd = plane_density[(plane_density['LayerName'] == layer_name)
                                                    & (plane_density['NetName'] == gnd_net)]
            if not plane_max_density_gnd.empty:
                plane_max_density_gnd.reset_index(drop=True)
                plane_max_density_gnd = plane_max_density_gnd.loc[plane_max_density_gnd['ActualMaxCurrentDensity'].idxmax()]
                table_plane_gnd[layer_name] = plane_max_density_gnd['ActualMaxCurrentDensity']

        final_table = {'Layer Name': [], 'via_pwr_net': [], 'via_gnd_net': [],
                        'plane_pwr_net': [], 'plane_gnd_net': []}
        for layer_name in results['power_loss_per_layer']['Name']:
            data = [table_via_pwr.get(layer_name, ''),
                        table_via_gnd.get(layer_name, ''),
                        table_plane_pwr.get(layer_name, ''),
                        table_plane_gnd.get(layer_name, '')]
            if len(data) != data.count(''):
                final_table['Layer Name'].append(layer_name)
                final_table['via_pwr_net'].append(data[0])
                final_table['via_gnd_net'].append(data[1])
                final_table['plane_pwr_net'].append(data[2])
                final_table['plane_gnd_net'].append(data[3])

        df = pd.DataFrame(final_table)
        df.columns = [['Layer Name', 'Max. Via Current [mA]',
                        'Max. Via Current [mA]',
                        'Max. Plane Current Density [A/mm^2]',
                        'Max. Plane Current Density [A/mm^2]'],
                        ['', pwr_net, gnd_net, pwr_net, gnd_net]]
        results['via_plane_current'] = df

        # Bin pin currents for both power and ground
        for conn_name, pins in pins_data.items():
            for net_type, net_name in zip(['pwr', 'gnd'], [pwr_net, gnd_net]):
                pins_by_net = pins[(pins['NetName'] == net_name)
                                    & (pins['ActualCurrent'] < np.inf)]
                try:
                    bins = np.linspace(0, max(pins_by_net['ActualCurrent']), 6)
                except ValueError: # Catches when a net does not pass through a certain connector
                    break
                if bins[-1] > 1000:
                    bins = sorted(np.append(bins, 1000))
                results[f'{conn_name}_bins_{net_type}'] = pins_by_net.groupby(pd.cut(pins_by_net['ActualCurrent'],
                                                                        bins=bins)).size()
                results[f'{conn_name}_bins_{net_type}'] = results[f'{conn_name}_bins_{net_type}'].reset_index()
                results[f'{conn_name}_bins_{net_type}'].columns = [['Pin Current Bins [mA]', 'Count'],
                                                                    [net_name, '']]
                
        # Add thermal results if exist
        try:
            results['via_temperature'] = raw_data['via_temperature']
            results['via_temperature'].columns = ['Name', 'Temperature [⁰C]']
            results['plane_temperature'] = raw_data['plane_temperature'][::-1].reset_index(drop=True)
            results['plane_temperature'].columns = ['Name', 'Temperature [⁰C]']
        except KeyError:
            pass
            
        # Sort the distributions by ordered layers
        if dist_path is not None:
            if self.db is None:
                new_index = list(range(len(volt_dist['Layer Name'])))
            else:
                new_index = [self.db.layer_names(verbose=False).index(layer_name)
                                for layer_name in volt_dist['Layer Name']]
            results['volt_dist'] = pd.DataFrame(volt_dist)
            results['volt_dist'] = results['volt_dist'].set_index(pd.Index(new_index)).sort_index()

        # Plot socket pin current distribution if exists
        for conn_name, pins in pins_data.items():
            if plot_ground:
                pins_to_plot = pins[((pins['NetName'] == pwr_net)
                                    | (pins['NetName'] == gnd_net))
                                    & (pins['ActualCurrent'] < np.inf)]
            else:
                pins_to_plot = pins[(pins['NetName'] == pwr_net)
                                    & (pins['ActualCurrent'] < np.inf)]
            self.db.plot_pin_current(pins_to_plot, 'mm', 'black',
                                    f"{os.path.basename(report_fname).split('.')[0]}_{conn_name}.html",
                                    plot_scale)

        # Save results to Excel file with tabs
        if save:
            with pd.ExcelWriter(report_fname) as writer:
                for result_name, result in results.items():
                    if not result.empty:
                        result.to_excel(writer, sheet_name=result_name)

        return results
    
    def parse_fivr_results(self, xml_fname, dist_path=None, report_fname=None):
        '''Parsing and creating report for FIVR PowerDC simulation results based on xml file
        that is saved at the end of the simulation. Additionally,
        .txt files with voltage distributions are used.

        :param xml_fname: xml File name
        :type xml_fname: str
        :param dist_path: Distribution folder path, defaults to None
        :type dist_path: str, optional
        :param report_fname: Report file name
        If not given, database name is used with a _pdcreport suffix, defaults to None
        :type report_fname: str, optional
        
        '''

        raw_data, pins_data, volt_dist = self._load_raw_results(xml_fname, dist_path)

        logger.info('\nCreating report for the following nets:')
        logger.info(f'\t{self.pwr_nets[0]}')
        results = self.parse_sim_results(
                            xml_fname, self.pwr_nets[0], self.gnd_nets[0],
                            dist_path, report_fname,
                            True, 1, False,
                            raw_data, pins_data, volt_dist
                        )
        results[self.pwr_nets[0]] = results['via_plane_current']
        del results['via_plane_current']
        
        for pwr_net in self.pwr_nets[1:]:
            logger.info(f'\t{pwr_net}')
            result = self.parse_sim_results(
                            xml_fname, pwr_net, self.gnd_nets[0],
                            dist_path, report_fname,
                            True, 1, False,
                            raw_data, pins_data, volt_dist
                        )
            results[pwr_net] = result['via_plane_current']

        with pd.ExcelWriter(report_fname) as writer:
            for result_name, result in results.items():
                if not result.empty:
                    result.to_excel(writer, sheet_name=result_name)
        

class SocketElectroThermalTask(TasksBase):
    '''Class to setup the socket current capability
    electro-thermal analysis.

    :param TasksBase: Inherited base class
    :type TasksBase: :class:`tasks.TasksBase()`
    '''
    
    def __init__(self, db_fname=None):
        '''Initializes the generated object.

        :param db_fname: Database file name or database object, defaults to None
        :type db_fname: str or :class:`speed.Database()`, optional
        '''

        super().__init__(db_fname)
        self.pdc = PdcTask(self.db)
        # Copy material file from app to working directory
        if db_fname is not None:
            shutil.copy(_thinkpi_path / 'thinkpi' / 'config' / 'materials' / cfg.ET_LGA_MATERIAL_FILE,
                        self.db.path)

    def _find_switch_nets(self, sw_net='VXBR*'):
        '''Find and group switching nets and their corresponding phases. 

        :param sw_net: Keyword to find the switching nets.
        Wildcards can be used, defaults to 'VXBR*'
        :type sw_net: str, optional
        :return: Switching net names
        :rtype: dict[list]
        '''

        sw_nets = defaultdict(list)
        ph_arg1 = re.compile(r'_PH[ASE]*[0-9]*', re.I)
        ph_arg2 = re.compile(r'_P[0-9]*', re.I)
        for net in self.db.rail_names(sw_net, enabled=True, verbose=False):
            results = ph_arg1.findall(net)
            if not results:
                results = ph_arg2.findall(net)
            net_keys = net
            for result in results:
                net_keys = net_keys.replace(result, '')
            sw_nets[net_keys].append(net)

        return sw_nets
    
    def _get_bounding_box(self, all_nodes: dict):
        '''Find a bounding box coordinates enclosing all the given nodes.

        :param all_nodes: Node names
        :type all_nodes: dict[str]
        :return: Coordinates of the bounding box,
        (x_bottom_left, y_bottom_left, x_top_right, y_top_right)
        :rtype: tuple[float, float, float, float]
        '''

        xmin, ymin = np.inf, np.inf
        xmax, ymax = -np.inf, -np.inf

        for nodes in all_nodes.values():
            xnodes = [self.db.nodes[node].x for node in nodes]
            ynodes = [self.db.nodes[node].y for node in nodes]
            xmin = min(xmin, min(xnodes))
            ymin = min(ymin, min(ynodes))
            xmax = max(xmax, max(xnodes))
            ymax = max(ymax, max(ynodes))

        return (xmin, ymin, xmax, ymax)
    
    def export_sink_setup(self, fname=None):
        '''Generate Excel file with the database sink names and related information.
        This file can be updated by the user in order to modify the sinks setup.
        It can then be used to modify sinks setup in the database by :class:`tasks.PdcTask.import_sink_setup()`

        :param fname: File name of the exported sink setup, defaults to None.
        If not given, a file name is contructed from the database name followed by ``_sinksetup``.
        :type fname: str, optional
        '''

        self.pdc.export_sink_setup(fname)

    def export_vrm_setup(self, fname=None):
        '''Generate Excel file with the database VRM names and related information.
        This file can be updated by the user in order to modify the VRM setup.
        It can then be used to modify VRM setup in the database by :method:`tasks.PdcTask.import_vrm_setup()`

        :param fname: File name of the exported VRM setup, defaults to None.
        If not given, a file name is constructed from the database name followed by ``_vrmsetup``.
        :type fname: str, optional
        '''

        self.pdc.export_vrm_setup(fname)

    def import_sink_setup(self, fname):
        '''Import Excel file and update database with the updated sink setup parameters.
        The template of this file can be generated by :method:`tasks.PdcTask.export_sink_setup()`.

        :param fname: Excel file name that contains the modified sink setup parameters
        :type fname: str
        '''

        self.pdc.import_sink_setup(fname)

    def import_vrm_setup(self, fname):
        '''Import Excel file and update database with the updated VRM setup parameters.
        The template of this file can be generated by :method:`tasks.PdcTask.export_vrm_setup()`.

        :param fname: Excel file name that contains the modified VRM setup parameters
        :type fname: str
        '''

        self.pdc.import_vrm_setup(fname)

    def place_sinks(self, layer, net_name, num_sinks, cap_finder='C*'):
        '''Places sinks based on the provided parameters.

        :param layer: Layer name on which to place sinks
        :type laye: str
        :param net_name: Net names to which to attach sinks
        :type net_name: str or list[str]
        :param num_sinks: Number of sinks to place per each power net
        :type num_sinks: int
        '''

        # Find all power cap nodes
        cap_pwr_nodes = []
        for cap in self.db.find_comps(cap_finder, verbose=False):
            for node in cap.nodes:
                if (self.db.nodes[node].layer == layer and
                        self.db.nodes[node].type == 'pin' and
                        'vss' not in self.db.nodes[node].rail.lower() and
                        'gnd' not in self.db.nodes[node].rail.lower()):
                    cap_pwr_nodes.append(node)
        # Exclude cap nodes from all the other nodes
        nodes_to_use = set(list(self.db.nodes.keys())) - set(cap_pwr_nodes)
        nodes_to_use = [self.db.nodes[node] for node in nodes_to_use]

        self.pdc.place_sinks(layer=layer,
                             net_name=net_name,
                             num_sinks=num_sinks,
                             suffix='SINK',
                             nodes_to_use=nodes_to_use)
    
    def place_vrms(self, layer, net_name):
        '''Places VRMs based on the provided parameters.

        :param layer: Layer name on which to place VRMs
        :type laye: str
        :param net_name: Net names to which to attach VRMs
        :type net_name: str or list[str]
        '''

        self.pdc.place_vrms(layer=layer, net_name=net_name)

    def place_ldo_circuits(self, input_pwr=None, sw_net='VXBR*'):
        """Places circuit definitions that are used in a seperate step to connect LDOs

        :param input_pwr: Input power net names that drive the different FIVRs, defaults to None
        :type input_pwr: str or list[str] or None, optional
        :param sw_net: FIVR swithcing net names, defaults to 'VXBR*'
        :type sw_net: str, optional
        :return: Sink and VRM power and ground nodes to connect to, as well as number of LDO circuits
        :rtype: tuple[dict, dict, int]
        """        

        sw_nets = self._find_switch_nets(sw_net)
        top_layer = self.db.layer_names(verbose=False)[0]
        
        port_db = pm.PortGroup(self.db)
        vrm_nodes, sink_nodes = {}, {}
        for ckt_cnt, (net_name, nets) in enumerate(sw_nets.items(), 1):
            sw_ports = port_db.auto_port(layer=top_layer, net_name=nets,
                                         num_ports=1, verbose=False)
            port_db.db.ports = {**port_db.db.ports, **{port.name: port for port in sw_ports.ports}}
            pos_nodes, neg_nodes = [], []
            for port in sw_ports.ports:
                for pnode in port.pos_nodes:
                    if pnode.type == 'pin':
                        pos_nodes.append(pnode.name)
                for nnode in port.neg_nodes:
                    if nnode.type == 'pin':
                        neg_nodes.append(nnode.name)
            vrm_nodes[net_name] = {'pos': set(pos_nodes),
                                   'neg': set(neg_nodes)}
            
            xmin, ymin, xmax, ymax = self._get_bounding_box(vrm_nodes[net_name])

            # Increase search area for the input power rail
            if (ymax - ymin) > (xmax - xmin):
                xmin = xmin*0.998 if xmin > 0 else xmin*1.002
                xmax = xmax*1.002 if xmax > 0 else xmax*0.998
            else:
                ymin = ymin*0.998 if ymin > 0 else ymin*1.002
                ymax = ymax*1.002 if ymax > 0 else ymax*0.998

            input_ports = port_db.auto_port(layer=top_layer,
                                            net_name=input_pwr,
                                            num_ports=1,
                                            area=(xmin, ymin, xmax, ymax),
                                            verbose=False)

            port_db.db.ports = {**port_db.db.ports, **{port.name: port for port in input_ports.ports}}
            pos_nodes, neg_nodes = [], []
            for port in input_ports.ports:
                for pnode in port.pos_nodes:
                    if pnode.type == 'pin':
                        pos_nodes.append(pnode.name)
                for nnode in port.neg_nodes:
                    if nnode.type == 'pin':
                        neg_nodes.append(nnode.name)
            sink_nodes[net_name] = {'pos': set(pos_nodes),
                                   'neg': set(neg_nodes)}

        port_db.add_ports(save=False)
        port_db.db.prepare_plots(top_layer)
        port_db.db.plot(top_layer)

        for net_name in sink_nodes.keys():
            TasksBase.cmds.append(self.tcl.place_ldo_circuit(list(sink_nodes[net_name]['pos']),
                                                    list(sink_nodes[net_name]['neg']),
                                                    list(vrm_nodes[net_name]['pos']),
                                                    list(vrm_nodes[net_name]['neg'])
                                                )
                                )

        return (sink_nodes, vrm_nodes, ckt_cnt)

    def place_ldos(self, sink_nodes, vrm_nodes, ckt_cnt):
        """Places LDOs based on the provided parameters for the electro-thermal analysis setup.
        This parameters are generated in a seperate step by :method:`tasks.PdcTask.place_ldo_circuits()`.

        :param sink_nodes: Positive and negative nodes of the sink portion of the LDO
        :type sink_nodes: dict
        :param vrm_nodes: Positive and negative nodes of the VRM portion of the LDO
        :type vrm_nodes: dict
        :param ckt_cnt: Number of the identified LDO circuits 
        :type ckt_cnt: int
        """        

        # Find ldo circuits nodes
        circuit_nodes = {}
        for idx in range(ckt_cnt):
            if idx > 0:
                start_block = f'.PartialCkt    NewEmptyCktDef{idx}'
            else:
                start_block = f'.PartialCkt    NewEmptyCktDef'
            line_gen = self.db.extract_block(start_block,
                                            '.EndPartialCkt')
            block = [line for _, line in line_gen]
            circuit_nodes[f'NewEmptyCkt{idx + 1}'] = re.findall(r'\d+', ' '.join(block))

        logger.info('Placing LDOs:')
        for ckt_name, net_name in zip(circuit_nodes.keys(), sink_nodes.keys()):
            logger.info(f'\tDCDC_{ckt_name}')
            TasksBase.cmds.append(self.tcl.place_ldo(list(sink_nodes[net_name]['pos']),
                                                    list(sink_nodes[net_name]['neg']),
                                                    list(vrm_nodes[net_name]['pos']),
                                                    list(vrm_nodes[net_name]['neg']),
                                                    ckt_name, circuit_nodes[ckt_name]))

    def export_ldo_setup(self, fname):
        '''Generate .csv file with the database LDO information.
        This file can be updated by the user in order to modify the LDO setup.
        It can then be used to modify LDO setup in the database by :method:`tasks.PdcTask.import_ldo_setup()`

        :param fname: File name of the exported LDO setup, defaults to None.
        If not given, a file name is constructed from the database name followed by ``_ldosetup``.
        :type fname: str, optional
        '''

        self.pdc.export_ldo_setup(fname)

    def import_ldo_setup(self, fname):
        '''Import .csv file and update database with the updated LDO setup parameters.
        The template of this file can be generated by :method:`tasks.PdcTask.export_ldo_setup()`.

        :param fname: CSV file name that contains the modified LDO setup parameters
        :type fname: str
        '''

        self.pdc.import_ldo_setup(fname)

    def _define_connector(self):

        conns = [(conn, len(self.db.connects[conn.name].nodes))
                  for conn in self.db.find_comps('*ConnectorCkt*', verbose=False)]
        conns = sorted(conns, key=itemgetter(1))
        conn = conns[0][0]

        conn_file = Path(self.db.path) / Path('socket.def')
        conn_file.write_text('\n'.join([f'.SocketModel {conn}',
                                   'PowerType 1',
                                   '.EndSocketModel']))
        
    def create_die_thermal(self, num_dies):

        top_layer = self.db.layer_names(verbose=False)[1]
        comps = [(comp.name, len(comp.nodes))
                    for comp in self.db.find_comps('*U*', verbose=False)
                    if comp.name in self.db.components
                        and self.db.components[comp.name].start_layer == top_layer]
        ref_ids = sorted(comps, key=itemgetter(1), reverse=True)[:num_dies]
        for ref_id in ref_ids:
            super().cmds.append(self.tcl.setup_C4_thermal(ref_id))

    def define_ic_thermal_nodes(self, input_layer, input_net):

        self.pdc.place_vrms(input_layer, input_net, only_ports=True)
    
        self.power_ic_coords = []
        for comp_name in self.pdc.comps_by_rail[input_net]:
            part_name = self.db.connects[comp_name].part
            xc = self.db.components[comp_name].xc
            yc = self.db.components[comp_name].yc
            # Going clockwise
            x_min, y_min = (min(self.db.parts[part_name].x_outline),
                            min(self.db.parts[part_name].y_outline)
            )
            x_max, y_max = (max(self.db.parts[part_name].x_outline),
                            max(self.db.parts[part_name].y_outline)
            )
            node_coords = [(x_min + xc, y_min + yc),
                           (x_min + xc, y_max + yc),
                           (x_max + xc, y_max + yc),
                           (x_max + xc, y_min + yc)
            ]

            # This will be used in the next phase to create thermal circuits
            self.power_ic_coords.append((x_min + xc,
                                            y_min + yc,
                                            x_max + xc,
                                            y_max + yc))
            for (x, y) in node_coords:
                super().cmds.append(self.tcl.add_node(x, y, 'Signal02'))

    def _nodes_in_box(self, x1, y1, x2, y2, nodes: np.array):

        nodes_x, nodes_y, nodes = nodes

        return nodes[(nodes_x >= x1)
                        & (nodes_x <= x2)
                        & (nodes_y >= y1)
                        & (nodes_y <= y2)]

    def setup_ic_thermal(self, node_coords,
                           material=cfg.IC_MATERIAL,
                           comp_thickness=cfg.IC_THICKNESS,
                           temp=cfg.IC_TEMPERATURE):

        nodes_x, nodes_y, nodes_on_layer = [], [], []
        for node_name, node in self.db.nodes.items():
            if node.layer == 'Signal02':
                nodes_on_layer.append(f'{node_name}::{node.rail}')
                nodes_x.append(node.x)
                nodes_y.append(node.y)

        for comp_idx, comp_bound in enumerate(node_coords, 1):
            nodes = self._nodes_in_box(*comp_bound, (np.array(nodes_x),
                                                     np.array(nodes_y),
                                                     np.array(nodes_on_layer))
                                    )
            TasksBase.cmds += [self.tcl.setup_die_thermal(f'VR{comp_idx}',
                                                            f'NewEmptyCkt{comp_idx}',
                                                            *nodes,
                                                        ),
                            self.tcl.define_die_size(f'dvr{comp_idx}',
                                                    f'NewEmptyCkt{comp_idx}',
                                                    comp_thickness),
                            self.tcl.setup_pcb_comp(f'VR{comp_idx}',
                                                    material,
                                                    comp_thickness,
                                                    temp)   
                        ]

    def et_socket_setup_phase1(self, db_fname, num_dies,
                               ihs_length, ihs_width, ihs_thickness,
                               hs_length, hs_width, hs_thickness,
                               tim1_thickness, power_mosfets_plane,
                               power_mosfets_rail, compute_power,
                               io_power=None,
                                material_fname=None,
                                temp=38, top_htc=15, bot_htc=10,
                                heatsink_htc=2000,
                                hs_adhesive_thickness=0.1e-3,
                                ihs_material=cfg.METAL_MATERIAL,
                                tim1_io_material=cfg.TIM1_IO_MATERIAL,
                                tim1_compute_material=cfg.TIM1_COMPUTE_MATERIAL,
                                tim1_material=cfg.TIM1_MATERIAL,
                                die_thickness=cfg.DIE_THICKNESS,
                                die_material=cfg.DIE_MATERIAL,
                                innerfill_material=cfg.INNERFILL_MATERIAL,
                                bump_thickness=cfg.BUMP_THICKNESS,
                                socket_cav_material=cfg.SOCKET_CAVITY_MATERIAL,
                                adhesive_material=cfg.ADHESIVE_MATERIAL,
                                adhesive_thickness=cfg.ADHESIVE_THICKNESS,
                                hs_adhesive_material=cfg.HS_ADHESIVE_MATERIAL):

        self._define_connector()

        if db_fname is not None:
            self.db.name = str(Path(db_fname).name)
            self.db.save()

        if material_fname is None:
            material_fname = os.path.join(self.db.path,
                                          cfg.ET_LGA_MATERIAL_FILE)

        layer_names = list(self.db.stackup.keys())
        TasksBase.cmds += [
                            self.tcl.enable_et_sim(),
                            self.tcl.setup_constraints(),
                            self.tcl.setup_termal_constraints(),
                            self.tcl.save_pdc_results(),
                            self.tcl.setup_thermal_boundery(temp, top_htc, bot_htc),
                            self.tcl.delete_layers(layer_names[0]) \
                                if 'smt' in layer_names[0] else '',
                            self.tcl.delete_layers(layer_names[-1]) \
                                if 'smb' in layer_names[-1] else '',
                            self.tcl.import_material(material_fname)
                        ]
        
        # Create die thermal components
        top_layer = self.db.layer_names(verbose=False)[0]
        comps = [(comp.name, len(comp.nodes))
                    for comp in self.db.find_comps('*U*', verbose=False)
                    if comp.name in self.db.components
                        and self.db.components[comp.name].start_layer == top_layer]
        
        ref_ids = sorted(comps, key=itemgetter(1), reverse=True)[:num_dies]
        for die_idx, (ref_id, _) in enumerate(ref_ids, 1):
            # Find all nodes of a die
            die_nodes = {f'{node_name}::{self.db.nodes[node_name].rail}': self.db.nodes[node_name]
                            for node_name in self.db.connects[ref_id].nodes}
            # Find bounding box around the nodes
            x_nodes, y_nodes = [], []
            for node in die_nodes.values():
                x_nodes.append(node.x)
                y_nodes.append(node.y)
            die_length = 1.03*(max(x_nodes) - min(x_nodes)) # Increase by 3%
            die_height = 1.03*(max(y_nodes) - min(y_nodes)) # Increase by 3%
            if 'IO' in self.db.connects[ref_id].part:
                tim_material = tim1_io_material
                power = io_power
            elif 'COMPUTE' in self.db.connects[ref_id].part:
                tim_material = tim1_compute_material
                power = compute_power
            else:
                tim_material = tim1_material
                power = compute_power
            TasksBase.cmds += [self.tcl.setup_C4_thermal(ref_id),
                               self.tcl.set_thermal_component(ref_id),
                               self.tcl.define_die_size(f'ddie{die_idx}',
                                                        self.db.connects[ref_id].part,
                                                        die_thickness,
                                                        die_length, die_height),
                                self.tcl.define_die(ref_id, tim_material,
                                                    die_length, die_height,
                                                    die_material,
                                                    innerfill_material,
                                                    bump_thickness),
                                self.tcl.define_power_dissipation(ref_id, power)
                            ]
        
        # Create socket thermal component between board top and package bottom layers
        # Find connector on package bottom layer
        comps = [(comp.name, len(comp.nodes))
                    for comp in self.db.find_comps('*A*', verbose=False)]
                    #if self.db.components[comp.name].start_layer == bot_pkg_layer]
        ref_id = max(comps, key=itemgetter(1))[0]
        TasksBase.cmds += [self.tcl.setup_C4_thermal(ref_id),
                           self.tcl.set_thermal_component(ref_id),
                           self.tcl.define_package_thermal(ref_id,
                                                           socket_cav_material,
                                                            ihs_length - 2*ihs_thickness,
                                                            ihs_width - 2*ihs_thickness,
                                                            (tim1_thickness
                                                            + bump_thickness
                                                            + die_thickness
                                                            + 0.001e-3),
                                                            ihs_material, ihs_thickness,
                                                            ihs_length, ihs_width,
                                                            adhesive_material,
                                                            adhesive_thickness),
                            self.tcl.define_heatsink(ref_id, ihs_material,
                                                     hs_length, hs_width,
                                                     hs_thickness,
                                                     hs_adhesive_material,
                                                     hs_adhesive_thickness,
                                                     heatsink_htc)
                        ]
        
        self.define_ic_thermal_nodes(power_mosfets_plane,
                                    power_mosfets_rail
                                )

    def et_socket_setup_phase2(self, node_coords,
                                material=cfg.IC_MATERIAL,
                                comp_thickness=cfg.IC_THICKNESS,
                                temp=cfg.IC_TEMPERATURE):

        # Delete extra dielectric layer
        layer_names = list(self.db.stackup.keys())
        if 'Medium01' in layer_names:
            super().cmds.append(self.tcl.delete_layers('Medium01'))
        # Create and setup power MOSFETs thermal components
        self.setup_ic_thermal(node_coords, material,
                              comp_thickness, temp
                            )

    def setup_stackup_padstack(self, stackup_fname, padstack_fname, db_type,
                               dielec_thickness=None, metal_thickness=None,
                               core_thickness=None, dielec_material=cfg.DIELECT_MATERIAL,
                               metal_material=cfg.METAL_MATERIAL,
                               core_material=cfg.CORE_MATERIAL,
                               socket_cav_material=cfg.SOCKET_CAVITY_MATERIAL,
                               socket_pin_material=cfg.SOCKET_PIN_MATERIAL,
                               socket_layer_thickness=cfg.SOCKET_LAYER_THICKNESS,
                               socket_pin_diameter=cfg.SOCKET_PIN_DIAMETER,
                               brd_dielec_material=cfg.BOARD_DIELEC_MATERIAL,
                               brd_metal_material=cfg.BOARD_METAL_MATERIAL,
                               fillin_dielec_material=cfg.FILLIN_DIELEC_MATERIAL,
                               bump_thickness=cfg.BUMP_THICKNESS,
                               pkg_gnd_plating=cfg.PKG_GND_PLATING,
                               pkg_pwr_plating=cfg.PKG_PWR_PLATING,
                               innerfill_material=cfg.INNERFILL_MATERIAL,
                               outer_thickness=cfg.OUTER_THICKNESS,
                               outer_coating_material=cfg.OUTER_COATING_MATERIAL,
                               c4_material=cfg.C4_MATERIAL,
                               c4_diameter=cfg.C4_DIAMETER, magnetic=True):

        temp_cmds = copy(super().cmds)
        self.auto_setup_stackup(fname=stackup_fname, dielec_thickness=dielec_thickness,
                            metal_thickness=metal_thickness, core_thickness=core_thickness,
                            conduct=None, dielec_material=dielec_material,
                            metal_material=metal_material, core_material=core_material,
                            fillin_dielec_material=fillin_dielec_material)
        self.auto_setup_padstack(fname=padstack_fname, db_type=db_type,
                            pkg_gnd_plating=cfg.PKG_GND_PLATING,
                            pkg_pwr_plating=cfg.PKG_PWR_PLATING, material=metal_material,
                            innerfill_material=innerfill_material if magnetic else None,
                            outer_thickness=outer_thickness if magnetic else None,
                            outer_coating_material=outer_coating_material if magnetic else None)
        
        super().cmds = temp_cmds
        # Update stackup parameters
        board_stackup = False
        stackup = pd.read_csv(stackup_fname)
        for index, row in stackup.iterrows():
            if 'bump' in row['Layer Name'].lower():
                stackup.at[index, 'Material'] = innerfill_material
                stackup.at[index, 'Fill-in Dielectric'] = ''
                stackup.at[index, 'Thickness [m]'] = bump_thickness
            elif 'solderball' in row['Layer Name'].lower():
                stackup.at[index, 'Material'] = socket_cav_material
                stackup.at[index, 'Fill-in Dielectric'] = ''
                stackup.at[index, 'Thickness [m]'] = socket_layer_thickness
            elif 'Signal02' in row['Layer Name'] or board_stackup:
                board_stackup = True
                if 'Medium' in row['Layer Name']: # that means it is a dielectric layer
                    stackup.at[index, 'Material'] = brd_dielec_material
                    stackup.at[index, 'Fill-in Dielectric'] = ''
                else: # otherwise this is a metal layer
                    stackup.at[index, 'Material'] = brd_metal_material
                    stackup.at[index, 'Fill-in Dielectric'] = brd_dielec_material

        stackup.to_csv(stackup_fname, index=False)
        self.update_stackup(stackup_fname)

        # Update padstack parameters
        padstack = pd.read_csv(padstack_fname)
        for index, row in padstack.iterrows():
            if 'bump' in row['Name']:
                padstack.at[index, 'Material'] = c4_material
                padstack.at[index, 'Conductivity [S/m]'] = ''
                padstack.at[index, 'Outer diameter [m]'] = c4_diameter
                padstack.at[index, 'Regular width [m]'] = c4_diameter
                padstack.at[index, 'Regular height [m]'] = c4_diameter
            elif 'Solderball' in row['Name']:
                padstack.at[index, 'Material'] = socket_pin_material
                padstack.at[index, 'Conductivity [S/m]'] = ''
                padstack.at[index, 'Outer diameter [m]'] = socket_pin_diameter
            elif 'BRD' in row['Name']:
                stackup.at[index, 'Material'] = brd_metal_material
                padstack.at[index, 'Conductivity [S/m]'] = ''
                padstack.at[index, 'Plating thickness [m]'] = 0.0254e-3

        padstack.to_csv(padstack_fname, index=False)
        self.update_padstack(padstack_fname)

    def parse_sim_results(self, folder_name, pwr_nets, gnd_nets,
                          report_fname, plot_ground=True):

        folder_name = Path(folder_name)
        err_file = list(folder_name.glob('*.err'))[0]
        results_xml = str(list(folder_name.glob('*.xml'))[0])
        results_txt = list(folder_name.glob('*.txt'))[0]

        # Print any found errors
        logger.error('Electro-thermal simulation errors:\n')
        logger.error(err_file.read_text())
        
        # Parse txt results
        et_results = defaultdict(list)
        result = results_txt.read_text().replace(' DieLayer', '_DieLayer')

        comps_summary = [('[Via Objects]', 'Vias'),
                         ('[Solder Ball Objects]', 'Socket pins'),
                         ('[Solder Bump Objects]', 'C4 bumps')]
        thermal_comps = [('[Molding Compound Objects]', 'VR components Tj'),
                         ('[Die Objects]', 'Die Tj'),
                         ('[Die Attach Objects]', 'Epoxy'),
                          ('[Die Slug Objects]', 'TIM1'),
                          ('[Heat Sink Objects]', 'Heat sink'),
                          ('[Heat Sink Adhesive Objects]', 'Tcase')]
       
        for (title, comp_name) in comps_summary:
            r = result.split(title)[1].split('\n')
            et_results['Component'].append(comp_name)
            et_results['Min Temperature [⁰C]'].append(float(r[2].split()[2]))
            et_results['Max Temperature [⁰C]'].append(float(r[3].split()[2]))

        for (title, comp_name) in thermal_comps:
            et_results['Component'].append('')
            et_results['Min Temperature [⁰C]'].append('')
            et_results['Max Temperature [⁰C]'].append('')
            et_results['Component'].append(comp_name)
            et_results['Min Temperature [⁰C]'].append('')
            et_results['Max Temperature [⁰C]'].append('')
            result_block = result.split(title)[1].split('-\n')[1].split('\n-')[0]
            for r in result_block.split('\n'):
                et_results['Component'].append(r.split()[1])
                et_results['Min Temperature [⁰C]'].append(float(r.split()[3]))
                et_results['Max Temperature [⁰C]'].append(float(r.split()[6]))

        # Parse xml results
        logger.info(f'Generating report(s) for:')
        for pwr_net, gnd_net in zip(pwr_nets, gnd_nets):
            logger.info(f'\t{pwr_net} {gnd_net}')
            report_name = report_fname.replace(Path(report_fname).suffix, f'_{pwr_net}.xlsx')
            all_results = self.pdc.parse_sim_results(xml_fname=results_xml,
                                                    pwr_net=pwr_net,
                                                    gnd_net=gnd_net,
                                                    report_fname=report_name,
                                                    plot_ground=plot_ground,
                                                    save=False
                                                )
            all_results['Socket_thermal'] = pd.DataFrame(et_results)

            # Save results to Excel file with tabs
            with pd.ExcelWriter(report_name) as writer:
                for result_name, result in all_results.items():
                    result.to_excel(writer, sheet_name=result_name)
        
        # Plot socket pins temperature heatmap
        skt_pins = []
        vias_temp = all_results['via_temperature'].to_dict(orient='list')
        if plot_ground:
            nets_to_plot = pwr_nets + gnd_nets
        else:
            nets_to_plot = pwr_nets
        for via_name, via_temp in zip(vias_temp['Name'], vias_temp['Temperature [⁰C]']):
            if ((self.db.vias[via_name.split('::')[0]].lower_layer == 'Signal02'
                or self.db.vias[via_name.split('::')[0]].upper_layer == 'Signal02')
                and via_name.split('::')[1] in nets_to_plot):
                    skt_pins.append((via_name, via_temp))
        skt_nodes = {'NodeName': [via_name for (via_name, via_temp) in skt_pins],
                     'ActualCurrent': [via_temp for (via_name, via_temp) in skt_pins]}

        self.db.plot_pin_current(pd.DataFrame(skt_nodes), 'mm', 'black',
                                    report_fname.replace(Path(report_fname).suffix, f'_skt_temp.html'))
        
        return all_results


class PackageInductorElectroThermalTask(TasksBase):
    '''Class dedicated for package inductor electro-thermal setup and analysis.

    :param TasksBase: Inherited base class
    :type TasksBase: :class:`tasks.TasksBase()`
    '''

    def __init__(self, db_fname=None):
        '''Initializes the generated object.

        :param db_fname: Database file name or database object, defaults to None
        :type db_fname: str or :class:`speed.Database()`, optional
        '''

        super().__init__(db_fname)
        self.pdc = PdcTask(self.db)
        # Copy material file from app to a working directory
        shutil.copy(_thinkpi_path / 'thinkpi' / 'config' / 'materials' / cfg.ET_MATERIAL_FILE,
                    self.db.path)

    def export_sink_setup(self, fname=None):
        '''Generate Excel file with the database sink names and related information.
        This file can be updated by the user in order to modify the sinks setup.
        It can then be used to modify sinks setup in the database by :class:`tasks.PdcTask.import_sink_setup()`

        :param fname: File name of the exported sink setup, defaults to None.
        If not given, a file name is contructed from the database name followed by ``_sinksetup``.
        :type fname: str, optional
        '''

        self.pdc.export_sink_setup(fname)

    def export_vrm_setup(self, fname=None):
        '''Generate Excel file with the database VRM names and related information.
        This file can be updated by the user in order to modify the VRM setup.
        It can then be used to modify VRM setup in the database by :method:`tasks.PdcTask.import_vrm_setup()`

        :param fname: File name of the exported VRM setup, defaults to None.
        If not given, a file name is constructed from the database name followed by ``_vrmsetup``.
        :type fname: str, optional
        '''

        self.pdc.export_vrm_setup(fname)

    def import_sink_setup(self, fname):
        '''Import Excel file and update database with the updated sink setup parameters.
        The template of this file can be generated by :method:`tasks.PdcTask.export_sink_setup()`.

        :param fname: Excel file name that contains the modified sink setup parameters
        :type fname: str
        '''

        self.pdc.import_sink_setup(fname)

    def import_vrm_setup(self, fname):
        '''Import Excel file and update database with the updated VRM setup parameters.
        The template of this file can be generated by :method:`tasks.PdcTask.export_vrm_setup()`.

        :param fname: Excel file name that contains the modified VRM setup parameters
        :type fname: str
        '''

        self.pdc.import_vrm_setup(fname)

    def place_sinks(self, num_sinks, area=None, use_top_layer=False):
        '''Places sinks for power DC analysis, based on the provided parameters.

        :param num_sinks: Number of sinks to place per each power net
        :type num_sinks: int
        :param area: Area to use to place the sinks
        If not given, the entire database area is used, defaults to None
        :type area: tuple[float], optional
        '''

        if num_sinks == 0:
            logger.info('No sinks are placed')
            return
        
        if use_top_layer:
            layer = self.db.layer_names(verbose=False)[0]
        else:
            layer = self.db.layer_names(verbose=False)[1]
        self.pdc.place_sinks(layer=layer,
                             net_name=[net for net in self.pwr_nets if 'vxbr' not in net.lower()],
                             num_sinks=num_sinks, area=area, suffix='SINK')
        self.db.ports = {}
    
    def place_vrms(self):
        '''Places VRMs for power DC analysis, based on the provided parameters.
        '''

        if '$' in self.db.layer_names(verbose=False)[0]:
            layer = self.db.layer_names(verbose=False)[0]
        else:
            layer = self.db.layer_names(verbose=False)[1]
        
        # Find and place ports on the phase nets
        vrm_ports = pm.PortGroup(self.db)
        # vrm_nets = sorted(vrm_ports.db.rail_names(vrm_phases, enabled=True, verbose=False))
        vrm_nets = [net for net in self.pwr_nets if 'vxbr' in net.lower()]
        for vrm_net in vrm_nets:
            vrm_ports = vrm_ports.auto_port(layer, vrm_net, 1, None)
            vrm_ports.ports[0].name = f"{vrm_ports.ports[0].name.replace('VXBR', 'VRM_et')}"
            vrm_ports.add_ports(save=False)

        # Place VRMs where the ports are
        line_num = self.db.lines.index('* PdcElem description lines\n') + 1
        for vrm in reversed(vrm_ports.db.ports.values()):
            if 'VRM_et' in vrm.name:
                block = [f'.VRM NominalVoltage = 0 SenseVoltage = 0 '
                            f'OutputCurrent = 0 Name = "{vrm.name.replace("_et", "")}"']
                block.append('.Pin Name = "Positive Pin"')
                for pos_node in vrm.pos_nodes:
                    block.append(f'.Node Name = {pos_node.name}::{pos_node.rail}')
                block.append('.EndPin')
                block.append('.Pin Name = "Negative Pin"')
                for neg_node in vrm.neg_nodes:
                    block.append(f'.Node Name = {neg_node.name}::{neg_node.rail}')
                block.append('.EndPin')
                block.append('.Pin Name = "Positive Sense Pin"')
                block.append('.EndPin')
                block.append('.Pin Name = "Negative Sense Pin"')
                block.append('.EndPin')
                block.append('.EndVRM\n')
                block.reverse()
                for line_in_block in block:
                    self.db.lines.insert(line_num, f'{line_in_block}\n')

        vrm_ports.db.prepare_plots(layer)
        vrm_ports.db.plot(layer)

        # Remove ports from the database
        vrm_ports.db.ports = {}
        vrm_ports.update_ports(save=False)

    def et_setup_phase1(self, db_fname=None, temp=105, material_fname=None, default_conduct=None):
        '''Setup first part of Power DC electro-thermal simulation.

        :param db_fname: New layout file name.
        If None, the original layout is overwritten, defaults to None
        :type db_fname: None or str, optional
        :param temp: Simulation temperature, defaults to 110
        :type temp: int, optional
        :param material_fname: Material file name. if not provided,
        the default thermal material file name is used, defaults to None
        :type material_fname: None or str, optional
        :param default_conduct: Via default conductivity.
        Will be used when material file is not provided, defaults to None
        :type default_conduct: None or float, optional
        '''

        if db_fname is not None:
            self.db.name = str(Path(db_fname).name)
            self.db.save()

        # Create and save *_dev.control file
        (Path(self.db.path) / Path(f'{Path(self.db.name).stem}_dev.control')).write_text(
                            'SolverID 3\nMETAL_MESH2D_MODE -1\n'
        )

        if material_fname is None:
            material_fname = os.path.join(self.db.path,
                                          cfg.ET_MATERIAL_FILE)

        top_layer = self.db.layer_names(verbose=False)[0]
        comps = [comp for comp in self.db.find_comps('*U*', verbose=False)
                    if self.db.components[comp.name].start_layer == top_layer]

        # Find component ref. id based on its nodes rail and the first power rail
        ref_id = None
        for comp in comps:
            node_rails = set([self.db.nodes[node_name].rail for node_name in comp.nodes])
            if self.pwr_nets[0] in node_rails:
                ref_id = comp.name
                break

        layer_names = list(self.db.stackup.keys())
        TasksBase.cmds += [self.tcl.enable_et_sim(),
                            self.tcl.setup_constraints(),
                            self.tcl.save_pdc_results(),
                            self.tcl.setup_thermal_boundery(temp),
                            self.tcl.setup_C4_thermal(ref_id) if ref_id is not None else '',
                            self.tcl.delete_layers(layer_names[0]) \
                                if 'smt' in layer_names[0] else '',
                            self.tcl.delete_layers(layer_names[-1]) \
                                if 'smb' in layer_names[-1] else '',
                            self.tcl.import_material(material_fname),
                            self.tcl.default_via_conduct(default_conduct)
                                if default_conduct is not None else ''
                    ]

    def et_setup_phase2(self, ind_rail, ind_layer='Signal$1bco',
                        die_name='ddie',
                        die_thickness=cfg.DIE_THICKNESS,
                        die_material=cfg.DIE_MATERIAL,
                        PCB_bot_temp=105,
                        mesh_edge=None):
        '''Setup second part of Power DC electro-thermal simulation.

        :param ind_rail: Net name of of the package inductor
        :type ind_rail: str
        :param ind_layer: The layer on which inductor traces are present, defaults to 'Signal$1bco'
        :type ind_layer: str, optional
        :param die_name: The die circuit name, defaults to 'ddie'
        :type die_name: str, optional
        :param die_thickness: Thickness in meters of the die layer, defaults to cfg.DIE_THICKNESS
        :type die_thickness: float, optional
        :param die_material: Material name of the die layer, defaults to cfg.DIE_MATERIAL
        :type die_material: str, optional
        :param PCB_bot_temp: Motherboard bottom temperature, defaults to 105
        :type PCB_bot_temp: float, optional
        :param mesh_edge: Maximum mesh edge around the inductor traces.
        If None, will be calculated, defaults to None
        :type mesh_edge: None or float, optional
        '''

        def within_area(xmin, ymin, xmax, ymax, px, py):

            if (xmin < px < xmax) and (ymin < py < ymax):
                return True
            else:
                return False

        # Calculate maximum excat mesh length
        if mesh_edge is None:
            edge_length = min((self.db.db_x_top_right - self.db.db_x_bot_left),
                              (self.db.db_y_top_right - self.db.db_y_bot_left)) / 20
            logger.info(f'Allowed mesh edge length range: '
                        f'{edge_length*0.1*1e3:.3f} mm to {edge_length*2*1e3:.3f} mm')
            mesh_edge = round(edge_length*0.1*1e3, 2)/1e3
        logger.info(f'Exact mesh length used: {mesh_edge*1e3} mm')

        # Find all nodes on the die layer
        die_layer = self.db.layer_names(verbose=False)[0]
        die_nodes = {f'{node_name}::{node.rail}': node for node_name, node in self.db.nodes.items()
                        if node.layer == die_layer}
        # Find bounding box around the nodes
        x_nodes, y_nodes = [], []
        for node in die_nodes.values():
            x_nodes.append(node.x)
            y_nodes.append(node.y)
        die_length = 1.03*(max(x_nodes) - min(x_nodes)) # Increase by 3%
        die_height = 1.03*(max(y_nodes) - min(y_nodes)) # Increase by 3%

        # Find fine mesh area
        # First find shapes on the provided layer and net name
        xmin, ymin = np.inf, np.inf
        xmax, ymax = -np.inf, -np.inf
        for shape in self.db.shapes.values():
            if (shape.net_name is not None
                    #and (shape.net_name == ind_rail or 'VXBR' in shape.net_name)
                    and 'vxbr' in shape.net_name.lower()
                    #and shape.net_name in self.pwr_nets
                    and self.db.net_names[shape.net_name][0] == 1
                    and shape.layer == ind_layer):
                xmin = min(xmin, min(shape.xcoords))
                ymin = min(ymin, min(shape.ycoords))
                xmax = max(xmax, max(shape.xcoords))
                ymax = max(ymax, max(shape.ycoords))
        
        # Limit the search area of the vout net
        xmin_bottom = xmin*0.97 if xmin > 0 else xmin*1.03
        ymin_bottom = ymin*0.97 if ymin > 0 else ymin*1.03
        xmax_top = xmax*1.03 if xmax > 0 else xmax*0.97
        ymax_top = ymax*1.03 if ymax > 0 else ymax*0.97

        for shape in self.db.shapes.values():
            xmin_shape = min(shape.xcoords)
            ymin_shape = min(shape.ycoords)
            xmax_shape = max(shape.xcoords)
            ymax_shape = max(shape.ycoords)
            if (shape.net_name is not None
                    #and (shape.net_name == ind_rail or 'VXBR' in shape.net_name)
                    and within_area(
                        xmin_bottom, ymin_bottom,
                        xmax_top, ymax_top,
                        xmin_shape, ymin_shape
                    )
                    and within_area(
                        xmin_bottom, ymin_bottom,
                        xmax_top, ymax_top,
                        xmax_shape, ymax_shape
                    )
                    and shape.net_name in self.pwr_nets
                    and self.db.net_names[shape.net_name][0] == 1
                    and shape.layer == ind_layer):
                xmin = min(xmin, xmin_shape)
                ymin = min(ymin, ymin_shape)
                xmax = max(xmax, xmax_shape)
                ymax = max(ymax, ymax_shape)

        xcenter = (xmin + xmax)/2
        ycenter = (ymin + ymax)/2
        area_length = (xmax - xmin)*1.15 # Increase by 15%
        area_width = (ymax - ymin)*1.15 # Increase by 15%

        TasksBase.cmds += [self.tcl.enable_et_sim(),
                            self.tcl.setup_die_thermal(die_name,
                                                       'NewEmptyCkt1',
                                                        *list(die_nodes.keys())),
                            self.tcl.define_die_size(die_name,
                                                     'NewEmptyCktDef',
                                                    die_thickness,
                                                    die_length, die_height),
                            self.tcl.setup_pcb_comp(die_name,
                                                    die_material,
                                                    die_thickness,
                                                    PCB_bot_temp),
                            self.tcl.setup_exact_mesh(xcenter, ycenter,
                                                        area_length, area_width,
                                                        'BottomAir',
                                                        'TopAir',
                                                        mesh_edge)
                        ]

    def setup_stackup_padstack(self, stackup_fname, padstack_fname, 
                               pkg_gnd_plating=cfg.PKG_GND_PLATING,
                               pkg_pwr_plating=cfg.PKG_PWR_PLATING,
                               dielec_thickness=None, metal_thickness=None,
                               core_thickness=None,
                               dielec_material=cfg.DIELECT_MATERIAL,
                               metal_material=cfg.METAL_MATERIAL,
                               core_material=cfg.CORE_MATERIAL,
                               fillin_dielec_material=cfg.FILLIN_DIELEC_MATERIAL,
                               bump_thickness=cfg.BUMP_THICKNESS,
                               innerfill_material=cfg.INNERFILL_MATERIAL,
                               outer_thickness=cfg.OUTER_THICKNESS,
                               outer_coating_material=cfg.OUTER_COATING_MATERIAL,
                               c4_material=cfg.C4_MATERIAL,
                               c4_diameter=cfg.C4_DIAMETER, magnetic=True):
        '''Automatically configures the stackup and padstack for the package
        inductor electro-thermal analysis.
        The final stackup and padstack .csv files are also saved for reference.
        The values used are based on user input as well as thinkpi_conf.py file.

        :param stackup_fname: File name of the generated .csv stackup file
        :type stackup_fname: str
        :param padstack_fname: File name of the generated .csv padstack file
        :type padstack_fname: str
        :param dielec_thickness: The thickness in meters that is applied to all dielectric layers.
        If not provided, the existing thickness in the databse is used, defaults to None
        :type dielec_thickness: float, optional
        :param metal_thickness: The thickness in meters that is applied to all metal layers.
        If not provided, the existing thickness in the databse is used, defaults to None
        :type metal_thickness: float, optional
        :param core_thickness: The thickness in meters that is applied to the core layer.
        If not provided, the existing thickness in the databse is used, defaults to None
        :type core_thickness: float, optional
        :param dielec_material: The name of the dielectric layer material
        that is listed in the material file, defaults to cfg.DIELECT_MATERIAL
        :type dielec_material: str, optional
        :param metal_material: The name of the metal layer material
        that is listed in the material file, defaults to cfg.METAL_MATERIAL
        :type metal_material: str, optional
        :param core_material: The name of the core layer material
        that is listed in the material file, defaults to cfg.CORE_MATERIAL
        :type core_material: str, optional
        :param fillin_dielec_material: The dielectric material name of the
        fill-in between metal layers, defaults to cfg.FILLIN_DIELEC_MATERIAL
        :type fillin_dielec_material: str, optional
        :param bump_thickness: The thickness or the height in meters of
        the C4 bumps, defaults to cfg.BUMP_THICKNESS
        :type bump_thickness: float, optional
        :param plating: The plating thickness of the core PTHs
        in meters, defaults to cfg.PLATING
        :type plating: float, optional
        :param innerfill_material: The name of the fill-in material of
        magnetic PTHs, defaults to cfg.INNERFILL_MATERIAL
        :type innerfill_material: str, optional
        :param outer_thickness: The outer coating thickness in meters of
        magnetic PTHs, defaults to cfg.OUTER_THICKNESS
        :type outer_thickness: float, optional
        :param outer_coating_material: The outer coating material name of
        magnetic PTHs, defaults to cfg.OUTER_COATING_MATERIAL
        :type outer_coating_material: str, optional
        :param c4_material: The name of the C4 bumps material, defaults to cfg.C4_MATERIAL
        :type c4_material: str, optional
        :param c4_diameter: The diameter in meters of the C4 bumps, defaults to cfg.C4_DIAMETER
        :type c4_diameter: float, optional
        :param magnetic: Indicating if the package inductor is magnetic or
        an air core inductor (ACI), defaults to True
        :type magnetic: bool, optional
        '''

        temp_cmds = copy(TasksBase.cmds)
        self.auto_setup_stackup(fname=stackup_fname, dielec_thickness=dielec_thickness,
                            metal_thickness=metal_thickness, core_thickness=core_thickness,
                            conduct=None, dielec_material=dielec_material,
                            metal_material=metal_material, core_material=core_material,
                            fillin_dielec_material=fillin_dielec_material)
        self.auto_setup_padstack(
                            fname=padstack_fname, db_type='package',
                            brd_plating=None, pkg_gnd_plating=pkg_gnd_plating,
                            pkg_pwr_plating=pkg_pwr_plating, conduct=None,
                            material=metal_material,
                            innerfill_material=innerfill_material if magnetic else None,
                            outer_thickness=outer_thickness if magnetic else None,
                            outer_coating_material=outer_coating_material if magnetic else None,
                            unit='m'
        )
        
        TasksBase.cmds = temp_cmds
        # Update stackup parameters
        stackup = pd.read_csv(stackup_fname)
        for index, row in stackup.iterrows():
            if 'bump' in row['Layer Name'].lower():
                stackup.at[index, 'Material'] = innerfill_material
                stackup.at[index, 'Fill-in Dielectric'] = ''
                stackup.at[index, 'Thickness [m]'] = bump_thickness
        stackup.to_csv(stackup_fname, index=False)
        self.update_stackup(stackup_fname)

        # Update padstack parameters
        padstack = pd.read_csv(padstack_fname)
        for index, row in padstack.iterrows():
            if 'bump' in row['Name']:
                padstack.at[index, 'Material'] = c4_material
                padstack.at[index, 'Outer diameter [m]'] = c4_diameter
                padstack.at[index, 'Regular width [m]'] = c4_diameter
                padstack.at[index, 'Regular height [m]'] = c4_diameter
        padstack.to_csv(padstack_fname, index=False)
        self.update_padstack(padstack_fname)

    def report_sim_results(self, xml_fname,
                            pwr_plating, gnd_plating,
                            product_life=7, report_fname=None,
                            plot_ground=True):
        
        logger.info('\nCreating report for the following nets:')
        logger.info(f'\t{self.pwr_nets[0]}')
        results = self.parse_sim_results(
                            xml_fname, self.pwr_nets[0], self.gnd_nets[0],
                            pwr_plating, gnd_plating,
                            product_life, report_fname,
                            plot_ground, False
                        )
        results[self.pwr_nets[0]] = results['via_plane_current']
        del results['via_plane_current']

        for pwr_net in self.pwr_nets[1:]:
            logger.info(f'\t{pwr_net}')
            result = self.parse_sim_results(
                            xml_fname, pwr_net, self.gnd_nets[0],
                            pwr_plating, gnd_plating,
                            product_life, report_fname,
                            plot_ground, False
                        )
            results[pwr_net] = result['via_plane_current']

        with pd.ExcelWriter(report_fname) as writer:
            for result_name, result in results.items():
                if not result.empty:
                    result.to_excel(writer, sheet_name=result_name)

    def parse_sim_results(self, xml_fname, pwr_net, gnd_net,
                            pwr_plating, gnd_plating,
                            product_life=7, report_fname=None,
                            plot_ground=True, save=True):
        '''Parses electro-thermal results and produces report with
        computed specifications based on the thermal results.

        :param xml_fname: File name of the .xml file with the simulation results
        :type xml_fname: str
        :param pwr_net: Name of the power net for which the report is created
        :type pwr_net: str
        :param gnd_net: Name of the ground net for which the report is created
        :type gnd_net: str
        :param pwr_net: Plating thickness in meters for the power PTHs
        :type pwr_net: float
        :param gnd_net: Plating thickness in meters for the ground PTHs
        :type gnd_net: float
        :param product_life: Designed product life time in years, defaults to 7
        :type product_life: float, optional
        :param report_fname: File name of the .xlsx report.
        If not given, a file name consisting the database name followed by
        `_pdcreport` will be used, defaults to None
        :type report_fname: None or str, optional
        :param plot_ground: Indicates if to include ground net in the plot, defaults to True
        :type plot_ground: bool, optional
        :param save: Indicates if to save the report as xlsx file, defaults to True
        :type save: bool, optional
        :return: Dictionary with pandas dataframes with the relevant results
        :rtype: dict[DataFrame]
        '''

        if report_fname is None:
            if self.db is None:
                report_fname = 'pdc_report.xlsx'
            else:
                report_fname = f'{os.path.join(self.db.path, self.db.name).split(".")[0]}_pdcreport.xlsx'
    
        results = self.pdc.parse_sim_results(xml_fname=xml_fname,
                                                    pwr_net=pwr_net,
                                                    gnd_net=gnd_net,
                                                    report_fname=report_fname,
                                                    plot_ground=plot_ground,
                                                    save=False
                                            )
        
        vias_by_layer = {layer_name: [] for layer_name in results['via_plane_current']['Layer Name']}
        try:
            via_temp = results['via_temperature'].to_dict(orient='list')
            plane_temp = results['plane_temperature'].to_dict(orient='list')

            plane_temp = {layer_name:temp for layer_name, temp in zip(plane_temp['Name'],
                                                                        plane_temp['Temperature [⁰C]'])}
            for via_name, temp in zip(via_temp['Name'], via_temp['Temperature [⁰C]']):
                via_name = via_name.split('::')[0]
                upper_layer = self.db.vias[via_name].upper_layer
                lower_layer = self.db.vias[via_name].lower_layer
                via_padstack = self.db.vias[via_name].padstack
                try:
                    via_diam = self.db.padstacks[via_padstack][upper_layer].tsv_radius*2
                except KeyError:
                    via_diam = self.db.padstacks[via_padstack][None].tsv_radius*2
                if upper_layer in vias_by_layer:
                    vias_by_layer[upper_layer].append((via_name, via_diam, float(temp)))
                try:
                    via_diam = self.db.padstacks[via_padstack][lower_layer].tsv_radius*2
                except KeyError:
                    via_diam = self.db.padstacks[via_padstack][None].tsv_radius*2
                if lower_layer in vias_by_layer:
                    vias_by_layer[lower_layer].append((via_name, via_diam, float(temp)))

            f_temp_scale = interpolate.interp1d(list(cfg.ETPS_TEMP_SCALE.keys()),
                                                list(cfg.ETPS_TEMP_SCALE.values())
                                            )
            f_years_scale = interpolate.interp1d(list(cfg.ETPS_YEARS_SCALE.keys()),
                                                list(cfg.ETPS_YEARS_SCALE.values())
                                            )
            via_temp_by_layer = {}
            via_spec_pwr = {}
            via_spec_gnd = {}
            plane_temp_by_layer = {}
            plane_spec = {}
            for layer_name, via_data in vias_by_layer.items():
                via_name, via_diam, via_temp = max(via_data, key=itemgetter(2))
                via_temp_by_layer[layer_name] = via_temp
                plane_temp_by_layer[layer_name] = plane_temp[layer_name]

                scale_factor = f_temp_scale(via_temp) * f_years_scale(product_life)
                if pwr_plating != 18e-6 and ('bco' in layer_name or 'fco' in layer_name):
                    via_radius = via_diam/2*1e6
                    effective_area = np.pi*(via_radius**2 - (via_radius - pwr_plating*1e6)**2)
                    via_spec_pwr[layer_name] = scale_factor * cfg.ETPS_PLANE_DENSITY*1e-3 * effective_area
                else:
                     via_spec_pwr[layer_name] = scale_factor * cfg.ETPS_IAVG[int(via_diam*1e6)]
                    
                if gnd_plating != 18e-6 and ('bco' in layer_name or 'fco' in layer_name):
                    via_radius = via_diam/2*1e6
                    effective_area = np.pi*(via_radius**2 - (via_radius - gnd_plating*1e6)**2)
                    #via_spec_pwr[layer_name] = scale_factor * cfg.ETPS_PLANE_DENSITY*1e-3 * effective_area
                    via_spec_gnd[layer_name] = scale_factor * cfg.ETPS_PLANE_DENSITY*1e-3 * effective_area
                else:
                    via_spec_gnd[layer_name] = scale_factor * cfg.ETPS_IAVG[int(via_diam*1e6)]

                scale_factor = f_temp_scale(plane_temp[layer_name]) * f_years_scale(product_life)
                plane_spec[layer_name] = min(cfg.ETPS_MAX_PLANE_DENSITY, scale_factor * cfg.ETPS_PLANE_DENSITY)

            results['via_plane_current'].insert(3, ('Max. Via Current [mA]', 'Temp [⁰C]'),
                                                list(via_temp_by_layer.values()))
            results['via_plane_current'].insert(4, ('Max. Via Current [mA]', 'Power spec'),
                                                list(via_spec_pwr.values()))
            results['via_plane_current'].insert(5, ('Max. Via Current [mA]', 'Ground spec'),
                                                list(via_spec_gnd.values()))
            results['via_plane_current'].insert(8, ('Max. Plane Current Density [A/mm^2]', 'Temp [⁰C]'),
                                                list(plane_temp_by_layer.values()))
            results['via_plane_current'].insert(9, ('Max. Plane Current Density [A/mm^2]', 'spec'),
                                                list(plane_spec.values()))
    
        except KeyError:
            logger.warning('Thermal results are not found. Check simulation setup and PowerDC saving options.')
        
        # Save results to Excel file with tabs
        if save:
            with pd.ExcelWriter(report_fname) as writer:
                for result_name, result in results.items():
                    result.to_excel(writer, sheet_name=result_name)
        return results


class IdemEvalResults:
    '''Class to evaluate and compare by plotting the best five macromodel matches.
    Comparison can be done real-time, during the optimization process.
    '''
    
    def __init__(self, sparam_fname, max_data_freq=None):
        '''Initializes the class :class:`IdemEvalResults()`

        :param sparam_fname: The touchstone file name
        :type sparam_fname: str
        :param max_data_freq: The maximum frequency in Hz for which the comparison is performed.
        If not provided the maximum frequency from the touchstone file is assumed, defaults to None.
        :type max_data_freq: float, optional
        '''
        
        self.hspice_path = Path(sparam_fname).parent.joinpath('hspice')
        self.node_names, self.ref = self._load_ref()
        if max_data_freq is None:
            self.max_bw = self.ref[0].data.x[-1]
        else:
            self.max_bw = max_data_freq
        self.ref_mat = self.build_matrix(self.ref.waves.values())
        self.macros = []
    
    def _load_ref(self):
        '''Loads the original extracted S-parameters, serving as the baseline. 

        :return: Port names
        :rtype: Tuple[list, :class:`Waveforms()`]
        '''
        
        nodes = ld.Waveforms()
        nodes.load_waves(os.path.join(str(self.hspice_path),
                                      'main_zf_s.ac0'),
                         x_unit='Hz', y_unit='Ω')
        return nodes.wave_names(verbose=False), nodes
    
    def build_matrix(self, waves):
        '''Constructs numpy matrix based on the provided waveforms.

        :param waves: Loaded waveforms from which to construct the matrix
        :type waves: :class:`Waveforms()`
        :return: Two dimensional matrix
        :rtype: numpy.array
        '''
        
        mat = [wave.clip(tend=self.max_bw).data.y for wave in waves]
        return np.array(mat)
    
    def refresh(self, node_name=None):
        '''Refreshes graphical comparison.
        This can be done during the optimization process.

        :param node_name: The port name for which a graphical comparison is performed.
        If not provided, the first port name is used, defaults to None.
        :type node_name: str, optional
        '''
        
        if node_name is None:
            node_name = self.node_names[0]
        
        for fpath in self.hspice_path.glob('*.ac0'):
            if 'macro' in fpath.name:
                nodes = ld.Waveforms()
                nodes.load_waves(str(fpath), x_unit='Hz', y_unit='Ω')
                macro_mat = self.build_matrix(nodes.waves.values())
                mse = mean_squared_error(self.ref_mat, macro_mat)
                for nname, node in nodes.waves.items():
                    macro_num = node.file_name.split('.')[0].split('_')[-1]
                    node.wave_name = f'{nname} | {macro_num} | mse={mse:.3e}'
                self.macros.append(nodes)
        waves_to_plot = [self.ref.waves[node_name]]
        for macro in self.macros:
            waves_to_plot.append(macro.waves[node_name])
        self.macros = []
        
        self.ref.plot_overlay(waves_to_plot, x_scale='M',
                              y_scale='', xaxis_type='log',
                              yaxis_type='linear')


class IdemWaveCompare:
    
    def __init__(self, ref_path, macromodel_path, pts_per_decade=None):
        
        self.ref_waves = ld.Waveforms()
        self.ref_waves.load_waves(os.path.abspath(ref_path))
        self.max_bw_data = list(self.ref_waves.waves.values())[0].data.x[-1]
        self.macromodel_path = os.path.abspath(macromodel_path)
        self.best_matches = []
        self.pts_per_decade = pts_per_decade
        
    def build_matrix(self, waves, bw):
        
        if self.pts_per_decade is None:
            mat = [wave.clip(tend=bw).data.y for wave in waves]
        else:
            total_points = self.pts_per_decade*int(np.log10(bw))
            mat = []
            for wave in waves:
                w = wave.clip(tend=bw)
                f = interp1d(w.data.x, w.data.y)
                mat.append(f(np.logspace(
                        np.log10(w.data.x[0]) if w.data.x[0] > 0 else 0,
                        np.log10(bw), total_points
                    ))
                )

        return np.array(mat)
    
    def mse(self, macro_path, params, max_bw):
        
        macromodel = ld.Waveforms()
        macromodel.load_waves(macro_path)
        
        ref_mat = self.build_matrix(self.ref_waves.waves.values(), max_bw)
        macro_mat = self.build_matrix(macromodel.waves.values(), max_bw)
        score = mean_squared_error(ref_mat, macro_mat)
        self.last_mse = score
        
        self.best_matches.append((macro_path, params,
                                  macromodel, score))
        sorted_matches = sorted(self.best_matches, key=itemgetter(3))
        self.best_matches = sorted_matches[:5]
        fname_best_matches = [match[0].split('_')[-1].split('.')[0] for match in sorted_matches[:5]]

        # Delete all related files with a low mse scores while leaving the best first five
        idem_path = Path(macro_path).parent.parent / 'idem'
        sparam_files = sorted(idem_path.glob('*.cir.s*p'),
                                  key=os.path.getctime)
        
        for sparam_file in sparam_files[:-1]:
            if str(sparam_file.name).split('.')[0] not in fname_best_matches:
                sparam_file.unlink()
        
        for match in sorted_matches[5:]:
            for ext in ['.ac0', '.ic0', '.lis', '.pa0',
                        '.st0', '.sp', '.bat']:
                Path(match[0].replace('.ac0', ext)).unlink()
            fname = match[0].split('_')[-1].split('.')[0]
            Path(idem_path / f'{fname}.cir').unlink()
            Path(idem_path / f'{fname}.mod.h5').unlink()
            Path(idem_path / f'{fname}.cir.export.bat').unlink()
            Path(idem_path / f'{fname}.mod.h5.fitting.bat').unlink()
            Path(idem_path / f'{fname}.mod.h5.passivity.bat').unlink()
            Path(idem_path / f'{fname}.mod.h5.passivity_check.bat').unlink()


class IdemOptimizer(TasksBase):
    
    def __init__(self, term_fname, sparam_fname, cap_models=None,
                max_data_freq=None, output_format='HSPICE-LAPLACE',
                acc=1e-5, pts_per_decade=None):
        
        super().__init__()
        self.term = pd.read_csv(term_fname)
        self.cnt = 0
        self.sparam_fname = sparam_fname
        self.cap_models = cap_models
        
        # Create sub directories hspice and idem in the given path
        self.hspice_path = Path(self.sparam_fname).parent.joinpath('hspice')
        shutil.rmtree(self.hspice_path, ignore_errors=True)
        self.hspice_path.mkdir(exist_ok=True)
        self.sparam_zf_spice_file_path = str(self.hspice_path / 'main_zf_s.sp')
        self.idem_path = Path(self.sparam_fname).parent.joinpath('idem')
        shutil.rmtree(self.idem_path, ignore_errors=True)
        self.idem_path.mkdir(exist_ok=True)
        self.logfile_path = Path(self.sparam_fname).parent / 'idem_opt.log'
        
        # Copy over .xml idem setup files
        for xml_file in Path(_thinkpi_path).joinpath(
                            'thinkpi', 'config', 'idem').rglob('*.xml'):
            shutil.copyfile(xml_file, Path(self.idem_path) / Path(xml_file.name))
            
        self.report_lines = []
        self.output_format = output_format
    
        self.comments_ref = self._get_comments_ref()
        self.sparam_ref = rf.Network(os.path.abspath(self.sparam_fname))
        if max_data_freq is None:
            self.max_data_freq = self.sparam_ref.f[-1]
        else:
            self.max_data_freq = max_data_freq
            
        self.create_ref()
        self.my_hspice_deck = hspice_deck.HspiceDeck(deck_path=str(self.hspice_path))
        self.my_hspice = hspice.hspice()
        self.my_hspice.set_hspice_path(self.exec_paths['hspice'][0])
        self.my_idem = idem.idem()
        self.my_idem.set_idemmp_path(self.exec_paths['idem'][0])
        self.acc = acc
        self.ref_waves = ld.Waveforms()
        self.ref_waves.load_waves(self.sparam_zf_spice_file_path.replace('.sp', '.ac0'))
        
        self.wc = IdemWaveCompare(self.sparam_zf_spice_file_path.replace('.sp', '.ac0'),
                              str(self.hspice_path), pts_per_decade)
    
    def _get_comments_ref(self):
        
        comments = []
        with open(os.path.abspath(self.sparam_fname)) as f:
            lines = f.readlines()
        comments = [line for line in lines if '!' in line]
        comments = ''.join(comments)
        comments = comments.replace('!', '')
        
        return comments
    
    def create_ref(self):
        
        self.build_and_run_zf_using_term_file(
                        self.exec_paths['hspice'][0],
                        self.sparam_zf_spice_file_path,
                        self.sparam_fname
                    )
    
    def optimize(self, min_bw, max_bw, bw_steps,
                 refzs, order_min, order_step, order_max,
                 max_iter_per_freq=10):
        
        bw_shuffled = np.linspace(min_bw, max_bw, bw_steps)
        shuffle(bw_shuffled)
        dc_nonpassive_cnt = 0
        #for bw in np.arange(bw_min, bw_max, bw_steps):
        for refz in refzs:
            for bw in bw_shuffled:
                self.idem_func(bw, order_min, order_step, order_max,
                               refz, False, 0.1)
                num_iter = 1
                while True:
                    success, dc_passive = self.idem_func(bw, order_min,
                                                         order_step, order_max,
                                                         refz, True, 0.1)
                    if not dc_passive and dc_nonpassive_cnt < 9:
                        dc_nonpassive_cnt += 1
                        dc_passive = True
                    else:
                        dc_nonpassive_cnt = 0
                    if not success:
                        break
                    if num_iter > max_iter_per_freq:
                        break
                    num_iter += 1
                if not dc_passive:
                    break
                        
        with open('idem_opt.log', 'at') as log_file:
            log_file.write(f'{time.perf_counter()} seconds\n')
                        
    def update_sparams(self, last_sparam_fname, ref_z, scale=0.1):
        
        last_net = rf.Network(last_sparam_fname)
        freq = rf.Frequency.from_f(last_net.f, unit='Hz')
        #new_net = self.sparam_ref.z - scale*(last_net.z - self.sparam_ref.z)
        #new_net = (self.sparam_ref.z_re - scale*(last_net.z_re - self.sparam_ref.z_re)
        #           + 1j*self.sparam_ref.z_im)
        new_net = (1j*(self.sparam_ref.z_im - scale*(last_net.z_im - self.sparam_ref.z_im))
                   + self.sparam_ref.z_re)

        new_net[0, :, :] = last_net.z[0, :, :]
        new_net = rf.Network(frequency=freq, z=new_net, comments=self.comments_ref)
        new_net.write_touchstone(os.path.join(self.idem_path,
                                              'new_sparam'),
                                 skrf_comment=False,
                                 r_ref=ref_z
                            )
    
    def idem_func(self, bw, order_min, order_step, order_max,
                  ref_z, new_sparam=False, scale=0.1):
        
        if new_sparam:
            idem_sparam_file = os.path.join(str(self.idem_path),
                                            f'new_sparam.'
                                            f"{self.sparam_fname.split('.')[1]}")
            self.update_sparams(os.path.join(str(self.idem_path),
                                             f'macro{self.cnt-1}.cir.'
                                             f"{self.sparam_fname.split('.')[1]}"),
                                ref_z, scale
                            )
        else:
            idem_sparam_file = self.sparam_fname
        
        macromodel_it = os.path.join(self.idem_path,
                                         f'macro{self.cnt}.cir')
        deck_it = os.path.join(str(self.hspice_path),
                                f'main_zf_macro{self.cnt}.sp')
        self.cnt += 1
        
        success = self.my_idem.create_idem_model(
                    idem_sparam_file, macromodel_it,
                    order_min, order_step, order_max, bw, 1,
                    self.acc, ["Touchstone", self.output_format],
                    str(self.idem_path / 'advance_settings_fitting.fopt.xml'),
                    str(self.idem_path / 'advance_settings_passivity.popt.xml')
                )
        if not success:
            self.cnt -= 1
            return False, True
        try:
            self.my_hspice_deck.write_test_zf_deck(
                                deck_it, macromodel_it,
                                self.term, self.cap_models,
                                #self.max_bw
                                self.max_data_freq
                            )
            self.my_hspice_deck.include_lines = []
            
            # Run Hspice
            self.my_hspice.hspice_run(deck_it)
        except FileNotFoundError: # Catches when passivity at DC fails
            self.my_hspice_deck.include_lines = []
            self.cnt -= 1
            return False, False
            pass

        params = {'order_min': order_min,
                  'order_step': order_step,
                  'order_max': order_max,
                  'bw': bw,
                  'acc': self.acc,
                  'impedance': ref_z}
        self.wc.mse(deck_it.replace('.sp', '.ac0'), params, self.max_data_freq) #self.max_bw)
        param_line = (f'macro{self.cnt-1} -> '
                            f'order_min = {order_min}, '
                            f'order_step = {order_step}, '
                            f'order_max = {order_max}, '
                            f'ref_z = {ref_z}, '
                            f'bw = {bw*1e-6} MHz, '
                            f"mse = {self.wc.last_mse}, "
                            f'scale = {scale}')
        self.report_lines.append((param_line, self.wc.last_mse))
        self.report_lines = sorted(self.report_lines, key=itemgetter(1))
        self.logfile_path.write_text('\n'.join([line[0] for line in self.report_lines]) + '\n')
        logger.info(param_line)
        
        return True, True
    
    def build_and_run_zf_using_term_file(self,
                                         hspice_path,
                                         sparam_zf_spice_file_path,
                                         sparam_file_path):
        #Create deck_builder
        my_hspice_deck = hspice_deck.HspiceDeck(deck_path=str(self.hspice_path))
        #Deck Run
        my_hspice = hspice.hspice()
        my_hspice.set_hspice_path(hspice_path)
        
        my_hspice_deck.write_test_zf_deck(
                zf_spice_file_path=sparam_zf_spice_file_path,
                model_fpath=sparam_file_path,
                termination_df=self.term,
                caps_folder=self.cap_models, bw=self.max_data_freq
            )
        
        my_hspice.hspice_run(sparam_zf_spice_file_path)


@dataclass
class Symbol:
    '''Dataclass used by :class:`Simplis()`.
    '''

    fname: str
    ref_id: str
    width: int
    height: int
    area: int
    cir_name: str
    ports: List[str]
    cir_def: str
    x: int = 0
    y: int = 0
    
    
class Simplis(TasksBase):
    '''Implementation of the Simplis automation flow.
    '''

    def __init__(self, cir_path):
        '''Initialization of the :class:`Simplis()` class

        :param cir_path: The path to the folder where macromodels and subcircuits are located
        :type cir_path: 'str'
        '''

        super().__init__()
        self.cir_path = Path(cir_path)
        shutil.copy(_thinkpi_path / 'thinkpi' / 'config' / 'simplis_scripts' / cfg.SIMPLIS_PARSER,
                    self.cir_path.parent)
        shutil.copy(_thinkpi_path / 'thinkpi' / 'config' / 'simplis_scripts' / cfg.SIMPLIS_SYMBOL,
                    self.cir_path.parent)
        self.conns = []
        self.symbols = []
        self.cmds = []
        self.simplis = SimplisCommands()
        self.max_width = -np.inf
        self.max_height = -np.inf
        self.min_y = np.inf
        self.max_x = -np.inf
        self.cap_muls = {}

    def replace_params(self, lines):
        '''Replaces parameters with their corresponding values.

        :param lines: Lines of the subcircuit definition
        :type lines: list[str]
        :return: Subcircuit lines with the parameters replaced, subcircuit name, and ports name
        :rtype: tuple[str, str, str]
        '''

        cir_name = None
        ports = None
        # Find all parameters
        params = {}
        for idx, line in enumerate(lines.copy()):
            if not line or line[0] == '*':
                continue
            if '=' in line:
                split_equal = line.strip('+').strip().split('=')
                params[split_equal[0].split()[-1].lower()] = split_equal[1].split()[0]
                if '.subckt' not in line.lower():
                    lines[idx] = f'* {line}'
                else:
                    lines[idx] = ' '.join(line.split('=')[0].split()[:-1])
                    cir_name = lines[idx].split()[1]
                    ports = lines[idx].split()[2:]
            elif '.subckt' in line.lower():
                cir_name = lines[idx].split()[1]
                ports = lines[idx].split()[2:]
            elif '.param' in line.lower():
                lines[idx] = f'* {line}'
            else:
                for param_name in params.keys():
                    if param_name in line.lower():
                        line = line.lower().replace(param_name, params[param_name])
                lines[idx] = line

        return lines, cir_name, ports

    def prep_cir(self, cir_types=['.cir', '.sp', '.inc']):

        ref_id = 1
        for path in self.cir_path.glob('*.*'):
            if path.suffix not in cir_types:
                continue
            cir_def = path.read_text()
            ports = []
            for line in cir_def.split('\n'):
                if not line:
                    continue
                if '::' in line:
                    ports.append(line.split()[1].split('::')[0])
                if 'ref' in line and 'ref' not in ports:
                    ports.append('ref')
                if '.subckt' in line.lower():
                    subckt_name = line.split()[1]
                    break

            for idx, port_name in enumerate(ports, 1):
                cir_def = cir_def.replace(f' a_{idx} ', f' {port_name} ')
            path.write_text(cir_def)

            if not ports:
                new_lines, subckt_name, ports = self.replace_params(cir_def.split('\n'))
                cir_def = '\n'.join(new_lines)
                path.write_text(cir_def)
             
            if ports:
                width = int(0.977*len(max(ports)) + 4.5253)
                height = int(0.8*len(ports) + 5.2)
                self.symbols.append(Symbol(path, f'U{ref_id}',
                                            width, height,
                                            width*height,
                                            subckt_name,
                                            ports, cir_def)
                                        )
                ref_id += 1
            
        self.symbols = sorted(self.symbols, key=attrgetter('area'))
        try:
            xdim = int(len(self.symbols)/2)
            ydim = int(np.ceil(len(self.symbols)/xdim))
        except ZeroDivisionError:
            xdim, ydim = 1, 1

        # Find maximum width and height of any symbol boxes
        for symbol in self.symbols:
            self.max_width = max(self.max_width, symbol.width)
            self.max_height = max(self.max_height, symbol.height)

        self.symbols = np.array(self.symbols).reshape(xdim, ydim)

    def export_circuit_map(self, fname):

        if isinstance(self.symbols, list):
            self.prep_cir()
        symbol_ports = [pd.DataFrame({f'{symbol.cir_name}_{symbol.ref_id}': symbol.ports})
                        for symbol in self.symbols.flatten()
                    ]
        # Add other symbols such as current sinks, probes, etc.
        symbol_ports = [pd.DataFrame({'idc."1m"': ['N+', 'N-']}),
                        pd.DataFrame({'ipwl_file."my_file_name.txt"': ['N+', 'N-']}),
                        pd.DataFrame({'ipwl."0 0 1u 1"': ['N+', 'N-']}),
                        pd.DataFrame({'vdc."5"': ['N+', 'N-']}),
                        pd.DataFrame({'vac."1 0"': ['N+', 'N-']})] \
                        + symbol_ports

        symbol_ports = pd.concat(symbol_ports, ignore_index=True)
        symbol_ports.to_excel(fname, index=False)

    def _modify_cap_count(self, symbol_name, mul):

        for symbol in self.symbols.flatten():
            if symbol.fname.stem in symbol_name:
                symbol.cir_def = symbol.cir_def.replace('/1', f'/{mul}')
                symbol.cir_def = symbol.cir_def.replace('*1', f'*{mul}')
                symbol.fname.write_text(symbol.cir_def)

    def import_circuit_map(self, fname):

        conn_map = pd.read_excel(fname, sheet_name=None)
        sources = ['idc', 'ipwlfile', 'ipwl', 'vdc', 'vac']
        src_ref_id = 1
        for symbol_pair in conn_map.values():
            sym1, sym2 = symbol_pair.columns

            val = None
            cap_mul = None
            if sym1.split('."')[-1].lower()[0] == 'x':
                cap_mul = (sym1.split('."')[0], sym1.split('."')[-1][1:-1])
            elif sym2.split()[-1].lower()[0] == 'x':
                cap_mul = (sym2.split('."')[0], sym2.split('."')[-1][1:-1])
            if cap_mul is not None:
                self._modify_cap_count(*cap_mul)
                self.cap_muls[cap_mul[0].split('_')[-1]] = cap_mul[1]

            ref_id1 = sym1.split('.')[0].split('_')[-1]
            if ref_id1 in sources:
                val = (ref_id1, sym1.split('."')[-1][:-1])
                ref_id1 = f'{ref_id1}_{src_ref_id}'
                src_ref_id += 1
            ref_id2 = sym2.split('.')[0].split('_')[-1]
            if ref_id2 in sources:
                val = (ref_id2, sym2.split('."')[-1][:-1])
                ref_id2 = f'{ref_id2}_{src_ref_id}'
                src_ref_id += 1
                
            for _, row in symbol_pair.iterrows():
                node1, node2 = row[sym1], row[sym2]
                try:
                    if 'probe' in row[sym1]:
                        probe_val = (row[sym1].split('.')[1], row[sym1].split('."')[-1][:-1])
                        if val is None:
                            val = probe_val
                        else:
                            val = val + probe_val
                        node1 = row[sym1].split('.')[0]
                except TypeError: # Catches if row[sym1] is None
                    pass
                try:
                    if 'probe' in row[sym2]:
                        probe_val = (row[sym2].split('.')[1], row[sym2].split('."')[-1][:-1])
                        if val is None:
                            val = probe_val
                        else:
                            val = val + probe_val
                        node2 = row[sym2].split('.')[0]
                except TypeError: # Catches if row[sym2] is None
                    pass

                if not pd.isna(node1) and ('gnd' in node1.lower()
                                            or 'ref' in node1.lower()):
                    self.conns.append((f"{node1.split('.')[0]}_{ref_id1}"
                                       if 'gnd' in node1.lower() else f"{node1.split('.')[0]}",
                                       'gnd',
                                       val if 'gnd' in node1.lower() else None)
                                    )
                    continue
                if not pd.isna(node2) and ('gnd' in node2.lower()
                                            or 'ref' in node2.lower()):
                    self.conns.append((f"{node2.split('.')[0]}_{ref_id2}"
                                       if 'gnd' in node2.lower() else f"{node2.split('.')[0]}",
                                       'gnd',
                                       val if 'gnd' in node2.lower() else None)
                                    )
                    continue
                if not pd.isna(node1) and not pd.isna(node2):
                    self.conns.append((f"{node1}_{ref_id1}",
                                        f"{node2}_{ref_id2}",
                                        val))
        self.conns = list(set(self.conns))

        # Find sources and sinks and connect them directly
        src_conns = defaultdict(list)
        new_conns = []
        for (pin1, pin2, val) in self.conns:
            if val is not None and val[0] in sources:
                if '+' in pin1:
                    src_conns[pin1.replace('+', '')].append((0, pin2, val))
                elif '-' in pin1:
                    src_conns[pin1.replace('-', '')].append((1, pin2, val))
                if '+' in pin2:
                    src_conns[pin2.replace('+', '')].append((0, pin1, val))
                elif '-' in pin2:
                    src_conns[pin2.replace('-', '')].append((1, pin1, val))
            else:
                new_conns.append((pin1, pin2, val))

        self.conns = new_conns
        for src_conn in src_conns.values():
            src_pins = sorted(src_conn, key=itemgetter(0))
            self.conns.append((src_pins[0][1], src_pins[1][1],
                               src_pins[1][2]
                               if len(src_pins[1][2]) > len(src_pins[0][2])
                               else src_pins[0][2])
                        )

    def place_cir(self, x_shift=0, y_shift=0):

        self.prep_cir()

        for y_idx in range(self.symbols.shape[0]):
            for x_idx in range(self.symbols.shape[1]):
                if x_idx == 0:
                    self.symbols[y_idx, x_idx].x = x_shift
                else:
                    self.symbols[y_idx, x_idx].x = (self.symbols[y_idx, x_idx-1].x
                                                    + self.max_width*75 + 2550
                                                )
                if y_idx == 0:
                    self.symbols[y_idx, x_idx].y = y_shift
                else:
                    self.symbols[y_idx, x_idx].y = (self.symbols[y_idx-1, x_idx].y
                                                    + self.max_height*158 + 923
                                                )
                self.cmds.append(self.simplis.spice_to_simplis(f"'{self.symbols[y_idx, x_idx].fname}'",
                                                               self.symbols[y_idx, x_idx].x,
                                                               self.symbols[y_idx, x_idx].y))
                
                self.min_y = min(self.min_y, self.symbols[y_idx, x_idx].y)
                self.max_x = max(self.max_x, self.symbols[y_idx, x_idx].x)

        self.max_x = 2.5*self.max_x
                
    def connect_cir(self, port_map=None):

        # Place wires and terminations
        for y_idx in range(self.symbols.shape[0]):
            for x_idx in range(self.symbols.shape[1]):
                self.cmds.append('')
                self.cmds.append(self.simplis.get_pin_locs(self.symbols[y_idx, x_idx].ref_id))
                for idx, port_name in enumerate(self.symbols[y_idx, x_idx].ports):
                    if port_name == 'ref':
                        self.cmds += ([self.simplis.draw_vert_wire(idx*2, 300),
                                        self.simplis.draw_vert_term(idx*2, 300, 1, 'ref')]
                                )
                        continue
                    if idx < int(np.ceil(len(self.symbols[y_idx, x_idx].ports)/2)):
                        length = -300
                        orient = 2
                    else:
                        length = 300
                        orient = 6
                    self.cmds += ([self.simplis.draw_horiz_wire(idx*2, length),
                                    self.simplis.draw_horiz_term(idx*2, length, orient,
                                                            f'{port_name}_{self.symbols[y_idx, x_idx].ref_id}')]
                                )
        
        # Connect circuits based on the provided port map
        sources = {'idc': self.simplis.idc, 'ipwlfile': self.simplis.ipwl_file,
                   'ipwl': self.simplis.ipwl, 'vdc': self.simplis.vdc, 'vac':self.simplis.vac}
        probes = {'iprobe': self.simplis.iprobe, 'vprobe': self.simplis.vprobe}
        self.cmds.append('')
        if port_map is not None:
            self.import_circuit_map(port_map)

            try:
                xdim = int(len(self.conns)/2)
                ydim = int(np.ceil(len(self.conns)/xdim))
            except ZeroDivisionError:
                xdim, ydim = 1, 1
            
            it = iter(self.conns)
            for y in np.arange(self.min_y, self.min_y + 1700*ydim, 1700):
                for x in np.arange(self.max_x, self.max_x + 2000*xdim, 2000):
                    try:
                        (n1_term , n2_term, val) = next(it)
                        if val is not None and val[0] in sources:
                            self.cmds += [self.simplis.draw_term(x, y, 3, n1_term),
                                          self.simplis.draw_wire(x, y, x, y + 100),
                                          sources[val[0]](val[1], orient=0) % (x, y + 100),
                                          self.simplis.draw_wire(x, y + 600, x, y + 700),
                                          self.simplis.draw_gnd(x, y + 700, 0) \
                                            if n2_term == 'gnd' else self.simplis.draw_term(x, y + 700, 1, n2_term)
                                        ]
                            if len(val) > 2: # That means we need to add a probe as well
                                self.cmds.append(probes[val[2]](val[3], orient=0) % (x, y + 100))
                        else:
                            self.cmds += [self.simplis.draw_term(x, y, 3, n1_term),
                                        self.simplis.draw_wire(x, y, x, y + 700),
                                        self.simplis.draw_gnd(x, y + 700, 0) \
                                            if n2_term == 'gnd' else self.simplis.draw_term(x, y + 700, 1, n2_term)
                                    ]
                            if val is not None:
                                self.cmds.append(probes[val[0]](val[1], orient=0) % (x, y + 350))
                    except StopIteration:
                        pass

        # Add capacitor multiplier as a symbol property
        for ref_id, mul in self.cap_muls.items():
            self.cmds.append(self.simplis.ncaps_prop(ref_id, mul))

    def create_sxscr(self, sxscr_fname, sxsch_fname):

        self.cmds = [self.simplis.new_schem(sxscr_fname), ''] + self.cmds
        self.cmds += ['', self.simplis.save_as(sxsch_fname),
                      self.simplis.close_sch()
                    ]
        Path(sxscr_fname).write_text('\n'.join(self.cmds))

    def run_sxscr(self, sxsrc_fname):
        '''Runs Simplis script.

        :param sxsrc_fname: Name of the script file to run
        :type sxsrc_fname: str
        '''

        logger.info(f'Running {sxsrc_fname}, Please wait... ')
        cmd = f'"{self.exec_paths["simplis"][0]}" /s "Execute {{\'{sxsrc_fname}\'}}" /i'
        logger.info(cmd)
        run_result = subprocess.run(cmd.split(), stdout=subprocess.PIPE, text=True)
        logger.info('Done\n')
                
               