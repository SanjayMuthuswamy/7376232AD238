# Notification Backend

Small FastAPI backend project for the backend track submission. It has a simple user API, a notification API, and a reusable logging middleware function.

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
- `GET /notifications` - list notifications
- `GET /notifications/{notification_id}` - get one notification
- `POST /notifications` - create a notification
- `GET /vehicle-scheduling` - fetch depot and vehicle data, then calculate the best maintenance schedule

Right now users and notifications are stored in memory, so data resets when the server restarts.

## Backend track files

- `logging_middleware/`
- `vehicle_maintenance_scheduler/`
- `notification_system_design.md`
- `notification_app_be/`

## Output

![Output Screenshot](./output/Screenshot%202026-05-08%20153053.png)
