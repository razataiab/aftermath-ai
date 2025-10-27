import os
import time
import requests
from fastapi import Request
from src.app.core.config import settings

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")
DISCORD_PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY", "")

BASE = "https://discord.com/api/v10"

def verify_discord_signature(request: Request, body: bytes):
    """
    Discord interaction signature verification.
    In production: verify using Ed25519 (X-Signature-Ed25519 & X-Signature-Timestamp).
    Here: placeholder that simply logs. Replace with nacl library verification.
    """
    ts = request.headers.get("X-Signature-Timestamp")
    sig = request.headers.get("X-Signature-Ed25519")
    if not ts or not sig:
        print("Discord signature missing - implement verification.")
    return True

async def retrieve_discord_chat_history(channel_id: str):
    """Return a list of messages from a Discord channel. Requires bot token & channel permissions."""
    url = f"{BASE}/channels/{channel_id}/messages?limit=200"
    headers = {"Authorization": f"Bot {DISCORD_TOKEN}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

async def retrieve_discord_user_name(user_id: str):
    url = f"{BASE}/users/{user_id}"
    headers = {"Authorization": f"Bot {DISCORD_TOKEN}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return "Unknown"
    data = resp.json()
    return data.get("username")

async def send_discord_message(channel_id: str, message: str):
    url = f"{BASE}/channels/{channel_id}/messages"
    headers = {"Authorization": f"Bot {DISCORD_TOKEN}", "Content-Type": "application/json"}
    payload = {"content": message}
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()
