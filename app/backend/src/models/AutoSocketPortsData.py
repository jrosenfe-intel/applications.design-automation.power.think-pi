from pydantic import BaseModel

class AutoSocketPortsData(BaseModel):
  spd_filename: str
  num_ports: str
  side: str
  ref_z: str