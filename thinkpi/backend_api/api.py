#import sys
#sys.path.append(r"D:\jrosenfe\ThinkPI\applications.design-automation.power.think-pi")
from collections import defaultdict
from pathlib import Path

from bokeh.embed import file_html
from bokeh.models import Model
from bokeh.resources import CDN

import pandas as pd

from thinkpi.operations import speed as spd
from thinkpi.flows import tasks
from thinkpi.operations import pman as pm
from thinkpi.config import thinkpi_conf as cfg
from thinkpi import logger

loaded_layouts = {}

class DbApi:
    '''This class is responsible to provide all the required functionality APIs
    to the front-end of ThinkPI application.
    '''

    def __init__(self, db_path=None, queue=None):
        '''Initialization method of the class.

        :param db_path: Path to the .spd layout file
        :type db_path: str
        '''

        self.db = spd.Database(db_path, queue)

    def cdn(self):
        '''Current CDN source for Bokeh plots.

        :return: URL of Bokeh CDN
        :rtype: str
        '''

        return CDN.render()

    def load_data(self):
        '''Load .spd layout file.

        :return: Layer names and the fisrt layer html view of the layout
        :rtype: dict[list, str]
        '''

        self.db.load_flags['plots'] = False
        self.db.load_data()
        loaded_layouts[self.db.name] = self.db
        
        # Sort out net names by type
        nets_by_type = defaultdict(list)
        for net_name, (enabled, net_type) in self.db.net_names.items():
            if enabled:
                nets_by_type[net_type].append(net_name)
        # By default return first layer view, all layer names, and all net names
        return {'layer_names': self.db.layer_names(verbose=False),
                'layer_html': self.layer_view(self.db.layer_names(verbose=False)[0]),
                'net_names': nets_by_type
        }

    def layer_view(self, layer_name, db=None):
        '''Generate html layer view of a specified layer.

        :param layer_name: Layer name to create the view
        :type layer_name: str
        :return: Html layer view
        :rtype: str
        '''
        
        db = self.db if db is None else db
        layer = db.plot_layer(layer_name)
        layer.border_fill_color = 'black'
        layer.xaxis.axis_line_color = 'gray'
        layer.yaxis.axis_line_color = 'gray'
        layer.axis.major_tick_line_color = 'gray'
        layer.axis.minor_tick_line_color = 'gray'
        html_layer = file_html(layer, CDN, layer_name)
        
        for model in layer.select({'type': Model}):
            prev_doc = model.document
            model._document = None
            if prev_doc:
                prev_doc.remove_root(model)
        return html_layer
    
    def get_material(self, fname):
        '''Load material file.

        :param fname: File name
        :type fname: str
        :return: Multi-level dictionary with materials and their corresponding properties
        :rtype: dict
        '''

        return self.db.load_material(fname)
    
    def save_material(self, fname, materials):
        '''Save material file.

        :param fname: File name
        :type fname: str
        :param materials: Multi-level dictionary with materials and their corresponding properties
        :type materials: dict
        '''

        self.db.save_material(fname, materials)

    def get_stackup(self):
        '''Generate the current layout stackup.

        :return: Stackup layers and their corresponding properties
        :rtype: dict
        '''

        return self.db.generate_stackup(save=False).to_dict(orient='list')

    def auto_setup_stackup(self, fname, unit, dielec_thickness=None,
                            metal_thickness=None, core_thickness=None,
                            conduct=None, dielec_material=None,
                            metal_material=None, core_material=None,
                            fillin_dielec_material=None, er=None, loss_tangent=None):
        '''Automatically prefills stackup information based on user input and saves it as .csv file.

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
        :return: Prefilled modified stackup
        :rtype: dict
        '''
        
        db = tasks.PsiTask(self.db)
        db.auto_setup_stackup(fname, dielec_thickness,
                                metal_thickness, core_thickness,
                                conduct, dielec_material,
                                metal_material, core_material,
                                fillin_dielec_material, er,
                                loss_tangent, unit)
        
        return pd.read_csv(fname).fillna('').to_dict(orient='list')

    def apply_stackup(self, stackup_fname, material_fname=None):
        """Apply the provided stackup csv file to the layout file and save it

        :param stackup_fname: Stackup csv file name
        :type stackup_fname: str
        :param material_fname: Material txt file name, defaults to None
        :type material_fname: str or None, optional
        """
        
        db = tasks.PsiTask(self.db)
        db.apply_stackup(stackup_fname, material_fname)
        
        tcl_fname = db.create_tcl(('PowerSI', 'extraction'))
        db.run_tcl(tcl_fname, db.exec_paths['sigrity'][0])

    def apply_padstack(self, padstack_fname, material_fname=None):
        """Apply the provided stackup csv file to the layout file and save it

        :param padstack_fname: Stackup csv file name
        :type padstack_fname: str
        :param material_fname: Material txt file name, defaults to None
        :type material_fname: str or None, optional
        """ 

        db = tasks.PsiTask(self.db)
        db.apply_padstack(padstack_fname, material_fname)
        
        tcl_fname = db.create_tcl(('PowerSI', 'extraction'))
        db.run_tcl(tcl_fname, db.exec_paths['sigrity'][0])

    def load_stackup(self, fname):
        '''load stackup csv file.

        :param fname: File name
        :type fname: str
        :return: Stackup information
        :rtype: dict
        '''

        return pd.read_csv(fname).fillna('').to_dict(orient='list')
    
    def save_stackup(self, fname, stackup):
        '''Save stackup as .csv file.

        :param fname: File name
        :type fname: str
        :param stackup: New stackup layers
        :type stackup: dict
        '''

        pd.DataFrame(stackup).to_csv(fname, index=False)
        logger.info(f'Saved file {fname}')

    def get_padstack(self):
        '''Generate the current layout padstack.

        :return: Padstacks and their corresponding properties
        :rtype: dict
        '''

        return self.db.generate_padstack(save=False).to_dict(orient='list')
        
    def auto_setup_padstack(self, fname, db_type, brd_plating=None,
                            pkg_gnd_plating=None, pkg_pwr_plating=None,
                            conduct=None, material=None,
                            innerfill_material=None, outer_thickness=None,
                            outer_coating_material=None, unit='m'):
        '''Automatically prefills padstack information based on user input
        and saves it as .csv file.

        :param fname: File name of the output padstack .csv file. If None,
        the layout name followed by a '_padstack' will be used
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
        
        if fname is None:
            fname = f'{Path(self.db.path) / Path(self.db.name).stem}_padstack.csv' 
        db = tasks.PsiTask(self.db)
        db.auto_setup_padstack(fname, db_type, brd_plating,
                            pkg_gnd_plating, pkg_pwr_plating,
                            conduct, material,
                            innerfill_material, outer_thickness,
                            outer_coating_material, unit)
        
        return pd.read_csv(fname).fillna('').to_dict(orient='list')
    
    def save_padstack(self, fname, padstack):
        '''Save padstack as .csv file.

        :param fname: File name
        :type fname: str
        :param stackup: New padstack
        :type stackup: dict
        '''

        pd.DataFrame(padstack).to_csv(fname)

    def preprocess(self, pwr_nets, gnd_nets,
                   stackup_fname=None, padstack_fname=None,
                   material_fname=None, default_conduct=None,
                   cut_margin=0, processed_fname=None, delete_unused_nets=False):
        '''Preprocess a database before performing 2D extraction or PowerDC simulation.

        :param pwr_nets: Power net names on which to perform the preprocessing
        :type pwr_nets: list[str]
        :param gnd_nets: Ground net names on which to perform the preprocessing
        :type gnd_nets: list[str]
        :param stackup_fname: File name with the stackup information
        :type stackup_fname: str
        :param padstack_fname: File name with the padstack information
        :type padstack_fname: str
        :param material_fname: File name with the material information, defaults to None
        :type material_fname: None or str, optional
        :param default_conduct: Conductivity in S/m that is assumed for copper.
        This should be provided when a material file is not available, defaults to None
        :type default_conduct: None or float, optional
        :param cut_margin: Margin to leave around nets of interest when cut is performed
        , given in meters. If 0 is provided no cut is performed, defaults to 0
        :type cut_margin: float, optional
        :param processed_fname: File name of processed database.
        If not provided the original database will be overwritten, defaults to None
        :type processed_fname: None or str, optional
        '''
        
        db = tasks.PsiTask(self.db)
        db.select_nets(pwr_nets, gnd_nets)
        db.preprocess(stackup_fname, padstack_fname,
                      material_fname, default_conduct,
                      cut_margin, processed_fname, delete_unused_nets)
        tcl_fname = db.create_tcl(('PowerSI', 'extraction'))
        db.run_tcl(tcl_fname, db.exec_paths['sigrity'][0])

    def report(self, nets, report_fname, cap_finder='C*'):
        """Create a general report per each net name.
        The report includes general information, as well as
        information about layers, ports, caps, and pins. 

        :param nets: Net names for which the report is created
        :type nets: str or a list of str
        :param report_fname: Report file name
        :type report_fname: str
        :param cap_finder: Wildcard lookup of capacitors, defaults to 'C*'
        :type cap_finder: str or list of str, optional
        :return: Reports with the relevant information
        :rtype: dict[str]
        """        

        reports = {}
        for net in nets:
            self.db.report(net, report_fname, cap_finder)
            reports[net] = Path(report_fname).read_text()

        return reports


class DbHandler:

    def __init__(self):

        self.port_report = []

    def db_loader(self, src_db, dst_db=None, flags=None):
        """Facilitates loading layouts.

        :param src_db: Name or object of the source layout
        :type src_db: str or :class:`speed.Database()`
        :param dst_db: Name or object of the destination layout, defaults to None
        :type dst_db: str or :class:`speed.Database()`, optional
        :param flags: A dictionary specifing the required sections of the
        layout to load. If None is provided plots are not prepared
        in advance, defaults to None
        :type flags: dict, optional
        :return: Source and destination layout objects
        :rtype: Tuple[:class:`speed.Database()`, :class:`speed.Database()`]
        """        

        if isinstance(src_db, str):
            if Path(src_db).name in loaded_layouts:
                src = loaded_layouts[Path(src_db).name]
            else:
                src = spd.Database(src_db, self.queue)
                if flags is None:
                    src.load_flags['plots'] = False
                else:
                    for flag_name, val in flags.items():
                        src.load_flags[flag_name] = val
                src.load_data()
                loaded_layouts[src.name] = src
        else:
            src = src_db

        if dst_db is None:
            dst = None
        elif isinstance(dst_db, str) and Path(dst_db).name not in loaded_layouts:
            dst = spd.Database(dst_db, self.queue)
            if flags is None:
                dst.load_flags['plots'] = False
            else:
                for flag_name, val in flags.items():
                    dst.load_flags[flag_name] = val
            dst.load_data()
            loaded_layouts[dst.name] = dst
        else:
            dst = dst_db

        return src, dst
    
    def report_results(self, dst_ports, add_ports=True):
        """Generates layer plots with ports and report.

        :param dst_ports: The copied ports object
        :type dst_ports: :class:`pman.PortGroup()`
        :param add_ports: If True, adds the generated ports to the
        layout and saves it, defaults to True
        :type add_ports: bool, optional
        :return: Layer views and report of the copied ports
        :rtype: dict
        """        

        if add_ports:
            dst_ports.add_ports(save=True)
        
        layers = []
        # Find layers of the ports
        for port in dst_ports.db.ports.values():
            if port.layers:
                layers.append(port.layers[0])
        layers = set(layers)
        if layers:
            dst_ports.db.prepare_plots(*layers)

        report = {layer: self.db_ops.layer_view(layer, dst_ports.db) for layer in layers}
        report['report'] = self.port_report

        return report
    
    def record_status(self, dst_ports):

        self.port_report += dst_ports.status(verbose=False)

    def clear_status(self):

        self.port_report = []
    

class PortHandler(DbHandler):
    """This class provides APIs for everything related to port handeling.
    """    

    def __init__(self, queue):
        """Initializes this class.

        :param queue: Queue object to store the logging information
        :type queue: queue.Queue
        """        

        super().__init__()
        self.queue = queue
        self.db_ops = DbApi()
    
    def get_port_info(self, db, csv_fname=None):
        """Provides layout port information.

        :param db: The name or object of layout to extract port information from
        :type db: str or :class:`speed.Database()`
        :param csv_fname: Name of the csv file with ports setup definition, defaults to None
        :type csv_fname: str, optional
        :return: Existing port information
        :rtype: dict
        """

        if csv_fname is not None:
            return pd.read_csv(csv_fname).fillna('').to_dict(orient='list')
        
        db_ports = pm.PortGroup(self.db_loader(db)[0])
        if db_ports.db.ports:
            ports_fname = f'{Path(db_ports.db.name).stem}_portinfo.csv'
            logger.info(f'Ports setup file {Path(db_ports.db.path) / Path(ports_fname)} is created')
            return db_ports.export_port_info(Path(db_ports.db.path) / Path(ports_fname)).to_dict(orient='list')
        else:
            logger.warning('Ports do not exist in this layout')
            return None
    
    def modify_port_info(self, db, ports_fname, port_info):
        """Modifies port information and saves it in the provided layout.

        :param db: The name or object of layout to use
        :type db: str or :class:`speed.Database()`
        :param ports_fname: The name of the csv setup file
        :type ports_fname: str
        :param port_info: The new port information recieved from the frontend
        :type port_info: dict
        """        

        db_ports = pm.PortGroup(self.db_loader(db)[0])
        df_port_info = pd.DataFrame(port_info)
        df_port_info.to_csv(ports_fname, index=False)
        logger.info(f'Sinks setup file {ports_fname} is created')
        db_ports.import_port_info(ports_fname)

    def setup_motherboard_ports(self, db, pwr_net_names,
                                cap_finder,
                                cap_layer_top, reduce_num_top,
                                cap_layer_bot, reduce_num_bot,
                                vrm_layer, ref_z, socket_mode,
                                from_db_side=None,
                                skt_num_ports=None,
                                pkg_fname=None):
        '''Create ports for a typical motherboard extraction.

        :param db: The name or object of layout to use to place ports
        :type db: str or :class:`speed.Database()`
        :param pwr_net_names: Power net name(s) to place ports
        :type pwr_net_names: str or list[str]
        :param cap_finder: Keyword to find capacitor components.
        Wildcards can be also used.
        :type cap_finder: str
        :param cap_layer_top: Top layer name to place capacitor ports
        :type cap_layer_top: str
        :param reduce_num_top: Number of ports to reduce to on the top layer
        :type reduce_num_top: int
        :param cap_layer_bot: Bottom layer name to place capacitor ports
        :type cap_layer_bot: Number of ports to reduce to on the bottom layer
        :param reduce_num_bot: Number of ports to reduce to on the bottom layer
        :type reduce_num_bot: int
        :param vrm_layer: Layer name to place VRMs on
        :type vrm_layer: str
        :param ref_z: Port reference impedance
        :type ref_z: float
        :param socket_mode: Indicates how to generate socket ports.
        Can only accept 'create' or 'transfer'.
        If 'create' mode is selected, new specified number of socket ports are created.
        If 'transfer' mode is selected, existing ports from a layout socket are copied.
        :type socket_mode: str
        :param from_db_side: Relavant only if socket_mode is 'transfer'.
        Indicating from which side to copy socket ports.
        Can only accept 'bottom' (for a package) or 'top' (for a board)
        :type from_db_side: str
        :param skt_num_ports: Relavant only if socket_mode is 'create'.
        Indiciating the number of required socket ports, defaults to None
        :type skt_num_ports: int, optional
        :param pkg_fname: Relavant only if socket_mode is 'transfer'.
        If so, user must provide the package layout name from which the ports are copied,
        defaults to None
        :type pkg_fname: str, optional
        :return: Layer views and report of the placed ports
        :rtype: dict
        '''
        
        self.clear_status()
        db_ports = pm.PortGroup(self.db_loader(db)[0])
        
        for pwr_net_name in pwr_net_names:
            db_ports = db_ports.auto_port_comp(layer=cap_layer_top,
                                                net_name=pwr_net_name,
                                                comp_find=cap_finder,
                                                ref_z=ref_z)
            db_ports.add_ports(save=False)
            self.record_status(db_ports)
            db_ports = db_ports.reduce_ports(layer=cap_layer_top,
                                            num_ports=reduce_num_top,
                                            select_ports=[port.name for port in db_ports.ports])
            db_ports.add_ports(save=False)
            self.record_status(db_ports)
            db_ports = db_ports.auto_port_comp(layer=cap_layer_bot,
                                                net_name=pwr_net_name,
                                                comp_find=cap_finder,
                                                ref_z=ref_z)
            db_ports.add_ports(save=False)
            self.record_status(db_ports)
            db_ports = db_ports.reduce_ports(layer=cap_layer_bot,
                                            num_ports=reduce_num_bot,
                                            select_ports=[port.name for port in db_ports.ports])
            db_ports.add_ports(save=False)
            self.record_status(db_ports)
            db_ports_vrm = db_ports.auto_vrm_ports(layer=vrm_layer,
                                                net_name=pwr_net_name,
                                                ref_z=ref_z)
            if db_ports_vrm is not None:
                db_ports_vrm.add_ports(save=False)
                db_ports = db_ports_vrm
                self.record_status(db_ports)
            else:
                logger.warning(f'VRM ports cannot be created on layer {vrm_layer} '
                      f'with net name {pwr_net_name}')

        if socket_mode.lower() == 'create':
            db_ports = db_ports.auto_port_conn(num_ports=skt_num_ports,
                                                side='top',
                                                ref_z=ref_z)
        else:
            pkg = spd.Database(pkg_fname)
            pkg.load_flags['plots'] = False
            pkg.load_data()
            pkg = pm.PortGroup(pkg)

            db_ports = pkg.transfer_socket_ports(to_db=db_ports.db,
                                                from_db_side=from_db_side,
                                                to_db_side='top',
                                                suffix='skt')
        db_ports.add_ports(save=True)
        self.record_status(db_ports)
        db_ports.db.prepare_plots(*[cap_layer_top, cap_layer_bot])

        return {cap_layer_top: self.db_ops.layer_view(cap_layer_top, db_ports.db),
                cap_layer_bot: self.db_ops.layer_view(cap_layer_bot, db_ports.db),
                'report': self.port_report}
    
    def setup_pkg_ports(self, db, sinks_mode,
                        pwr_net_names, cap_finder,
                        cap_layer_top, reduce_num_top,
                        cap_layer_bot, reduce_num_bot,
                        socket_mode, ref_z,
                        sinks_layer=None,
                        sinks_num_ports=None,
                        sinks_area=None,
                        from_db_side=None,
                        skt_num_ports=None,
                        brd_fname=None):
        '''Create ports for a typical package extraction.

        :param db: The name or object of layout to use to place ports
        :type db: str or :class:`speed.Database()`
        :param sinks_mode: Indicates how to generate sink ports.
        Can only accept 'boxes' or 'auto'.
        :type sinks_mode: str
        :param pwr_net_name: Power net name(s) to place ports
        :type pwr_net_name: str or list[str]
        :param cap_finder: Keyword to find capacitor components.
        Wildcards can be also used.
        :type cap_finder: str
        :param cap_layer_top: Top layer name to place capacitor ports
        :type cap_layer_top: str
        :param reduce_num_top: Number of ports to reduce to on the top layer
        :type reduce_num_top: int
        :param cap_layer_bot: Bottom layer name to place capacitor ports
        :type cap_layer_bot: Number of ports to reduce to on the bottom layer
        :param reduce_num_bot: Number of ports to reduce to on the bottom layer
        :type reduce_num_bot: int
        :param socket_mode: Indicates how to generate socket ports.
        Can only accept 'create' or 'transfer'.
        If 'create' mode is selected, new specified number of socket ports are created.
        If 'transfer' mode is selected, existing ports from another layout socket are copied.
        :type socket_mode: str
        :param ref_z: Port reference impedance
        :type ref_z: float
        :param sinks_layer: Relavant only if sinks_mode is 'auto'.
        Layer name where the sink ports are placed, defaults to None
        :type sinks_layer: str
        :param sinks_num_ports: Relavant only if sinks_mode is 'auto'.
        Number of sink ports to place, defaults to None
        :type sinks_num_ports: int
        :param sinks_area: Relavant only if sinks_mode is 'auto'.
        Area where the ports must be placed in the form of
        (x_bot_left, y_bot_left, x_top_right, y_top_right).
        If None the entire layout area is considered, defaults to None
        :type sinks_area: tuple[float, float, float, float]
        :param from_db_side: Relavant only if socket_mode is 'transfer'.
        Indicating from which side to copy socket ports.
        Can only accept 'bottom' (for a package) or 'top' (for a board)
        :type from_db_side: str
        :param skt_num_ports: Relavant only if socket_mode is 'create'.
        Indiciating the number of required socket ports, defaults to None
        :type skt_num_ports: int, optional
        :param brd_fname: Relavant only if socket_mode is 'transfer'.
        If so, user must provide the board layout name from which the ports are copied,
        defaults to None
        :type brd_fname: str, optional
        :return: Layer views and report of the placed ports
        :rtype: dict
        '''
        
        self.clear_status()
        db_ports = pm.PortGroup(self.db_loader(db)[0])

        if sinks_mode.lower() == 'boxes':
            db_ports = db_ports.boxes_to_ports(ref_z=ref_z)
        elif sinks_mode.lower() == 'auto':
            db_ports = db_ports.auto_port(layer=sinks_layer,
                                        net_name=pwr_net_names,
                                        num_ports=sinks_num_ports,
                                        area=sinks_area,
                                        ref_z=ref_z)
        db_ports.add_ports(save=False)
        self.record_status(db_ports)

        '''
        if socket_mode.lower() == 'create':
            db_ports = db_ports.auto_port_conn(num_ports=skt_num_ports,
                                                side='bottom')
        elif socket_mode.lower() == 'transfer':
            brd = pm.PortGroup(self.db_loader(brd_fname)[0])
            db_ports = brd.transfer_socket_ports(to_db=db_ports.db,
                                                from_db_side=from_db_side,
                                                to_db_side='bottom',
                                                suffix='skt')
        db_ports.add_ports('test.spd', save=True)
        self.record_status(db_ports)
        return self.port_report
        '''
    
        for pwr_net_name in pwr_net_names:
            db_ports = db_ports.auto_port_comp(layer=cap_layer_top,
                                                net_name=pwr_net_name,
                                                comp_find=cap_finder)
            db_ports.add_ports(save=False)
            self.record_status(db_ports)
            db_ports = db_ports.reduce_ports(layer=cap_layer_top,
                                            num_ports=reduce_num_top,
                                            select_ports=[port.name for port in db_ports.ports])
            db_ports.add_ports(save=False)
            self.record_status(db_ports)
            db_ports = db_ports.auto_port_comp(layer=cap_layer_bot,
                                                net_name=pwr_net_name,
                                                comp_find=cap_finder)
            db_ports.add_ports(save=False)
            self.record_status(db_ports)
            db_ports = db_ports.reduce_ports(layer=cap_layer_bot,
                                            num_ports=reduce_num_bot,
                                            select_ports=[port.name for port in db_ports.ports])
            db_ports.add_ports(save=False)
            self.record_status(db_ports)

            if socket_mode.lower() == 'create':
                db_ports = db_ports.auto_port_conn(num_ports=skt_num_ports,
                                                    side='bottom',
                                                    net_name=pwr_net_name,
                                                    ref_z=ref_z)
                
        if socket_mode.lower() == 'transfer':
            brd = pm.PortGroup(self.db_loader(brd_fname)[0])
            db_ports = brd.transfer_socket_ports(to_db=db_ports.db,
                                                from_db_side=from_db_side,
                                                to_db_side='bottom',
                                                suffix='skt')
        db_ports.add_ports(save=True)
        self.record_status(db_ports)
        db_ports.db.prepare_plots(*[cap_layer_top, cap_layer_bot])

        return {cap_layer_top: self.db_ops.layer_view(cap_layer_top, db_ports.db),
                cap_layer_bot: self.db_ops.layer_view(cap_layer_bot, db_ports.db),
                'report': self.port_report}

    def auto_copy(self, src_db, dst_db, force=False):
        """Automatically copy ports from one layout to a different layout.
        This functionality is based on identifing common pin name in both layouts
        as well as the relative distance and rotation angle between them.

        :param src_db: The name of the source layout with the ports,
        or the database object
        :type src_db: str or :class:`speed.Database()`
        :param dst_db: The name of the destination layout without the ports,
        or the database object
        :type dst_db: str or :class:`speed.Database()`
        :param force: If True new nodes (if existing nodes cannot be found)
        are added to the layout in order to connect a copied port,
        defaults to False
        :type force: bool, optional
        :return: Layer views and report of the placed ports
        :rtype: dict
        """

        self.clear_status()
        src, dst = self.db_loader(src_db, dst_db)
        src_ports = pm.PortGroup(src)
        dst_ports = src_ports.auto_copy(dst, force)
        self.record_status(dst_ports)

        return self.report_results(dst_ports)
    
    def copy(self, x_src, y_src, x_dst, y_dst,
             src_db, dst_db=None, ref_z=None, force=False):
        """Copies ports from one layout to another or within the same layout
        based on two pairs of coordinates, referencing the source and destination
        locations.

        :param x_src: The source x coordinate
        :type x_src: float
        :param y_src: The source y coordinate
        :type y_src: float
        :param x_dst: The destination x coordinate,
        which can be in the same layout
        :type x_dst: float
        :param y_dst: The destination y coordinate,
        which can be in the same layout
        :type y_dst: float
        :param src_db: The source layout file name or layout object
        :type src_db: str or :class:`speed.Database()`
        :param dst_db: The destination layout file name or layout object,
        defaults to None
        :type dst_db: str or :class:`speed.Database()`, optional
        :param ref_z: The reference impedance of the copied ports, defaults to None
        :type ref_z: float, optional
        :param force: If True, insert new nodes, if required, in order to connect a copied port,
        defaults to False
        :type force: bool, optional
        :return: Layer views and report of the placed ports
        :rtype: dict
        """

        self.clear_status()
        src, dst = self.db_loader(src_db, dst_db)
        src_ports = pm.PortGroup(src)
        dx = x_dst - x_src
        dy = y_dst - y_src
        dst_ports = src_ports.copy(dx, dy, dst,
                                   ref_z=ref_z,
                                   force=force)
        self.record_status(dst_ports)
        
        return self.report_results(dst_ports)
    
    def array_copy(self, src_db,
                    x_src, y_src,
                    x_horz, y_vert,
                    nx, ny,
                    dst_db=None, ref_z=None,
                    force=False):
        """Array copies all existing ports as a block array horizontally and vertically.

        :param src_db: The name of the source layout with the ports,
        or the database object
        :type src_db: str or :class:`speed.Database()`
        :param x_src: The source x coordinate
        :type x_src: float
        :param y_src: The source y coordinate
        :type y_src: float
        :param x_horz: Horizontal distance between copied blocks
        :type x_horz: float
        :param y_vert: Vertical distance between copied blocks
        :type y_vert: float
        :param nx: Number of blocks in the x direction
        :type nx: int
        :param ny: Number of blocks in the y direction
        :type ny: int
        :param dst_db: The name of the destination layout without the ports,
        or the database object, defaults to None
        :type dst_db: str or :class:`speed.Database()`, optional
        :param ref_z: The reference impedance of the copied ports, defaults to None
        :type ref_z: float, optional
        :param force: If True, insert new nodes, if required, in order to connect a copied port,
        defaults to False
        :type force: bool, optional
        :return: Layer views and report of the placed ports
        :rtype: dict
        """        
        
        self.clear_status()
        src, dst = self.db_loader(src_db, dst_db)
        src_ports = pm.PortGroup(src)
        dst_ports = src_ports.array_copy(to_db=dst,
                                        x_src=x_src,
                                        y_src=y_src,
                                        x_horz=x_horz,
                                        y_vert=y_vert,
                                        nx=nx, ny=ny,
                                        ref_z=ref_z,
                                        force=force
                                    )
        self.record_status(dst_ports)
        
        return self.report_results(dst_ports)
    
    def mirror_copy(self, src_db, x_src, y_src,
                    x_dst, y_dst,
                    dst_db=None, ref_z=None,
                    force=False):
        """Mirror copies along any axis determined by source and destionation reference coordinates.

        :param src_db: The name of the source layout with the ports,
        or the database object
        :type src_db: str or :class:`speed.Database()`
        :param x_src: The source x coordinate
        :type x_src: float
        :param y_src: The source y coordinate
        :type y_src: float
        :param x_dst: The destination x coordinate,
        which can be in the same layout
        :type x_dst: float
        :param y_dst: The destination y coordinate,
        which can be in the same layout
        :type y_dst: float
        :param dst_db: The name of the destination layout without the ports,
        or the database object, defaults to None
        :type dst_db: str or :class:`speed.Database()`, optional
        :param ref_z: The reference impedance of the copied ports, defaults to None
        :type ref_z: float, optional
        :param force: If True, insert new nodes, if required, in order to connect a copied port,
        defaults to False
        :type force: bool, optional
        :return: Layer views and report of the placed ports
        :rtype: dict
        """        
        
        self.clear_status()
        src, dst = self.db_loader(src_db, dst_db)
        src_ports = pm.PortGroup(src)
        dst_ports = src_ports.mirror_copy(to_db=dst,
                                        x_src=x_src,
                                        y_src=y_src,
                                        x_dst=x_dst,
                                        y_dst=y_dst,
                                        ref_z=ref_z,
                                        force=force)
        self.record_status(dst_ports)
        
        return self.report_results(dst_ports)
    
    def rotate_copy(self, src_db,
                    x_src, y_src,
                    x_dst, y_dst, rot_angle,
                    dst_db=None,
                    ref_z=None,
                    force=False):
        """Rotate copies based on the provided rotation angle and reference points.
        Negative angle rotates CW, while positive angle rotates CCW.

        :param src_db: The name of the source layout with the ports,
        or the database object
        :type src_db: str or :class:`speed.Database()`
        :param x_src: The source x coordinate
        :type x_src: float
        :param y_src: The source y coordinate
        :type y_src: float
        :param x_dst: The destination x coordinate,
        which can be in the same layout
        :type x_dst: float
        :param y_dst: The destination y coordinate,
        which can be in the same layout
        :type y_dst: float
        :param rot_angle: Rotation angle to copy the ports.
        Negative angle rotates CW, while positive angle rotates CCW.
        :type rot_angle: float
        :param dst_db: The name of the destination layout without the ports,
        or the database object, defaults to None
        :type dst_db: str or :class:`speed.Database()`, optional
        :param ref_z: The reference impedance of the copied ports, defaults to None
        :type ref_z: float, optional
        :param force: If True, insert new nodes, if required, in order to connect a copied port,
        defaults to False
        :type force: bool, optional
        :return: Layer views and report of the placed ports
        :rtype: dict
        """

        self.clear_status()
        src, dst = self.db_loader(src_db, dst_db)
        src_ports = pm.PortGroup(src)
        dst_ports = src_ports.rotate_copy(to_db=dst,
                                        x_src=x_src,
                                        y_src=y_src,
                                        x_dst=x_dst,
                                        y_dst=y_dst,
                                        rot_angle=rot_angle,
                                        ref_z=ref_z,
                                        force=force)
        self.record_status(dst_ports)
        
        return self.report_results(dst_ports)
    
    def get_sinks_vrms_ldos_info(self, db, source_type, csv_fname=None):
        """Finds and returns sink and vrm information in the given layout.

        :param src_db: The name of the layout with the sinks and/or vrms,
        or the database object
        :type src_db: str or :class:`speed.Database()`
        :param csv_fname: Name of the csv file with sinks or vrms setup definition, defaults to None
        :type csv_fname: str, optional
        :param source_type: Source or sink type. Can only accept 'sink', 'vrm', or 'ldo'
        :type source_type: str
        :return: A dictionary with sink and vrm information
        :rtype: dict
        """        

        if csv_fname is not None:
            return pd.read_csv(csv_fname).fillna('').to_dict(orient='list')
        
        db_sinks_vrms_ldos = tasks.PdcTask(self.db_loader(db)[0])

        if source_type == 'sink':
            sinks_fname = Path(db_sinks_vrms_ldos.db.path) / Path(f'{Path(db_sinks_vrms_ldos.db.name).stem}_sinksinfo.csv')
            logger.info(f'Sinks setup file {sinks_fname} is created')
            return db_sinks_vrms_ldos.export_sink_setup(sinks_fname).to_dict(orient='list')
        elif source_type == 'vrm':
            vrms_fname = Path(db_sinks_vrms_ldos.db.path) / Path(f'{Path(db_sinks_vrms_ldos.db.name).stem}_vrmsinfo.csv')
            logger.info(f'VRMs setup file {vrms_fname} is created')
            return db_sinks_vrms_ldos.export_vrm_setup(vrms_fname).to_dict(orient='list')
        elif source_type == 'ldo':
<<<<<<< HEAD
            ldos_fname = Path(db_sinks_vrms_ldos.db.path) / Path(f'{Path(db_sinks_vrms_ldos.db.name).stem}_ldosinfo.csv')
            logger.info(f'LDOs setup file {ldos_fname} is created')
            return db_sinks_vrms_ldos.export_ldo_setup(ldos_fname).to_dict(orient='list')
=======
            ldos_fname = Path(db_sinks_vrms_ldos.db.path) / Path(f'{Path(db_sinks_vrms_ldos.db.name).stem}_ldossinfo.csv')
            logger.info(f'LDOs setup file {ldos_fname} is created')
            return db_sinks_vrms_ldos.export_vrm_setup(ldos_fname).to_dict(orient='list')
>>>>>>> 1c6304a4c09f18c88dd2e91926471b4e2ffc3c7e
        else:
            return None
    
    def modify_sink_info(self, db, sinks_fname, sink_info):
        """Modifies sink parameters as specified by the user through the frontend.

        :param db: The name or object of layout to use
        :type db: str or :class:`speed.Database()`
        :param sinks_fname: The name of the csv setup file
        :type sinks_fname: str
        :param sink_info: New sink parameters to be modified in the layout file
        :type sink_info: dict
        """        

        db_sinks = tasks.PdcTask(self.db_loader(db)[0])
        df_sinks_info = pd.DataFrame(sink_info)
        df_sinks_info.to_csv(sinks_fname, index=False)
        logger.info(f'Sinks setup file {sinks_fname} is created')
<<<<<<< HEAD

=======
        
>>>>>>> 1c6304a4c09f18c88dd2e91926471b4e2ffc3c7e
        db_sinks.import_sink_setup(sinks_fname)
        db_sinks.db.save()

    def modify_vrm_info(self, db, vrms_fname, vrm_info):
        """Modifies VRM parameters as specified by the user in the frontend.

        :param db: The name or object of layout to use
        :type db: str or :class:`speed.Database()`
        :param vrms_fname: The name of the csv setup file
        :type vrms_fname: str
        :param vrm_info: New vrm parameters to be modified in the layout file
        :type vrm_info: dict
        """        

        db_vrms = tasks.PdcTask(self.db_loader(db)[0])
        df_vrms_info = pd.DataFrame(vrm_info)
        df_vrms_info.to_csv(vrms_fname, index=False)
        logger.info(f'VRMs setup file {vrms_fname} is created')

        db_vrms.import_vrm_setup(vrms_fname)
        db_vrms.db.save()
<<<<<<< HEAD

    def modify_ldo_info(self, db, ldos_fname, ldo_info):
        """Modifies LDO parameters as specified by the user in the frontend.

        :param db: The name or object of layout to use
        :type db: str or :class:`speed.Database()`
        :param ldos_fname: The name of the csv setup file
        :type ldos_fname: str
        :param ldo_info: New ldo parameters to be modified in the layout file
        :type ldo_info: dict
        """        

        db_ldos = tasks.PdcTask(self.db_loader(db)[0])
        df_ldos_info = pd.DataFrame(ldo_info)
        df_ldos_info.to_csv(ldos_fname, index=False)
        logger.info(f'LDOs setup file {ldos_fname} is created')

        db_ldos.import_ldo_setup(ldos_fname)
        db_ldos.db.save()
=======
>>>>>>> 1c6304a4c09f18c88dd2e91926471b4e2ffc3c7e
    
    def sinks_vrms_to_ports(self, db, stimuli, to_fname=None,
                            ref_z=10, sink_suffix=None, vrm_suffix=None):
        """Places ports where sinks or/and VRMs are placed.
        The existing sinks or/and VRMs are not removed.

        :param db: The name of the layout with the sinks or/and VRMs,
        or the database object
        :type db: str or :class:`speed.Database()`
        :param stimuli: Indicating if sinks or VRMs or both should be convereted to ports.
        Accepts only 'sinks', 'VRMs', 'both'.
        :type stimuli: str
        :param to_fname: Name of the new layout with the ports.
        If None, overwrites the existing layout, defaults to None
        :type to_fname: None or str, optional
        :param ref_z: Port reference impendace in Ohm, defaults to 10
        :type ref_z: float, optional
        :param sink_suffix: Suffix to add to the name of the port
        that is derived from the name of the sink, defaults to None
        :type sink_suffix: None or str, optional
        :param vrm_suffix: Suffix to add to the name of the port
        that is derived from the name of the VRM defaults to None
        :type vrm_suffix: None or str, optional
        :return: Layer views and report of the placed ports
        :rtype: dict
        """
        
        self.clear_status()
        db_stimuli = pm.PortGroup(self.db_loader(db)[0])
        if stimuli.lower() == 'sinks' or stimuli.lower() == 'both':
            if db_stimuli.db.sinks:
                logger.info('Sinks are found:')
                for sink_name in db_stimuli.db.sinks.keys():
                    logger.info(f'\t{sink_name}')
                db_stimuli = db_stimuli.sinks_to_ports(ref_z=ref_z,
                                                 suffix=sink_suffix)
                db_stimuli.add_ports(save=False)
                self.record_status(db_stimuli)
            else:
                logger.warning('Cannot find sinks therefore ports cannot be created')
        if stimuli.lower() == 'vrms' or stimuli.lower() == 'both':
            if db_stimuli.db.vrms:
                logger.info('VRMs are found:')
                for vrm_name in db_stimuli.db.vrms.keys():
                    logger.info(f'\t{vrm_name}')
                db_stimuli = db_stimuli.vrms_to_ports(ref_z=ref_z,
                                                 suffix=vrm_suffix)
                db_stimuli.add_ports(save=False)
                self.record_status(db_stimuli)
            else:
                logger.warning('Cannot find VRMs, therefore, ports cannot be created')

        db_stimuli.db.save(to_fname)

        return self.report_results(db_stimuli)
    
    def get_ports_list(self, db):      
        """Generates a list of port names and saves it as .csv file.

        :param db: The name of the layout with ports,
        or the database object
        :type db: str or :class:`speed.Database()`
        :return: Dictionary with port names
        :rtype: dict
        """        

        db_ports = pm.PortGroup(self.db_loader(db)[0])
        df_port_list = db_ports.export_port_info(ports_fname=Path(db_ports.db.path)
                                                            / Path(f'{Path(db_ports.db.name).stem}_portlist.csv'),
                                                names_only=True)
        
        return df_port_list.to_dict(orient='list')
        
    def ports_to_vrms_sinks(self, db, to_fname=None,
                            sink_suffix=None, vrm_suffix=None):
        """Places sinks and VRMs where ports are located based on the list saved by :method:`PortHandler.get_ports_list()`.

        :param db: The name of the layout with ports,
        or the database object
        :type db: str or :class:`speed.Database()`
        :param to_fname: Name of the new layout with the ports.
        If None, overwrites the existing layout, defaults to None
        :type to_fname: None or str, optional
        :return: Layer views of the placed sinks/VRMs
        :rtype: dict
        """

        self.clear_status()
        db_vrms_sinks = tasks.PdcTask(self.db_loader(db)[0])
        
        port_list_fname = (Path(db_vrms_sinks.db.path)
                           / Path(f'{Path(db_vrms_sinks.db.name).stem}_portlist.csv'))
        self.port_report += db_vrms_sinks.ports_to_vrms(port_fname=port_list_fname,
                                                        suffix=vrm_suffix)
        self.port_report += db_vrms_sinks.ports_to_sinks(port_fname=port_list_fname,
                                                         suffix=sink_suffix)
        db_vrms_sinks.db.save(to_fname)

        return self.report_results(db_vrms_sinks, add_ports=False)
    
    def auto_vrm_ports(self, db, power_nets, layer, to_fname=None,
                        ind_finder='*L*', ref_z=10):
        """Automatically places ports where board VRMs with external inductors are recognized.

        :param db: The name of the layout or the database object
        :type db: str or :class:`speed.Database()`
        :param power_nets: Power net names for which to place ports where the VRMS are
        :type power_nets: str or list[str]
        :param layer: Layer name on which to place ports
        :type layer: str
        :param to_fname: Name of the new layout with the ports.
        If None, overwrites the existing layout, defaults to None
        :type to_fname: None or str, optional
        :param ind_finder: Keyword with wildcards to find VRMs' inductors,
        defaults to '*L*'
        :type ind_finder: str, optional
        :param ref_z: Port reference impendace in Ohm, defaults to 10
        :type ref_z: float, optional
        :return: Layer views and report of the placed ports
        :rtype: dict
        """        

        self.clear_status()
        db_ports = pm.PortGroup(self.db_loader(db)[0])
        if layer.lower() =='top':
            layer = db_ports.db.layer_names(verbose=False)[0]
        elif layer.lower() =='top':
            layer = db_ports.db.layer_names(verbose=False)[-1]
        
        db_ports = db_ports.auto_vrm_ports(layer=layer, net_name=power_nets,
                                           find_comps=ind_finder, ref_z=ref_z)
        db_ports.add_ports(to_fname, save=True)
        self.record_status(db_ports)

        return self.report_results(db_ports)
    
    def auto_ports(self, db, power_nets, layer, num_ports,
                   area=None, ref_z=1, port3D=False, prefix=None):
        """Automatically places specific number of ports based on the provided information.

        :param db: The name of the layout or the database object
        :type db: str or :class:`speed.Database()`
        :param power_nets: Power net names for which to place ports where the VRMS are
        :type power_nets: str or list[str]
        :param layer: Layer name on which to place ports
        :type layer: str
        :param num_ports: Number of ports to place
        :type num_ports: int
        :param area: If provided, specifies the area within which ports are placed.
        The area should be provided in this order: (x_bot_left, y_bot_left, x_top_right, y_top_right).
        :type area: tuple[int, int, int, int]
        :param ref_z: Port reference impedance in Ohm, defaults to 1
        :type ref_z: float, optional
        :param port3D: If True 3D ports are placed, otherwise 2D ports are placed, defaults to False
        :type port3D: bool, optional
        :param prefix: Prefix string to the beginning of the port name, defaults to None
        :type prefix: str, optional
        :return: Layer views and report of the placed ports
        :rtype: dict
        """        
        
        self.clear_status()
        db_ports = pm.PortGroup(self.db_loader(db)[0])
        db_ports = db_ports.auto_port(layer=layer,
                                      net_name=power_nets,
                                      num_ports=num_ports,
                                      area=area, ref_z=ref_z,
                                      port3D=port3D, prefix=prefix)
        
        db_ports.add_ports(save=True)
        self.record_status(db_ports)

        return self.report_results(db_ports)
    
    def auto_socket_ports(self, db, num_ports, side, ref_z=10):
        """Automatically places selected number of ports using socket pins.
        The ports are placed on the enabled power pin rails.
        If several power rails are enabled, the number of ports for each rail
        is proportionally determined based on the number of pins.

        :param db: The name of the layout or the database object
        :type db: str or :class:`speed.Database()`
        :param num_ports: Total number of ports
        :type num_ports: int
        :param side: Accepts only 'bottom' (for package) or 'top' (for board) parameters.
        :type side: str
        :param ref_z: Port reference impedance, defaults to 10
        :type ref_z: int, optional
        :return: Layer views and report of the placed ports
        :rtype: dict
        """        

        self.clear_status()
        db_ports = pm.PortGroup(self.db_loader(db)[0])
        db_ports = db_ports.auto_port_conn(num_ports,
                                           side, ref_z)
        db_ports.add_ports(save=True)
        self.record_status(db_ports)

        return self.report_results(db_ports)

    def transfer_socket_ports(self, from_db, to_db,
                              from_db_side, to_db_side,
                              suffix=None):
        """Copies socket ports from a layout to another layout.
        For example, board top socket ports are copied to the corresponding
        bottom of the package. The copy is done based on pin names, ensuring
        accurate port allocation on each side.

        :param db: The name of the layout or the database object
        :type db: str or :class:`speed.Database()`
        :param to_db: Database where ports are coppied to
        :type to_db: :class:`speed.Database()`
        :param from_db_side: Accepts only 'bottom' (for package)
        or 'top' (for board) parameters.
        :type side: str
        :param to_db_side: Accepts only 'bottom' (for package)
        or 'top' (for board) parameters.
        :type side: str
        :param suffix: Suffix to add to each coppied port, defaults to None
        :type suffix: str, optional
        :return: Layer views and report of the placed ports
        :rtype: dict
        """        
        

        self.clear_status()
        from_db = pm.PortGroup(self.db_loader(from_db)[0])
        to_db = self.db_loader(to_db)[0]
        db_ports = from_db.transfer_socket_ports(
                                        to_db, from_db_side,
                                        to_db_side, suffix
                                    )
        
        db_ports.add_ports(save=True)
        self.record_status(db_ports)

        return self.report_results(db_ports)