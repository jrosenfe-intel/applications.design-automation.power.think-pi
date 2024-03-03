from pydantic import BaseModel

class TransferSocketPortsData(BaseModel):
  from_db: str
  to_db: str
  from_db_side: str
  to_db_side: str
  suffix: str