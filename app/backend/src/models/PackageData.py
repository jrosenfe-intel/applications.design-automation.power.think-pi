from pydantic import BaseModel

class PackageData(BaseModel):
  spd_filename:str
  sinks_mode: str
  ports_fname: str
  pwr_net_name: list
  cap_finder: str
  cap_layer_top: str
  reduce_num_top: int
  cap_layer_bot: str
  reduce_num_bot: int
  socket_mode: str
  ref_z: float
  boxes_fname: str
  sinks_layer: str
  sinks_num_ports: str
  sinks_area: str
  from_db_side: str
  skt_num_ports: str
  brd_fname: str


