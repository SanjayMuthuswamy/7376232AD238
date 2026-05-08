# Affordmed API

Backend service for the Affordmed project.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

The API runs at:

- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/api/v1/health

## Layout

```text
app/
  api/
    v1/
      endpoints/
      router.py
  core/
    config.py
  schemas/
  main.py
tests/
```

## Environment

Copy `.env.example` to `.env` and adjust values as needed.

## Tests

```powershell
pytest
```

## Docker

```powershell
docker build -t affordmed-api .
docker run --rm -p 8000:8000 --env-file .env affordmed-api
```
