import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum
from sqlalchemy.sql import text  # re-exported for use in main.py

from .database import Base


class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Status(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(SAEnum(Priority), default=Priority.medium, nullable=False)
    status = Column(SAEnum(Status), default=Status.todo, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
