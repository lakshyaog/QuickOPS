from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from .models import Priority, Status


# ── Request schemas ─────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, example="Fix login bug")
    description: Optional[str] = Field(None, example="Users can't log in on Safari")
    priority: Priority = Field(Priority.medium, example="high")
    status: Status = Field(Status.todo, example="todo")


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None


# ── Response schemas ─────────────────────────────────────────────────────────

class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: Priority
    status: Status
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
