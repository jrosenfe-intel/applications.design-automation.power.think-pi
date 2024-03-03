from pydantic import BaseModel

class MaterialData(BaseModel):
  layout_fname: str
  material_fname: str