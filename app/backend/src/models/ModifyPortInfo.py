from pydantic import BaseModel

class ModifyPortInfo(BaseModel):
  layout_fname: str
  csv_fname: str
  port_info: dict
