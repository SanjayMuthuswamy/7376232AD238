import os

import requests

from logging_middleware import Log


BASE_URL = "http://4.224.186.213/evaluation-service"


def _headers():
    token = os.getenv("AUTH_TOKEN")
    if not token:
        raise ValueError("AUTH_TOKEN is missing")

    return {"Authorization": f"Bearer {token}"}


def fetch_depots():
    Log("backend", "info", "service", "fetching depot details")
    response = requests.get(f"{BASE_URL}/depots", headers=_headers(), timeout=10)
    response.raise_for_status()
    data = response.json()
    return data.get("depots", [])


def fetch_vehicles():
    Log("backend", "info", "service", "fetching vehicle maintenance tasks")
    response = requests.get(f"{BASE_URL}/vehicles", headers=_headers(), timeout=10)
    response.raise_for_status()
    data = response.json()
    return data.get("vehicles", [])
