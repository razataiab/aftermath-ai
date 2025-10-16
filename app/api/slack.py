from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from slack_sdk.signature import SignatureVerifier
from fastapi.responses import JSONResponse
from config import settings

verifier = SignatureVerifier(settings.SLACK_SIGNING_SECRET)
router = APIRouter()

def verify_slack_signature(request: Request, body: bytes):
    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    signature = request.headers.get("X-Slack-Signature")

    verified = verifier.is_valid(body.decode(), timestamp, signature)
    
    if not verified:
        raise HTTPException(status_code=400, detail="Invalid Slack signature.")

@router.post("/slash")
async def handle_slash_command(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()
    verify_slack_signature(request, body)

    form = dict((k, v) for k, v in [pair.split("=") for pair in body.decode().split("&")])
    command_text = form.get("text", "").strip()
    channel_id = form.get("channel_id")
    user_id = form.get("user_id")

    if not command_text:
        return JSONResponse(content={"text": "Usage: `/aftermath generate-postmortem`"}, status_code=200)

    if command_text == "generate-postmortem":
        background_tasks.add_task(run_postmortem_generation, channel_id, user_id)
        return JSONResponse(
            content={"text": "⏳ Generating postmortem report... I’ll post it here soon."},
            status_code=200
        )

    return JSONResponse(content={"text": f"Unknown command `{command_text}`"}, status_code=200)

# async def run_postmortem_generation(channel_id: str, user_id: str):
#     pass
#    # try:
#    #     messages = slack_fetcher.get_channel_messages(channel_id)
#    #     deploy_meta = slack_fetcher.get_recent_deploy(channel_id)
#    #     result = agent_pipeline.run_incident_pipeline(messages=messages, deploy=deploy_meta)
#    #     slack_poster.post_report(channel_id, result)
#
#    # except Exception as e:
#    #     slack_poster.post_error(channel_id, f"Error while generating postmortem: {e}")
#    #     raise