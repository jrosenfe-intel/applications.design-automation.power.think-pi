from pydantic import BaseModel

class ArrayCopyData(BaseModel):
  src_db: str = None
  dst_db: str = None
  ref_z: str = None
  force: bool = None
  x_src: str = None
  y_src: str = None
  x_horz: str = None
  y_vert: str = None
  nx: str = None
  ny: str = None
