from pydantic import BaseModel

class ReducePortsInfo(BaseModel):
  fname: str
  layer: str
  num_ports: int
  select_ports: str