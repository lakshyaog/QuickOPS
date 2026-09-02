"""
Test suite for the DevBoard FastAPI application.

All tests use the in-memory SQLite client provided by conftest.py.
No running PostgreSQL or Docker container is required.

NOTE: test_broken_intentional is deliberately failing to demonstrate
      CI breakage — it will be fixed in the follow-up commit.
"""

# ── Health ─────────────────────────────────────────────────────────────────────

def test_health_check(client):
    """GET /health should return 200 with status=ok (DB key may be error on SQLite)."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "api" in data
    assert "timestamp" in data


# ── Create task ────────────────────────────────────────────────────────────────

def test_create_task_returns_201(client):
    """POST /tasks with valid payload should create a task and return 201."""
    payload = {"title": "Write CI pipeline", "priority": "high", "status": "todo"}
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] >= 1
    assert data["title"] == "Write CI pipeline"
    assert data["priority"] == "high"
    assert data["status"] == "todo"


def test_create_task_missing_title_returns_422(client):
    """POST /tasks without a title should be rejected with 422 Unprocessable Entity."""
    response = client.post("/tasks", json={"priority": "low"})
    assert response.status_code == 422


# ── List tasks ─────────────────────────────────────────────────────────────────

def test_list_tasks_empty(client):
    """GET /tasks on a fresh DB should return an empty list."""
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_after_create(client):
    """GET /tasks should include tasks that were just created."""
    client.post("/tasks", json={"title": "Task Alpha", "priority": "medium", "status": "todo"})
    client.post("/tasks", json={"title": "Task Beta", "priority": "low", "status": "in_progress"})
    response = client.get("/tasks")
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert "Task Alpha" in titles
    assert "Task Beta" in titles


# ── Get single task ────────────────────────────────────────────────────────────

def test_get_task_by_id(client):
    """GET /tasks/{id} should return the correct task."""
    create_resp = client.post(
        "/tasks", json={"title": "Specific Task", "priority": "high", "status": "todo"}
    )
    task_id = create_resp.json()["id"]
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Specific Task"


def test_get_task_not_found(client):
    """GET /tasks/99999 should return 404 when the task does not exist."""
    response = client.get("/tasks/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


# ── Update task ────────────────────────────────────────────────────────────────

def test_update_task(client):
    """PUT /tasks/{id} should update only the provided fields."""
    create_resp = client.post(
        "/tasks", json={"title": "Old Title", "priority": "low", "status": "todo"}
    )
    task_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/tasks/{task_id}",
        json={"title": "New Title", "status": "done"},
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["title"] == "New Title"
    assert data["status"] == "done"
    assert data["priority"] == "low"  # untouched


def test_update_task_not_found(client):
    """PUT /tasks/99999 should return 404 when the task does not exist."""
    response = client.put("/tasks/99999", json={"title": "Ghost"})
    assert response.status_code == 404


# ── Delete task ────────────────────────────────────────────────────────────────

def test_delete_task(client):
    """DELETE /tasks/{id} should return 204 and the task should no longer exist."""
    create_resp = client.post(
        "/tasks", json={"title": "Doomed Task", "priority": "medium", "status": "todo"}
    )
    task_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/tasks/{task_id}")
    assert delete_resp.status_code == 204

    # Confirm it's gone
    get_resp = client.get(f"/tasks/{task_id}")
    assert get_resp.status_code == 404


def test_delete_task_not_found(client):
    """DELETE /tasks/99999 should return 404 when the task does not exist."""
    response = client.delete("/tasks/99999")
    assert response.status_code == 404


# ── CI verification demo test ──────────────────────────────────────────────────

def test_broken_intentional():
    """
    Fixed CI demo test — now passes cleanly!
    """
    assert True
