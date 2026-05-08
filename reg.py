import requests

url = "http://4.224.186.213/evaluation-service/auth"

payload = {
    "email": "sanjaym.ad23@bitsathy.ac.in",
    "name": "Sanjay M",
    "rollNo": "7376232AD238",
    "accessCode": "uKaJfm",
    "clientID": "840f29f7-a277-4353-a169-c62e53af0aef",
    "clientSecret": "VkFbPxbgmzEFJSGV"
}

res = requests.post(url, json=payload)

print(res.status_code)
print(res.json())
