from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    repository_url: str | None = None
    branch: str = Field(default="main", min_length=1, max_length=100)


class ProjectRead(BaseModel):
    id: int
    name: str
    description: str | None
    repository_url: str | None
    branch: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)