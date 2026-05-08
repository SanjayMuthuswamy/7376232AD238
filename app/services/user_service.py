from app.models.user_model import User


def get_users() -> list[User]:
    return [
        User(id=1, name="Sanjay", email="sanjay@example.com"),
    ]
