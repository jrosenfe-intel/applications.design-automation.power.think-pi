import sys
sys.path.append(r"C:\thinkpi_dev\core_latest")
#sys.path.append(r"D:\jrosenfe\ThinkPI\applications.design-automation.power.think-pi")

import os
import signal
import time
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Any
import json

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse

import asyncio
import queue
import uvicorn

from src.models.NewProject import NewProject
from src.models.DeleteProject import DeleteProject
from src.models.SpdData import SpdData
from src.models.MaterialData import MaterialData
from src.models.SpdLayerData import SpdLayerData
from src.models.SaveMaterialData import SaveMaterialData
from src.models.SaveStackupData import SaveStackupData
from src.models.LoadStackupData import LoadStackupData
from src.models.ApplyStackupData import ApplyStackupData
from src.models.ApplyPadstackData import ApplyPadstackData
from src.models.AutoStackupData import AutoStackupData
from src.models.PadStackData import PadStackData
from src.models.PreprocessData import PreprocessData
from src.models.MotherboardData import MotherboardData
from src.models.PackageData import PackageData
from src.models.AutoCopyData import AutoCopyData
from src.models.CopyData import CopyData
from src.models.ArrayCopyData import ArrayCopyData
from src.models.MirrorCopyData import MirrorCopyData
from src.models.RotateCopyData import RotateCopyData
from src.models.ReportData import ReportData
from src.models.AutoVrmPortsData import AutoVrmPortsData
from src.models.TransferSocketPortsData import TransferSocketPortsData
from src.models.AutoSocketPortsData import AutoSocketPortsData
from src.models.GetPortInfoData import GetPortInfoData
from src.models.ModifyPortInfo import ModifyPortInfo
from src.models.SinksVrmsLdosInfo import SinksVrmsLdosInfo
from src.models.ModifySinkInfo import ModifySinkInfo
from src.models.ModifyVrmInfo import ModifyVrmInfo
from src.models.AutoPortsInfo import AutoPortsInfo
from src.models.BoxesToPortsInfo import BoxesToPortsInfo
from src.models.ReducePortsInfo import ReducePortsInfo
from src.models.SinksVrmsToPortsInfo import SinksVrmsToPortsInfo
from src.models.PathContent import PathContent
from src.models.ServerInfo import ServerInfo

import thinkpi.backend_api.api as api
from thinkpi.backend_api import lib
#from thinkpi.config import thinkpi_conf as cfg
from thinkpi import __version__

app = FastAPI()

