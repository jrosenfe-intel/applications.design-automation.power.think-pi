from pydantic import BaseModel

class ReportData(BaseModel):
  layout_fname: str
  cap_finder: str
  nets: list
