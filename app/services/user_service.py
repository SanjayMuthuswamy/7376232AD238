from app.models.user_model import User
from app.schemas.user_schema import UserCreate

users = [
    User(id=1, name="Sanjay", email="sanjay@example.com"),
]


def get_users():
    # copy so routes don't accidentally change the list directly
    return users.copy()


def get_user_by_id(user_id: int):
    for user in users:
        if user.id == user_id:
            return user
    return None


def add_new_user(data: UserCreate):
    for old_user in users:
        if old_user.email == data.email:
            # keeping this simple for now, no auth/user table yet
            raise ValueError("Email is already registered")

    new_user = User(
        id=next_id(),
        name=data.name,
        email=data.email,
    )
    users.append(new_user)

    return new_user


# older function names kept because I used them while testing in the shell
def list_users():
    return get_users()


def find_user(user_id: int):
    return get_user_by_id(user_id)


def create_user(payload: UserCreate):
    return add_new_user(payload)


def next_id():
    if len(users) == 0:
        return 1

    return max(user.id for user in users) + 1
