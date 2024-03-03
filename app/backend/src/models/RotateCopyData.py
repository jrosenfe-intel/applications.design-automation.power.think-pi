from pydantic import BaseModel

class RotateCopyData(BaseModel):
  src_db: str = None
  dst_db: str = None
  ref_z: str = None
  force: bool = None
  x_src: str = None
  y_src: str = None
  x_dst: str = None
  y_dst: str = None
  rot_angle: str = None
