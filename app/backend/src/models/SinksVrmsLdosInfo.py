from pydantic import BaseModel

class SinksVrmsLdosInfo(BaseModel):
  layout_fname: str
  csv_fname: str | None
