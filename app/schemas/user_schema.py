from pydantic import BaseModel, field_validator

from app.utils.text import normalize_email


class UserCreate(BaseModel):
    name: str
    email: str

    @field_validator("name")
    @classmethod
    def check_name(cls, value):
        name = value.strip()
        if name == "":
            raise ValueError("Name is required")

        return name

    @field_validator("email")
    @classmethod
    def check_email(cls, value):
        email = normalize_email(value)
        domain = email.split("@")[-1]
        if "@" not in email or "." not in domain:
            raise ValueError("A valid email is required")

        return email


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
