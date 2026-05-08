from fastapi import FastAPI

from app.config import DEBUG, PROJECT_NAME
from app.routes.user_routes import router as users
from notification_app_be.notification_routes import router as notifications
from vehicle_maintenance_scheduler.scheduler_routes import router as vehicle_scheduler

app = FastAPI(title=PROJECT_NAME, debug=DEBUG)


@app.get("/")
def home():
    return {"message": "Notification backend is running :)"}


app.include_router(users, prefix="/users", tags=["users"])
app.include_router(notifications, prefix="/notifications", tags=["notifications"])
app.include_router(vehicle_scheduler, prefix="/vehicle-scheduling", tags=["vehicle scheduling"])
