from pydantic import BaseModel

class ModifyVrmInfo(BaseModel):
  layout_fname: str
  csv_fname: str
  vrm_info: dict