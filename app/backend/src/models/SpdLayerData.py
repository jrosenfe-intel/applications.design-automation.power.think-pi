from pydantic import BaseModel

class SpdLayerData(BaseModel):
  filename: str
  layer: str