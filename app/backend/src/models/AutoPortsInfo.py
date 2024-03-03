from pydantic import BaseModel

class AutoPortsInfo(BaseModel):
  fname: str
  power_nets: dict
  layer: str
  num_ports: int
  area: dict
  ref_z: str
  port3D: bool
  prefix: str