origins = [
    # "http://localhost.tiangolo.com",
    # "https://localhost.tiangolo.com",
    # "http://localhost",
    "http://localhost:8000",
    "http://10.39.135.137:8000",
    # "http://1ocalhost:8001",
    # "http://10.39.135.137:8001",
    # "http://localhost:8080",
    # "http://localhost:8081",
    # "http://10.39.135.137:8081",
    # "http://10.212.126.102:8080",
    # "http://localhost:8091",
    # "http://10.39.135.137:8091",
    "http://10.39.135.137:5173",
    "http://localhost:5173",
    "http://localhost:4173",
    "http://10.39.135.137:4173",
    "http://localhost:3000",
    "http://10.39.135.137:3000",
    "https://10.18.218.176:3000",
    "https://10.18.218.176:8080",
    "http://thinkpi.apps1-fm-int.icloud.intel.com:3000",
    "http://thinkpi.apps1-fm-int.icloud.intel.com:8000",
    "http://thinkpi.apps1-fm-int.icloud.intel.com:8080",
    "https://thinkpi.apps1-fm-int.icloud.intel.com:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

processed_Dbapi_object = {}
all_queues = {}
current_queue = None

lib_manager_path = r'D:\jrosenfe\ThinkPI\lib_manager'
material_path = r'D:\jrosenfe\ThinkPI\material\\'
spd_path = r'D:\jrosenfe\ThinkPI\spd_files\\'

'''
@dataclass
class CurrentQueue:
    queue: queue.Queue
'''

#current_queue = CurrentQueue(None)
#que = queue.Queue()
#ports = api.PortHandler(que)
#ports = api.PortHandler()

# @app.post("/")
# async def root():
#     lib_mgr = lib.LibManager(root=lib_manager_path)
#     res = lib_mgr.path_to_dict()
#     return JSONResponse(content=res)

@app.get("/")
async def root():
    return JSONResponse(content={'result': __version__})
    # lib_mgr = lib.LibManager()
    # return JSONResponse(content=lib_mgr.scan_servers())

@app.get("/stop-server")
def stop_server():
    os.kill(os.getpid(), signal.SIGTERM)

@app.get("/ping")
def ping():
    return JSONResponse(content={'result': 'pong'})

@app.get("/update")
def update():
    lib_mgr = lib.LibManager()
    lib_mgr.update()
    return JSONResponse(content={'result': 'success'})

@app.post("/path")
async def path(val: PathContent):
    lib_mgr = lib.LibManager()
    res = lib_mgr.get_path_content(val.path)
    return JSONResponse(content=res)

'''
@app.post("/resource-info")
async def get_resource_info():
    lib_mgr = lib.LibManager(root=lib_manager_path)
    res = lib_mgr.get_resource_info()
    return JSONResponse(content=res)

@app.post("/server-list")
async def get_server_list():
    lib_mgr = lib.LibManager(root=lib_manager_path)
    res = lib_mgr.get_server_list()
    return JSONResponse(content=res)
'''

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

class SharedData:
    def __init__(self):
        self.session_queues = {}
        self.ports = None

ws_manager = ConnectionManager()
sd = SharedData()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await ws_manager.connect(websocket)
    que = queue.Queue()
    sd.session_queues[session_id] = que
    sd.ports = api.PortHandler(que)
    while True:
        # data = await websocket.receive_text()
        try:
            data = que.get_nowait()
            await ws_manager.send_personal_message(data, websocket)
        except queue.Empty:
            await asyncio.sleep(1)
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)
            del sd.session_queues[session_id]
            await manager.broadcast(f"User #{session_id} left")

@app.post("/new-project")
def new_project(val: NewProject):
    lib_mgr = lib.LibManager(root=lib_manager_path)
    lib_mgr.new_project(project_name=val.project_name,
                        study_name=val.study_name,
                        rail_name=val.rail_name)

    res = lib_mgr.path_to_dict()
    # res = lib_mgr.tree(verbose=False)
    return JSONResponse(content=res)

@app.post("/copy-project")
def copy_project(val: NewProject):
    lib_mgr = lib.LibManager(root=lib_manager_path)
    lib_mgr.new_project(project_name=val.project_name,
                        study_name=val.study_name,
                        rail_name=val.rail_name,
                        copy_project=val.copy_project)

    res = lib_mgr.path_to_dict()
    # res = lib_mgr.tree(verbose=False)
    return JSONResponse(content=res)


@app.post("/new-study")
def new_study(val: NewProject):
    lib_mgr = lib.LibManager(root=lib_manager_path)
    lib_mgr.new_study(project_name=val.project_name,
                      study_name=val.study_name,
                      rail_name=val.rail_name)

    res = lib_mgr.path_to_dict()
    # res = lib_mgr.tree(verbose=False)
    return JSONResponse(content=res)


@app.post("/new-rail")
def new_rail(val: NewProject):
    lib_mgr = lib.LibManager(root=lib_manager_path)
    lib_mgr.new_rail(project_name=val.project_name,
                     study_name=val.study_name,
                     rail_name=val.rail_name)

    res = lib_mgr.path_to_dict()
    # res = lib_mgr.tree(verbose=False)
    return JSONResponse(content=res)


@app.post("/add-folder")
def add_folder(val: DeleteProject):
    lib_mgr = lib.LibManager(root=lib_manager_path)
    lib_mgr.add_folder(val.path)

    time.sleep(1)
    res = lib_mgr.path_to_dict()
    # res = lib_mgr.tree(verbose=False)
    return JSONResponse(content=res)


