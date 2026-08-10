import requests
import json
import os

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")

url = "https://accounts.spotify.com/api/token"
headers = {"Content-Type": "application/x-www-form-urlencoded"}
data = {"grant_type": "client_credentials"}
auth = (CLIENT_ID, CLIENT_SECRET)

response = requests.post(url, headers=headers, data=data, auth=auth)
result = response.json()

if response.status_code == 200:
    print("Success!")
    print(f"Token: {result['access_token'][:50]}...")
else:
    print("Failed!")
    print(json.dumps(result, indent=2))