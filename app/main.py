from fastapi import FastAPI

from app.config import DEBUG, PROJECT_NAME
from app.routes.user_routes import router as users

app = FastAPI(title=PROJECT_NAME, debug=DEBUG)


@app.get("/")
def home():
    return {"message": "Affordmed API is running :)"}


app.include_router(users, prefix="/users", tags=["users"])
