from pydantic import BaseModel

class BoxesToPortsInfo(BaseModel):
  fname: str
  ref_z: str
  port3D: bool