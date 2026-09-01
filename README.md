# DevBoard — Developer Task Management API

> **Day 1 — Application + Docker**  
> FastAPI · PostgreSQL · Docker · Docker Compose

---

## Project Structure

```
QuickOPS/
├── docker-compose.yml          ← Compose orchestration
├── .env.example                ← Environment variable template
└── backend/
    ├── Dockerfile              ← Backend container image
    ├── requirements.txt        ← Python dependencies
    └── app/
        ├── main.py             ← FastAPI routes + app factory
        ├── database.py         ← SQLAlchemy engine / session
        ├── models.py           ← ORM models (Task)
        ├── schemas.py          ← Pydantic request/response schemas
        └── crud.py             ← Database helper functions
```

---

## Quick Start

```bash
# 1 — Clone and enter the project
cd QuickOPS

# 2 — Bring everything up
docker compose up -d

# 3 — Verify containers are running
docker ps

# 4 — Check health
curl http://localhost:8000/health
```

---

## API Reference

| Method   | Endpoint         | Description            |
|----------|-----------------|------------------------|
| `GET`    | `/health`        | Health + DB status     |
| `POST`   | `/tasks`         | Create a task          |
| `GET`    | `/tasks`         | List all tasks         |
| `GET`    | `/tasks/{id}`    | Get a single task      |
| `PUT`    | `/tasks/{id}`    | Update a task          |
| `DELETE` | `/tasks/{id}`    | Delete a task          |

Interactive docs available at **http://localhost:8000/docs** (Swagger UI).

---

## Example cURL Commands

```bash
# Create a task
curl -s -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Fix login bug","priority":"high","status":"todo"}' | jq

# List all tasks
curl -s http://localhost:8000/tasks | jq

# Update a task (change status to in_progress)
curl -s -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status":"in_progress"}' | jq

# Delete a task
curl -s -X DELETE http://localhost:8000/tasks/1
```

---

## Docker Concepts Covered

| Concept               | Where used                                   |
|-----------------------|----------------------------------------------|
| **Image vs container**| `postgres:16-alpine` image → `devboard_db` container |
| **Dockerfile**        | `backend/Dockerfile` — builds the API image  |
| **Volumes**           | `postgres_data` — persists DB across restarts; bind-mount for live-reload |
| **Networks**          | `devboard_net` — isolated bridge network     |
| **Environment vars**  | `DATABASE_URL`, `POSTGRES_*` in Compose      |
| **Docker Compose**    | `docker-compose.yml` — orchestrates both services |
| **Health check**      | `pg_isready` on db; backend waits for it     |

---

## Useful Commands

```bash
# View logs
docker compose logs -f

# Stop containers (keep volumes)
docker compose down

# Stop and remove volumes (fresh DB)
docker compose down -v

# Rebuild backend after code changes
docker compose up -d --build backend

# Open a psql shell in the DB container
docker exec -it devboard_db psql -U devboard -d devboard
```
