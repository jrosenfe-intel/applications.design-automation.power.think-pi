from pydantic import BaseModel

class SinksVrmsToPortsInfo(BaseModel):
  fname: str
  stimuli: str
  to_fname: str
  ref_z: str
  sink_suffix: str
  vrm_suffix: str