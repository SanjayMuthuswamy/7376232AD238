from fastapi import FastAPI

from app.routes.user_routes import router as user_router

app = FastAPI(title="FastAPI Project")


@app.get("/")
def home() -> dict[str, str]:
    return {"message": "FastAPI project is running"}


app.include_router(user_router, prefix="/users", tags=["users"])
