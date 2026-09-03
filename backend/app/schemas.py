from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from .models import Priority, Status


# ── Request schemas ─────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, examples=["Fix login bug"])
    description: Optional[str] = Field(None, examples=["Users can't log in on Safari"])
    priority: Priority = Field(Priority.medium, examples=["high"])
    status: Status = Field(Status.todo, examples=["todo"])


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None


# ── Response schemas ─────────────────────────────────────────────────────────

class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    priority: Priority
    status: Status
    created_at: datetime
    updated_at: datetime

