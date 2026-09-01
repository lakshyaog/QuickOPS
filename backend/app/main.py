# ── stdlib ────────────────────────────────────────────────────────────────────
import time
from typing import List

# ── third-party ───────────────────────────────────────────────────────────────
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

# ── local ─────────────────────────────────────────────────────────────────────
from .database import Base, engine, get_db
from . import crud, models, schemas

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DevBoard — Developer Task Management API",
    description="A simple task management API for developers, backed by PostgreSQL.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
def root():
    """Redirect root to the interactive API docs."""
    return RedirectResponse(url="/docs")


# ─────────────────────────────────────────────
#  Health
# ─────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Check that the API and the database are both reachable."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:
        db_status = f"error: {exc}"

    return {
        "status": "ok",
        "api": "DevBoard v1.0.0",
        "database": db_status,
        "timestamp": time.time(),
    }


# ─────────────────────────────────────────────
#  Tasks
# ─────────────────────────────────────────────

@app.post("/tasks", response_model=schemas.TaskOut, status_code=201, tags=["Tasks"])
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    return crud.create_task(db, task)


@app.get("/tasks", response_model=List[schemas.TaskOut], tags=["Tasks"])
def list_tasks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Return all tasks (supports pagination via skip/limit)."""
    return crud.get_tasks(db, skip=skip, limit=limit)


@app.get("/tasks/{task_id}", response_model=schemas.TaskOut, tags=["Tasks"])
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Return a single task by ID."""
    task = crud.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/tasks/{task_id}", response_model=schemas.TaskOut, tags=["Tasks"])
def update_task(
    task_id: int, task_update: schemas.TaskUpdate, db: Session = Depends(get_db)
):
    """Update an existing task by ID."""
    task = crud.update_task(db, task_id, task_update)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/tasks/{task_id}", status_code=204, tags=["Tasks"])
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task by ID."""
    deleted = crud.delete_task(db, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
