import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials from .env
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")

# API endpoints
NOTIFICATIONS_API = "http://4.224.186.213/evaluation-service/notifications"

# Headers with authorization
headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

# Fetch notifications
response = requests.get(NOTIFICATIONS_API, headers=headers)

print(f"Status Code: {response.status_code}")
print("Response:")
print(response.json())
