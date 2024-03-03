from pydantic import BaseModel

class PadStackData(BaseModel):
  csv_fname: str | None = None
  unit: str
  layout_type: str
  spd_fname: str
  material: str | None = None
  inner_fill_material: str | None = None
  outer_thickness: float | None = None
  conduct: float | None = None
  brd_plating: float | None = None
  pkg_gnd_plating: float | None = None
  pkg_pwr_plating: float | None = None
  outer_coating_material: str | None = None
