# Contacts API

This project is a small REST API built with FastAPI for managing contacts.
It supports creating, reading, updating, deleting, searching contacts, and listing upcoming birthdays.

## Tech Stack

- Python 3.12
- FastAPI
- SQLAlchemy (async)
- PostgreSQL
- Alembic
- Docker / Docker Compose

## Run with Docker (recommended)

1. Copy environment file:
   - `cp .env.example .env`
2. Start services:
   - `docker compose up --build`
3. Open API:
   - `http://localhost:5001/docs`

## Run locally

1. Install dependencies:
   - `poetry install`
2. Copy environment file:
   - `cp .env.example .env`
3. Run migrations:
   - `poetry run alembic upgrade head`
4. Start app:
   - `poetry run python main.py`
5. Open API:
   - `http://127.0.0.1:8003/docs`

## Health check

- Endpoint: `GET /api/healthchecker`
