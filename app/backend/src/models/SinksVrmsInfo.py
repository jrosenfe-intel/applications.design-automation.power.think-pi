from pydantic import BaseModel

class SinksVrmsInfo(BaseModel):
  ports_fname: str
  csv_fname: str
