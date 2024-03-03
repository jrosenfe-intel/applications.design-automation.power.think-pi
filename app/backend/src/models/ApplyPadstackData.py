from pydantic import BaseModel

class ApplyPadstackData(BaseModel):
  spd_fname: str
  padstack_fname: str
  material_fname: str | None = None

