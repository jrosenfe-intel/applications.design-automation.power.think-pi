from pydantic import BaseModel

class GetPortInfoData(BaseModel):
  layout_fname: str
  csv_fname: str | None = None
