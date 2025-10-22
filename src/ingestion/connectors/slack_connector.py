from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from fastapi import Request
from src.app.core.config import settings

client = WebClient(token=settings.SLACK_TOKEN)
verifier = SignatureVerifier(settings.SLACK_SIGNING_SECRET)

def verify_slack_signature(request: Request, body: bytes):
    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    signature = request.headers.get("X-Slack-Signature")
    verified = verifier.is_valid(body, timestamp, signature)
    if not verified:
        print("Signature verification failed: Invalid signature")

async def retrieve_slack_chat_history(channel_id: str):
    response = client.conversations_history(channel=channel_id)
    return response["messages"]

async def retrieve_slack_user_name(user_id: str):
    response = client.users_info(user=user_id)
    return response["user"].get("real_name")

async def send_slack_message(channel_id: str, message: str):
    client.chat_postMessage(channel=channel_id, text=message)

# async def get_channel_id(body: bytes):
#     payload = slack_parser.parse_slash_payload(body)
#     return payload.get("channel_id")

# async def get_user_id(body: bytes):
#     payload = slack_parser.parse_slash_payload(body)
#     return payload.get("user_id")

# async def get_channel_name(body: bytes):
#     payload = slack_parser.parse_slash_payload(body)
#     return payload.get("channel_name")