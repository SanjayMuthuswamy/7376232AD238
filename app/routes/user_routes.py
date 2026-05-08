from fastapi import APIRouter, HTTPException, status

from app.schemas.user_schema import UserCreate, UserResponse
from app.services.user_service import add_new_user, get_user_by_id, get_users

router = APIRouter()


@router.get("/", response_model=list[UserResponse])
def all_users():
    return get_users()


@router.get("/{user_id}", response_model=UserResponse)
def single_user(user_id: int):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def add_user(payload: UserCreate):
    try:
        return add_new_user(payload)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
