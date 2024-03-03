from pydantic import BaseModel

class SaveStackupData(BaseModel):
  spd_filename: str
  csv_fname: str
  stackup_data: dict

