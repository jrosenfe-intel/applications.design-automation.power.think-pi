from pydantic import BaseModel

class DeleteProject(BaseModel):
  path: str