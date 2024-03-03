from pydantic import BaseModel

class ModifySinkInfo(BaseModel):
  layout_fname: str
  csv_fname: str
  sink_info: dict
