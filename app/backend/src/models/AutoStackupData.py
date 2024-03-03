from pydantic import BaseModel

class AutoStackupData(BaseModel):
  filename: str = None
  unit: str = None
  spd_filename: str = None
  dielec_thickness: str = None
  metal_thickness: str = None
  core_thickness: str = None
  conduct: str = None
  er: str = None
  loss_tangent: str = None
  dielec_material: str = None
  metal_material: str = None
  core_material: str = None
  fillin_dielec_material: str = None
