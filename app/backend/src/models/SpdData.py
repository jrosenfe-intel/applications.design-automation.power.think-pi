from pydantic import BaseModel

class SpdData(BaseModel):
  session_id: str
  layout_fname: str