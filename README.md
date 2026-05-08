# Affordmed API

Small FastAPI project for trying out basic user APIs.

## Run locally

```bash
pip install -r requirements.txt
python run.py
```

The app starts on `http://127.0.0.1:8000`.

## Current endpoints

- `GET /` - health check
- `GET /users` - list users
- `GET /users/{user_id}` - get one user
- `POST /users` - add a user

Right now users are stored in memory, so data resets when the server restarts.
