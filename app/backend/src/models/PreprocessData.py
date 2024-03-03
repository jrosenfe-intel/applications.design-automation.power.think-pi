from pydantic import BaseModel

class PreprocessData(BaseModel):
  layout_fname: str
  power_nets: str | list[str]
  ground_nets: str
  stackup_fname: str | None = None
  padstack_fname: str | None = None
  material_fname: str | None = None
  default_conduct: float | None = None
  cut_margin: float = 0
  post_processed_fname: str | None = None
  delete_unused_nets: bool = False
