from pydantic import BaseModel

class NewProject(BaseModel):
  project_name: str
  study_name: str
  rail_name: str