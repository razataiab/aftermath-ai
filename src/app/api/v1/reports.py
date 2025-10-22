from datetime import datetime
from typing import List, Optional
import asyncio
import uuid

from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse

from src.app.core.models import Incident, Message
from src.ingestion.parsers import slack_parser
from src.ingestion.connectors.slack_connector import (
    verify_slack_signature, 
    send_slack_message, 
    retrieve_slack_chat_history, 
    retrieve_slack_user_name
)
from src.llm.pipeline import PostmortemAgent

router = APIRouter()

async def generate_and_send_postmortem(incident: Incident):
    agent = PostmortemAgent()
    postmortem = agent.run(incident)

    await send_slack_message(
        incident.channel_id, 
        f"*Postmortem for incident `{incident.incident_id}`:*\n\n{postmortem}"
    )

@router.post("/slack")
async def handle_slack_command(request: Request, background_tasks: BackgroundTasks):
    body: bytes = await request.body()

    verify_slack_signature(request, body)
    payload = slack_parser.parse_slash_payload(body)

    channel_id = payload.get("channel_id")
    user_id = payload.get("user_id")
    user_name = await retrieve_slack_user_name(user_id)
    channel_name = payload.get("channel_name")

    messages= await retrieve_slack_chat_history(channel_id)
    conversation: List[Message] = []
    for msg in messages:
        conversation.append(
            Message(
                user_id=msg["user"],
                username=await retrieve_slack_user_name(user_id) or "Unknown",
                text=msg["text"],
                timestamp=datetime.fromtimestamp(float(msg["ts"]))
            )
        )

    incident = Incident(
        incident_id=str(uuid.uuid4()),
        channel_id=channel_id,
        triggered_by_user_id=user_id,
        triggered_by_user_name=user_name,
        channel_name=channel_name,
        conversation=conversation
    )

    background_tasks.add_task(generate_and_send_postmortem, incident)

    return PlainTextResponse("Generating postmortem...", status_code=200)
