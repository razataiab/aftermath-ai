import os
import requests
from fastapi import Request
from src.app.core.config import settings

TEAMS_CLIENT_ID = os.environ.get("TEAMS_CLIENT_ID")
TEAMS_CLIENT_SECRET = os.environ.get("TEAMS_CLIENT_SECRET")
TEAMS_TENANT_ID = os.environ.get("TEAMS_TENANT_ID")
GRAPH_BASE = "https://graph.microsoft.com/v1.0"

def verify_teams_request(request: Request, body: bytes):
    return True

async def retrieve_teams_chat_history(channel_id: str):
    token = os.environ.get("TEAMS_GRAPH_TOKEN")
    if not token:
        raise RuntimeError("TEAMS_GRAPH_TOKEN is not set - implement auth using MSAL.")
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{GRAPH_BASE}/teams/{channel_id}/channels/{channel_id}/messages"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json().get("value", [])

async def retrieve_teams_user_name(user_id: str):
    token = os.environ.get("TEAMS_GRAPH_TOKEN")
    if not token:
        return "Unknown"
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{GRAPH_BASE}/users/{user_id}"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return "Unknown"
    return resp.json().get("displayName")

async def send_teams_message(channel_id: str, message: str):
    token = os.environ.get("TEAMS_GRAPH_TOKEN")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{GRAPH_BASE}/teams/{channel_id}/channels/{channel_id}/messages"
    payload = {"body": {"content": message}}
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()
