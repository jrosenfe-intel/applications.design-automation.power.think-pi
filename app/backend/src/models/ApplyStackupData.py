from pydantic import BaseModel

class ApplyStackupData(BaseModel):
  spd_fname: str
  stackup_fname: str
  material_fname: str | None = None

