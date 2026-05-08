import os


def get_bool(key, default=False):
    value = os.getenv(key)
    if value is None:
        return default

    return value.strip().lower() in ["1", "true", "yes", "on"]


PROJECT_NAME = os.getenv("APP_NAME", "Affordmed API")
DEBUG = get_bool("APP_DEBUG")
