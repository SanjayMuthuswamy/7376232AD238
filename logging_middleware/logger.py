import os

import requests


LOG_API = "http://4.224.186.213/evaluation-service/logs"


def Log(stack, level, package, message):
    token = os.getenv("AUTH_TOKEN")
    if not token:
        return {"message": "auth token missing"}

    body = {
        "stack": stack,
        "level": level,
        "package": package,
        "message": message,
    }

    try:
        response = requests.post(
            LOG_API,
            json=body,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return response.json()
    except Exception:
        # logging should not break the actual API response
        return {"message": "log failed"}