@app.post("/delete-project")
def delete_project(val: DeleteProject):
    lib_mgr = lib.LibManager(root=lib_manager_path)
    lib_mgr.delete_folder(val.path)

    res = lib_mgr.path_to_dict()
    return JSONResponse(content=res)


@app.post("/new-study")
def new_study(val: NewProject):
    lib_mgr = lib.LibManager(root=lib_manager_path)
    lib_mgr.new_study(project_name=val.project_name,
                      study_name=val.study_name,
                      rail_name=val.rail_name)

    res = lib_mgr.tree(verbose=False)

    return JSONResponse(content=res)


@app.post("/new-rail")
def new_rail(val: NewProject):
    lib_mgr = lib.LibManager(root=lib_manager_path)
    lib_mgr.new_rail(project_name=val.project_name,
                     study_name=val.study_name,
                     rail_name=val.rail_name)

    res = lib_mgr.path_to_dict()

    return JSONResponse(content=res)

@app.post("/upload-spd")
def upload_spd(file: UploadFile = File(...)):
    with open(f'upload/{file.filename}', "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"file_name": file.filename}

@app.post("/load-spd-data")
def load_SPD_data(data: SpdData):
    #path = name.filename
    #all_queues[path] = current_queue.queue
    db_api = api.DbApi(data.layout_fname, sd.session_queues[data.session_id])
    j = db_api.load_data()
    processed_Dbapi_object[data.layout_fname] = db_api

    return JSONResponse(content=j)

@app.post("/delete-spd")
def delete_SPD(name: SpdData):
    filename = name.filename
    api.loaded_layouts[filename].pop(filename)
    processed_Dbapi_object[filename].pop(filename)
    del all_queues[filename]

    return {"status": "success"}

@app.post("/load-spd-by-layer")
def load_SPD_by_Layer(name: SpdLayerData):
    filename = name.filename
    # path = "E:\intel\spd files\\" + filename
    # db_api = api.DbApi(path)
    # db_api.load_data()

    j = processed_Dbapi_object[filename].layer_view(name.layer)

    return JSONResponse(content=j)

@app.post("/load-material-data")
def load_material_data(data: MaterialData):
    #db_api = api.DbApi(data.layout_fname)
    #material_response = db_api.get_material(data.fname)
    material_response = processed_Dbapi_object[data.layout_fname].get_material(data.material_fname)

    return JSONResponse(content=material_response)

@app.post("/save-material-data")
def save_material_data(data: SaveMaterialData):
    path = data.filename
    material_data = data.material_data
    db_api = api.DbApi(path)

    material_response = db_api.save_material(path, material_data)

    return JSONResponse(content=material_response)

@app.post("/get-stackup")
def get_stackup(data: SpdData):
    j = processed_Dbapi_object[data.layout_fname].get_stackup()

    return JSONResponse(content=j)

@app.post("/load-stackup")
def save_stackup(data: LoadStackupData):
    db_api = api.DbApi()

    return JSONResponse(content=db_api.load_stackup(data.fname))

@app.post("/save-stackup")
def save_stackup(data: SaveStackupData):
    if Path(data.csv_fname).name == data.csv_fname:
        data.csv_fname = str(Path(data.spd_filename).parent / Path(data.csv_fname))
    stackup_response = processed_Dbapi_object[data.spd_filename].save_stackup(
                                    data.csv_fname, data.stackup_data
                        )

@app.post('/apply-stackup')
def apply_stackup(data: ApplyStackupData):
    if Path(data.stackup_fname).name == data.stackup_fname:
        data.stackup_fname = str(Path(data.spd_fname).parent / Path(data.stackup_fname))
    processed_Dbapi_object[data.spd_fname].apply_stackup(
        data.stackup_fname, data.material_fname
    )

@app.post("/auto-setup-stackup")
def auto_setup_Stackup(data: AutoStackupData):
    spd_filename = data.spd_filename
    filename = data.filename
    unit = data.unit
    dielec_thickness = float(
        data.dielec_thickness) if data.dielec_thickness else None
    metal_thickness = float(
        data.metal_thickness) if data.metal_thickness else None
    core_thickness = float(
        data.core_thickness) if data.core_thickness else None
    conduct = float(data.conduct) if data.conduct else None

    dielec_material = data.dielec_material
    metal_material = data.metal_material
    core_material = data.core_material
    fillin_dielec_material = data.fillin_dielec_material
    er = data.er
    loss_tangent = data.loss_tangent

    stackup_response = processed_Dbapi_object[spd_filename].auto_setup_stackup(
        filename, unit, dielec_thickness, metal_thickness, core_thickness,
        conduct, str(dielec_material), metal_material, core_material,
        fillin_dielec_material, er, loss_tangent)

    return JSONResponse(content=stackup_response)

@app.post('/apply-padstack')
def apply_stackup(data: ApplyPadstackData):
    if Path(data.padstack_fname).name == data.padstack_fname:
        data.padstack_fname = str(Path(data.spd_fname).parent / Path(data.padstack_fname))
    processed_Dbapi_object[data.spd_fname].apply_padstack(
        data.padstack_fname, data.material_fname
    )

@app.post("/get-padstack")
def get_PadStack(data: SpdData):
    j = processed_Dbapi_object[data.layout_fname].get_padstack()

    return JSONResponse(content=j)

@app.post("/auto-setup-padstack")
def auto_setup_padstack(data: PadStackData):
    if data.material == 'Default':
        data.material = None
    if data.inner_fill_material == 'Default':
        data.inner_fill_material = None
    if data.outer_coating_material == 'Default':
        data.outer_coating_material = None

    padstack_response = processed_Dbapi_object[data.spd_fname].auto_setup_padstack(
        data.csv_fname, data.layout_type, data.brd_plating,
        data.pkg_gnd_plating, data.pkg_pwr_plating, data.conduct, data.material,
        data.inner_fill_material, data.outer_thickness,
        data.outer_coating_material, data.unit
    )

    return JSONResponse(content=padstack_response)

def prepend_path(layout_fname, other_fname):
    if other_fname is not None and Path(other_fname).name == other_fname:
        return str(Path(layout_fname).parent / Path(other_fname))
    else:
        return other_fname

@app.post("/preprocess")
def preprocess(data: PreprocessData):
    data.stackup_fname = prepend_path(data.layout_fname, data.stackup_fname)
    data.padstack_fname = prepend_path(data.layout_fname, data.padstack_fname)
    data.material_fname = prepend_path(data.layout_fname, data.material_fname)
    data.post_processed_fname = prepend_path(data.layout_fname, data.post_processed_fname)

    # if data.stackup_fname is not None and Path(data.stackup_fname).name == data.stackup_fname:
    #     data.stackup_fname = str(Path(data.layout_fname).parent / Path(data.stackup_fname))
    # if data.padstack_fname is not None and Path(data.padstack_fname).name == data.padstack_fname:
    #     data.padstack_fname = str(Path(data.layout_fname).parent / Path(data.padstack_fname))
    # if data.material_fname is not None and Path(data.material_fname).name == data.material_fname:
    #     data.material_fname = str(Path(data.layout_fname).parent / Path(data.material_fname))
    # if data.post_processed_fname is not None and Path(data.post_processed_fname).name == data.post_processed_fname:
    #     data.post_processed_fname = str(Path(data.layout_fname).parent / Path(data.post_processed_fname))
    
    processed_Dbapi_object[data.layout_fname].preprocess(
        data.power_nets, data.ground_nets,
        data.stackup_fname, data.padstack_fname,
        data.material_fname, data.default_conduct,
        data.cut_margin, data.post_processed_fname,
        data.delete_unused_nets
    )
    
    return {"status": "success"}

@app.post("/motherboard")
def motherboard(data: MotherboardData):
    filename = data.spd_filename
    #ports = api.PortHandler(all_queues[filename])
    ports_fname = data.ports_fname
    # pwr_net_name = ["P1V1_L", "P3V3_E"]
    pwr_net_name = data.pwr_net_name
    cap_layer_top = data.cap_layer_top if data.cap_layer_top else None
    reduce_num_top = int(data.reduce_num_top) if data.reduce_num_top else None
    cap_layer_bot = data.cap_layer_bot if data.cap_layer_bot else None
    reduce_num_bot = int(data.reduce_num_bot) if data.reduce_num_bot else None
    vrm_layer = data.vrm_layer if data.vrm_layer else None
    socket_mode = data.socket_mode if data.socket_mode else None
    from_db_side = data.from_db_side if data.from_db_side else None
    skt_num_ports = int(data.skt_num_ports) if data.skt_num_ports else None
    pkg_fname = data.pkg_fname if data.pkg_fname else None
    cap_finder = data.cap_finder if data.cap_finder else None
    ref_z = float(data.ref_z) if data.ref_z else None

    motherboard_response = ports.setup_motherboard_ports(filename,
                                                         pwr_net_name, cap_finder, cap_layer_top, reduce_num_top,
                                                         cap_layer_bot, reduce_num_bot, vrm_layer, ref_z,
                                                         socket_mode, from_db_side, skt_num_ports, pkg_fname)

    return JSONResponse(content=motherboard_response)

@app.post("/package")
def package(data: PackageData):
    filename = data.spd_filename
    #ports = api.PortHandler(all_queues[filename])
    sinks_mode = data.sinks_mode if data.sinks_mode else None
    ports_fname = data.ports_fname
    #pwr_net_name = ["P1V1_L", "P3V3_E"]
    pwr_net_name = data.pwr_net_name
    cap_finder = data.cap_finder
    cap_layer_top = data.cap_layer_top if data.cap_layer_top else None
    reduce_num_top = int(data.reduce_num_top) if data.reduce_num_top else None
    cap_layer_bot = data.cap_layer_bot if data.cap_layer_bot else None
    reduce_num_bot = int(data.reduce_num_bot) if data.reduce_num_bot else None
    socket_mode = data.socket_mode if data.socket_mode else None
    ref_z = float(data.ref_z) if data.ref_z else None
    boxes_fname = data.boxes_fname if data.boxes_fname else None
    sinks_layer = data.sinks_layer if data.sinks_layer else None
    sinks_num_ports = data.sinks_num_ports if data.sinks_num_ports else None
    sinks_area = data.sinks_area if data.sinks_area else None
    from_db_side = data.from_db_side if data.from_db_side else None
    skt_num_ports = int(data.skt_num_ports) if data.skt_num_ports else None
    brd_fname = data.brd_fname if data.brd_fname else None

    package_response = ports.setup_pkg_ports(
        filename, sinks_mode, pwr_net_name, cap_finder, cap_layer_top, reduce_num_top,
        cap_layer_bot, reduce_num_bot, socket_mode, ref_z, sinks_layer, sinks_num_ports,
        sinks_area, from_db_side, skt_num_ports, brd_fname)

    return JSONResponse(content=package_response)


@app.post("/auto-copy")
def auto_copy(data: AutoCopyData):
    src_db = data.src_db
    dst_db = data.dst_db
    force = data.force
    print(data)
    #response = ports.auto_copy(spd_path+src_db, spd_path+dst_db, force)
    response = None

    return JSONResponse(content=response)

@app.post("/copy-port")
def copy(data: CopyData):
    src_db = data.src_db
    dst_db = data.dst_db
    force = data.force
    x_src = float(data.x_src) if data.x_src else None
    y_src = float(data.y_src) if data.y_src else None
    x_dst = float(data.x_dst) if data.x_dst else None
    y_dst = float(data.y_dst) if data.y_dst else None
    ref_z = float(data.ref_z) if data.ref_z else None
    #response = ports.copy(x_src, y_src, x_dst, y_dst, spd_path+src_db, spd_path+dst_db, ref_z, force)
    response = None

    return JSONResponse(content=response)

@app.post("/array-copy")
def array_copy(data: ArrayCopyData):
    src_db = data.src_db
    dst_db = data.dst_db
    force = data.force
    x_src = float(data.x_src) if data.x_src else None
    y_src = float(data.y_src) if data.y_src else None
    x_horz = float(data.x_horz) if data.x_horz else None
    y_vert = float(data.y_vert) if data.y_vert else None
    nx = float(data.nx) if data.nx else None
    ny = float(data.ny) if data.ny else None
    ref_z = float(data.ref_z) if data.ref_z else None
    #response = ports.array_copy(spd_path+src_db, x_src, y_src, x_horz, y_vert, nx, ny, spd_path+dst_db, ref_z, force)
    response = None
    return JSONResponse(content=response)

@app.post("/mirror-copy")
def mirror_copy(data: MirrorCopyData):
    src_db = data.src_db
    dst_db = data.dst_db
    force = data.force
    x_src = float(data.x_src) if data.x_src else None
    y_src = float(data.y_src) if data.y_src else None
    x_dst = float(data.x_dst) if data.x_dst else None
    y_dst = float(data.y_dst) if data.y_dst else None
    ref_z = float(data.ref_z) if data.ref_z else None
    #response = ports.mirror_copy(spd_path+src_db, x_src, y_src, x_dst, y_dst, spd_path+dst_db, ref_z, force)
    response = None

    return JSONResponse(content=response)

@app.post("/rotate-copy")
def rotate_copy(data: RotateCopyData):
    src_db = data.src_db
    dst_db = data.dst_db
    force = data.force
    x_src = float(data.x_src) if data.x_src else None
    y_src = float(data.y_src) if data.y_src else None
    x_dst = float(data.x_dst) if data.x_dst else None
    y_dst = float(data.y_dst) if data.y_dst else None
    rot_angle = float(data.rot_angle) if data.rot_angle else None
    ref_z = float(data.ref_z) if data.ref_z else None
    #response = ports.rotate_copy(spd_path + src_db, x_src, y_src, x_dst, y_dst, rot_angle, spd_path+dst_db, ref_z, force)
    response = None
    return JSONResponse(content=response)

@app.post("/report")
def report(data: ReportData):
    report_fname = data.layout_fname.replace(Path(data.layout_fname).suffix, '_report.txt')
    
    response = processed_Dbapi_object[data.layout_fname].report(
                                                            data.nets,
                                                            report_fname,
                                                            data.cap_finder
    )

    return JSONResponse(content=response)

@app.post("/auto-vrm-ports")
def auto_vrm_ports(data: AutoVrmPortsData):
    src_db = data.db
    power_nets = data.power_nets
    layer = data.layer
    to_fname = data.to_fname
    ind_finder = data.ind_finder
    ref_z = float(data.ref_z) if data.ref_z else None

    #response = ports.auto_vrm_ports(spd_path+src_db, power_nets, layer, to_fname, ind_finder, ref_z)
    response = None

    return JSONResponse(content=response)

@app.post("/transfer-socket-ports")
def transfer_socket_ports(data: TransferSocketPortsData):
    from_db = data.from_db
    to_db = data.to_db
    from_db_side = data.from_db_side
    to_db_side = data.to_db_side
    suffix = data.suffix

    #response = ports.transfer_socket_ports(spd_path+from_db, spd_path+to_db, from_db_side, to_db_side, suffix)
    response = None

    return JSONResponse(content=response)

@app.post("/auto-socket-ports")
def auto_socket_ports(data: AutoSocketPortsData):
    db = data.spd_filename
    #ports = api.PortHandler(all_queues[db])
    num_ports = data.num_ports
    side = data.side
    ref_z = float(data.ref_z) if data.ref_z else None

    response = ports.auto_socket_ports(api.loaded_layouts[db].db, num_ports, side, ref_z)
    return JSONResponse(content=response)

@app.post("/get-port-info")
def get_port_info(data: GetPortInfoData):
    data.csv_fname = prepend_path(data.layout_fname, data.csv_fname)
    response = sd.ports.get_port_info(data.layout_fname, data.csv_fname)

    return JSONResponse(content=response)

@app.post("/modify-port-info")
def modify_port_info(data: ModifyPortInfo):
    data.csv_fname = prepend_path(data.layout_fname, data.csv_fname)
    response = sd.ports.modify_port_info(data.layout_fname, data.csv_fname,
                                        data.port_info)

@app.post("/get-sink-info")
def get_sink_info(data: SinksVrmsLdosInfo):
    data.csv_fname = prepend_path(data.layout_fname, data.csv_fname)
    response = sd.ports.get_sinks_vrms_ldos_info(data.layout_fname, 'sink', data.csv_fname)
    
    return JSONResponse(content=response)

@app.post("/get-vrm-info")
def get_vrm_info(data: SinksVrmsLdosInfo):
    data.csv_fname = prepend_path(data.layout_fname, data.csv_fname)
    response = sd.ports.get_sinks_vrms_ldos_info(data.layout_fname, 'vrm', data.csv_fname)
    
    return JSONResponse(content=response)

@app.post("/get-ldo-info")
def get_ldo_info(data: SinksVrmsLdosInfo):
    data.csv_fname = prepend_path(data.layout_fname, data.csv_fname)
    response = sd.ports.get_sinks_vrms_ldos_info(data.layout_fname, 'ldo', data.csv_fname)
    
    return JSONResponse(content=response)

@app.post("/modify-sink-info")
def modify_sink_info(data: ModifySinkInfo):
    data.csv_fname = prepend_path(data.layout_fname, data.csv_fname)
    response = sd.ports.modify_sink_info(data.layout_fname, data.csv_fname,
                                        data.sink_info)

@app.post("/modify-vrm-info")
def modify_vrm_info(data: ModifyVrmInfo):
    data.csv_fname = prepend_path(data.layout_fname, data.csv_fname)
    response = sd.ports.modify_vrm_info(data.layout_fname, data.csv_fname,
                                        data.vrm_info)

@app.post("/auto-ports")
def auto_ports(data: AutoPortsInfo):
    fname = data.fname
    power_nets = data.power_nets
    layer = data.layer
    num_ports = data.num_ports
    area = data.area
    ref_z = float(data.ref_z) if data.ref_z else None
    port3D = data.port3D
    prefix = data.prefix

    #response = ports.auto_ports(
    #    spd_path+fname, power_nets, layer, num_ports,
    #    area, ref_z, port3D, prefix)
    response = None
    return JSONResponse(content=response)

@app.post("/boxes-to-ports")
def boxes_to_ports(data: BoxesToPortsInfo):
    fname = data.fname
    ref_z = data.ref_z
    port3D = data.port3D
    response = ''
    return JSONResponse(content=response)

@app.post("/reduce-ports")
def reduce_ports(data: ReducePortsInfo):
    fname = data.fname
    layer = data.layer
    num_ports = data.num_ports
    select_ports = data.select_ports
    response = ''
    return JSONResponse(content=response)

@app.post("/sinks_vrms_to_ports")
def sinks_vrms_to_ports(data: SinksVrmsToPortsInfo):
    fname = data.fname
    stimuli = data.stimuli
    to_fname = data.to_fname
    ref_z = float(data.ref_z) if data.ref_z else None
    sink_suffix = data.sink_suffix
    vrm_suffix = data.vrm_suffix
    #response = ports.sinks_vrms_to_ports(
    #    spd_path+fname, stimuli, to_fname, ref_z, sink_suffix, vrm_suffix)
    response = None
    print("response", response)
    return JSONResponse(content=response)

@app.get("/get-server-info")
def get_server_info():
    lib_mgr = lib.LibManager()
    return JSONResponse(content=lib_mgr.get_resource_info())

@app.get("/get-ip-list")
def get_ip_list():
    lib_mgr = lib.LibManager()
    return JSONResponse(content=lib_mgr.get_server_list()['ip_address'])

@app.post("/servers-info")
async def root(servers: ServerInfo):
    lib_mgr = lib.LibManager()
    return JSONResponse(content=lib_mgr.score_servers(servers.info))


if __name__ == "__main__": uvicorn.run(app, host="0.0.0.0", port=8000)
