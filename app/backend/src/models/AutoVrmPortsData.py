from pydantic import BaseModel

class AutoVrmPortsData(BaseModel):
  db:str
  power_nets: list
  layer: str
  to_fname: str
  ind_finder: str
  ref_z: str