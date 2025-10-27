from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse, JSONResponse

from src.app.core.models import Incident, Message
from src.ingestion.parsers import slack_parser, discord_parser, teams_parser
from src.ingestion.connectors.slack_connector import (
    verify_slack_signature,
    retrieve_slack_chat_history,
    retrieve_slack_user_name,
    send_slack_message,
)
from src.ingestion.connectors.discord_connector import (
    verify_discord_signature,
    retrieve_discord_chat_history,
    retrieve_discord_user_name,
    send_discord_message,
)
from src.ingestion.connectors.teams_connector import (
    verify_teams_request,
    retrieve_teams_chat_history,
    retrieve_teams_user_name,
    send_teams_message,
)
from src.llm.pipeline import PostmortemAgent

router = APIRouter()

async def generate_and_send_postmortem(incident: Incident):
    agent = PostmortemAgent()
    postmortem = agent.run(incident)

    if incident.source == "slack":
        await send_slack_message(incident.channel_id, f"*Postmortem for incident `{incident.incident_id}`:*\n\n{postmortem}")
    elif incident.source == "discord":
        await send_discord_message(incident.channel_id, f"**Postmortem for incident `{incident.incident_id}`**\n\n{postmortem}")
    elif incident.source == "teams":
        await send_teams_message(incident.channel_id, f"**Postmortem for incident `{incident.incident_id}`**\n\n{postmortem}")
    else:
        print("Unknown incident source; no outbound message sent.")

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
                user_id=msg.get("user","unknown"),
                username=await retrieve_slack_user_name(msg.get("user")) or "Unknown",
                text=msg.get("text",""),
                timestamp=datetime.fromtimestamp(float(msg.get("ts", 0))),
                source="slack"
            )
        )

    incident = Incident(
        incident_id=str(uuid.uuid4()),
        channel_id=channel_id,
        triggered_by_user_id=user_id,
        triggered_by_user_name=user_name,
        channel_name=channel_name,
        conversation=conversation,
        source="slack",
        trigger_platform="slack_slash"
    )

    background_tasks.add_task(generate_and_send_postmortem, incident)
    return PlainTextResponse("Generating postmortem...", status_code=200)

@router.post("/discord")
async def handle_discord_interaction(request: Request, background_tasks: BackgroundTasks):
    body: bytes = await request.body()

    verify_discord_signature(request, body)

    payload = await request.json()
    parsed = discord_parser.parse_interaction_payload(payload)

    channel_id = parsed.get("channel_id")
    user_id = parsed.get("user_id")
    user_name = await retrieve_discord_user_name(user_id)
    channel_name = parsed.get("channel_name")

    messages = await retrieve_discord_chat_history(channel_id)
    conversation: List[Message] = []
    for msg in messages:
        conversation.append(
            Message(
                user_id=msg.get("author", {}).get("id", "unknown"),
                username=msg.get("author", {}).get("username") or "Unknown",
                text=msg.get("content", ""),
                timestamp=datetime.fromtimestamp(float(msg.get("timestamp", datetime.utcnow().timestamp()))),
                source="discord"
            )
        )

    incident = Incident(
        incident_id=str(uuid.uuid4()),
        channel_id=channel_id,
        triggered_by_user_id=user_id,
        triggered_by_user_name=user_name,
        channel_name=channel_name,
        conversation=conversation,
        source="discord",
        trigger_platform=parsed.get("trigger_platform", "discord_interaction")
    )

    background_tasks.add_task(generate_and_send_postmortem, incident)
    return JSONResponse({"type": 200, "message": "Postmortem generation started."})

@router.post("/teams")
async def handle_teams_trigger(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint that accepts triggers from multiple Platforms:
      - teams:channel_message (Graph webhook)
      - teams:incoming_webhook
      - teams:adaptive_card (action)
      - power_automate
    The payload should include enough context (channelId or conversationId). Parsers attempt to normalize common Teams payloads.
    """
    body: bytes = await request.body()
    json_payload = await request.json()

    verify_teams_request(request, body)

    parsed = teams_parser.parse_trigger_payload(json_payload)
    channel_id = parsed.get("channel_id")
    user_id = parsed.get("user_id")
    user_name = await retrieve_teams_user_name(user_id)
    channel_name = parsed.get("channel_name")
    trigger_platform = parsed.get("trigger_platform", "teams_webhook")

    messages = await retrieve_teams_chat_history(channel_id)
    conversation: List[Message] = []
    for msg in messages:
        conversation.append(
            Message(
                user_id=msg.get("from", {}).get("user", {}).get("id", "unknown"),
                username=msg.get("from", {}).get("user", {}).get("displayName") or "Unknown",
                text=msg.get("body", {}).get("content", ""),
                timestamp=datetime.fromtimestamp(float(msg.get("createdDateTime", datetime.utcnow().timestamp()))),
                source="teams"
            )
        )

    incident = Incident(
        incident_id=str(uuid.uuid4()),
        channel_id=channel_id,
        triggered_by_user_id=user_id,
        triggered_by_user_name=user_name,
        channel_name=channel_name,
        conversation=conversation,
        source="teams",
        trigger_platform=trigger_platform
    )

    background_tasks.add_task(generate_and_send_postmortem, incident)
    return PlainTextResponse("Generating postmortem...", status_code=200)
