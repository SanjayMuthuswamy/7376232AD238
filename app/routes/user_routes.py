from fastapi import APIRouter

from app.schemas.user_schema import UserResponse
from app.services.user_service import get_users

router = APIRouter()


@router.get("/", response_model=list[UserResponse])
def list_users() -> list[UserResponse]:
    return get_users()
