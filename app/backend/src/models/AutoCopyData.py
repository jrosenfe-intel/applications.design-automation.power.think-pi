from pydantic import BaseModel

class AutoCopyData(BaseModel):
  src_db: str = None
  dst_db: str = None
  force: bool = None
