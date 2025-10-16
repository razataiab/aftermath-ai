from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from fastapi.responses import JSONResponse
import requests
from urllib.parse import parse_qs
from config import settings

verifier = SignatureVerifier(settings.SLACK_SIGNING_SECRET)
router = APIRouter()
client = WebClient(token=settings.SLACK_TOKEN)

def verify_slack_signature(request: Request, body: bytes):
    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    signature = request.headers.get("X-Slack-Signature")

    print(f"Verifying signature:")
    
    verified = verifier.is_valid(body, timestamp, signature)
    if not verified:
        print("Signature verification failed!")
    
    print("Signature verified successfully!")

@router.post("/slash")
async def handle_slash_command(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()

    verify_slack_signature(request, body) 

    body_str = body.decode('utf-8')
    parsed = parse_qs(body_str)
    form = {k: v[0] if v else '' for k, v in parsed.items()}

    channel_id = form.get("channel_id", "unknown")

    background_tasks.add_task(run_postmortem_generation, channel_id)
    return JSONResponse(content={"text": "⏳ Generating postmortem report... I'll post it here soon."}, status_code=200)

async def run_postmortem_generation(channel_id: str):
    print(f"Running postmortem generation for channel={channel_id}")
    await retrieve_slack_chat_history(channel_id)
    await send_postmortem_report(channel_id)
    print("Postmortem generation complete!")

async def send_postmortem_report(channel_id: str):
    message = client.chat_postMessage(channel=channel_id, text="Postmortem generation complete")

async def retrieve_slack_chat_history(channel_id: str):
    conversation_history = []
    response = client.conversations_history(channel=channel_id)

    conversation_history = response["messages"]

    for msg in conversation_history:
        user = msg.get("user")
        username = await retrieve_slack_user_name(user)
        text = msg.get("text")
        print(f"{username}: {text}")
    
    return conversation_history

async def retrieve_slack_user_name(userId: str):
    response = client.users_info(user=userId)
    user_info = response["user"]
    return user_info.get("real_name")