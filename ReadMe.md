# Face Encoding Service

A backend service to manage face encoding sessions, image uploads, and data aggregation.

This project implements the Veriff home task flow:
- create a session
- upload up to 5 images to that session
- call the Face Encoding service for each uploaded image
- persist the returned face vectors
- expose a session summary with all collected encodings

## Tech Stack
- **FastAPI**
- **SQLAlchemy (Async)**
- **PostgreSQL**
- **Alembic**
- **Docker**
---

## 🚀 Quick Start (Docker)

The easiest way to run it, is with Docker Compose. The compose file starts:
- PostgreSQL
- the Veriff Face Encoding service (external)
- this API service

1. **Configure Environment**:
   ```bash
   cp .env-example .env
   ```
2. **Launch the stack**:
   ```bash
   docker compose up --build
   ```

The API startup script applies Alembic migrations automatically before starting the app.

Available docs:
- Face Encoding service: [http://localhost:8000/docs](http://localhost:8000/docs)
- API service: [http://localhost:8080/docs](http://localhost:8080/docs)

If you already had an older Postgres volume before the dedicated test database was added, create it once with:
```bash
docker compose exec db psql -U postgres -d postgres -c "CREATE DATABASE veriff_test;"
```

Database check commands:
```sh
docker exec -it veriff-db psql -U postgres -d veriff
\dt
select * from sessions;
select * from images;
select image_id, jsonb_array_length(vector) from face_encodings;
```

---

## 🛠 Manual Setup (Development)

1. **Virtual Env**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Database**:
   ```bash
   docker compose up -d db
   alembic upgrade head
   ```
3. **Run external Face Encoding service**:
   ```bash
   docker compose up -d face-encoding
   ```
4. **Run App**:
   ```bash
   uvicorn src.main:app --reload --port 8080
   ```

---

## 🧪 Testing

The project uses `pytest` with a dedicated test database (`veriff_test`).

Start the database first:

```bash
docker compose up -d db
```

```bash
.venv/bin/pytest -q
```

---

## 📡 API Endpoints

### Sessions
- `POST /v1/sessions/`: Initialize a new encoding session.

### Images
- `POST /v1/sessions/{id}/images`: Upload an image (Max 5 per session).
  - Automatically detects faces and generates 128-dim vectors via the external Encoding Service.

### Summary
- `GET /v1/sessions/{id}/summary`: Get a flat list of all face encodings generated in the session.

## External Face Encoding API

The task provides a separate Face Encoding service maintained by Veriff.

- Docker image: [veriffdocker/face-encoding-test-task](https://hub.docker.com/r/veriffdocker/face-encoding-test-task/tags)
- local docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- verified endpoint used by this project: `POST /v1/selfie`

The API accepts one uploaded image file and returns a list of 128-dimensional face encodings, one vector per detected face.

## Notes

- The Veriff Face Encoding service contract was verified against `POST /v1/selfie`.
- Uploaded image binaries are processed in memory and only metadata plus face encodings are persisted.
- Encodings are stored as JSONB arrays in PostgreSQL.

