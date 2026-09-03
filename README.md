# DevBoard — Developer Task Management API

[![CI](https://github.com/<YOUR_USERNAME>/QuickOPS/actions/workflows/ci.yml/badge.svg)](https://github.com/<YOUR_USERNAME>/QuickOPS/actions/workflows/ci.yml)

> **Day 1 — Application + Docker** · **Day 2 — GitHub Actions CI** · **Day 3 — Registry + CD**  
> FastAPI · PostgreSQL · Docker · Docker Compose · pytest · flake8 · GHCR · Trivy

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

---

## Day 2 — CI Pipeline

### What runs in GitHub Actions

| Job | Tool | What it checks |
|-----|------|---------------|
| `lint` | flake8 | PEP 8 style, unused imports, undefined names |
| `test` | pytest + coverage | All API routes via in-memory SQLite (no DB needed) |
| `docker-build` | docker/build-push-action | Dockerfile builds successfully |

All three jobs run **in parallel** on every push and pull request.

### Run tests locally

```bash
cd backend

# Install dev dependencies (once)
pip3 install -r requirements-dev.txt

# Run test suite
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=term-missing

# Lint check
flake8 app/ --config=setup.cfg
```

### Project structure (Day 2 additions)

```
QuickOPS/
├── .github/
│   └── workflows/
│       └── ci.yml              ← GitHub Actions CI pipeline
└── backend/
    ├── requirements-dev.txt    ← Dev/test dependencies (not in Docker image)
    ├── setup.cfg               ← flake8 + pytest configuration
    └── tests/
        ├── __init__.py
        ├── conftest.py         ← SQLite fixtures, TestClient setup
        └── test_tasks.py       ← Full CRUD test suite (10 tests)
```

### Protecting `main` (optional)

Go to **Settings → Branches → Add branch protection rule** for `main`:
- ☑ **Require status checks to pass before merging**
  - Add: `Lint (flake8)`, `Test (pytest)`, `Build, Scan & Publish (GHCR)`
- ☑ **Require branches to be up to date before merging**

---

## Day 3 — Registry + CD

### What runs in the CD Pipeline

```
┌──────────────┐     ┌──────────────┐     ┌────────────────────────────────────────────────────────┐
│  Lint (app)  │     │  Test (DB)   │     │ Build, Scan & Publish (GHCR)                           │
│  (flake8)    │ ──► │  (pytest)    │ ──► │ 1. Buildx build                                        │
│              │     │              │     │ 2. Trivy vulnerability scan (CRITICAL/HIGH)            │
│              │     │              │     │ 3. Push to ghcr.io with SHA + SemVer tags (on main/v*) │
└──────────────┘     └──────────────┘     └────────────────────────────────────────────────────────┘
```

### Key Highlights
1. **GitHub Container Registry (GHCR)**: Images published to `ghcr.io/<owner>/quickops/backend`.
2. **Workflow Permissions**: Configured with `packages: write` and `security-events: write`.
3. **Commit SHA Image Tagging**: Every build produces an immutable `sha-<short_sha>` tag, avoiding the risks of deploying `:latest` in production.
4. **Trivy Vulnerability Scanner**: Automated container image scanning across OS packages and Python dependencies with SARIF results uploaded to the GitHub Security tab.
5. **In-Depth Documentation**: See [docs/image-tagging-strategy.md](docs/image-tagging-strategy.md) for tag specifications, rollback strategies, and deployment runbooks.

### Pull & Run from GHCR

```bash
# Pull by commit SHA (production/staging)
docker pull ghcr.io/<YOUR_USERNAME>/quickops/backend:sha-<COMMIT_SHA>

# Run image
docker run -d -p 8000:8000 ghcr.io/<YOUR_USERNAME>/quickops/backend:sha-<COMMIT_SHA>
```

