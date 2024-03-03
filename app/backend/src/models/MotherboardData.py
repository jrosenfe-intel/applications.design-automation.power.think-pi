from pydantic import BaseModel

class MotherboardData(BaseModel):
  spd_filename:str
  ports_fname: str
  pwr_net_name: list
  cap_finder: str
  cap_layer_top: str
  reduce_num_top: int
  cap_layer_bot: str
  reduce_num_bot: int
  vrm_layer: str
  socket_mode: str
  from_db_side: str
  skt_num_ports: int
  pkg_fname: str
  ref_z: float
