from pydantic import BaseModel

class SaveMaterialData(BaseModel):
  filename: str
  material_data: dict
