from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slack_sdk.signature import SignatureVerifier
import uvicorn
from urllib.parse import parse_qs
import time

CORS_ORIGINS = ["*"]
ENV = "development"

verifier = SignatureVerifier(SLACK_SIGNING_SECRET)

def verify_slack_signature(request: Request, body: bytes):
    """Verify incoming Slack request signature"""
    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    signature = request.headers.get("X-Slack-Signature")

    print(f"🔍 Verifying signature:")
    print(f"   Timestamp: {timestamp}")
    print(f"   Signature: {signature}")
    print(f"   Body length: {len(body)} bytes")

    
    if not timestamp or not signature:
        raise HTTPException(status_code=400, detail="Missing Slack signature headers.")

    
    try:
        req_time = int(timestamp)
        current_time = int(time.time())
        if abs(current_time - req_time) > 60 * 5:  
            raise HTTPException(status_code=400, detail="Request timestamp too old.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp.")

    
    verified = verifier.is_valid(body, timestamp, signature)

    if not verified:
        print("❌ Signature verification failed!")
        raise HTTPException(status_code=400, detail="Invalid Slack signature.")
    
    print("✅ Signature verified successfully!")





def create_app() -> FastAPI:
    app = FastAPI(
        title="Aftermath AI - Incident Postmortem Generator",
        version="0.1.0",
        description="AI agent that turns incident discussions + deploy logs into postmortem reports",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def health():
        return {"status": "ok"}

    
    @app.post("/slash")
    async def handle_slash_command(request: Request, background_tasks: BackgroundTasks):
        body = await request.body()

        
        try:
            verify_slack_signature(request, body)
        except HTTPException as e:
            print(f"❌ Verification error: {e.detail}")
            return JSONResponse(content={"error": e.detail}, status_code=e.status_code)

        
        try:
            body_str = body.decode('utf-8')
            parsed = parse_qs(body_str)
            
            form = {k: v[0] if v else '' for k, v in parsed.items()}
        except Exception as e:
            print(f"❌ Form parsing error: {e}")
            return JSONResponse(
                content={"error": f"Invalid form data: {str(e)}"}, 
                status_code=400
            )

        command_text = form.get("text", "").strip()
        channel_id = form.get("channel_id", "unknown")
        user_id = form.get("user_id", "unknown")

        print(f"📥 Received command: text='{command_text}', channel={channel_id}, user={user_id}")

        if not command_text:
            return JSONResponse(
                content={"text": "Usage: `/aftermath generate-postmortem`"},
                status_code=200,
            )

        if command_text == "generate-postmortem":
            background_tasks.add_task(run_postmortem_generation, channel_id, user_id)
            return JSONResponse(
                content={
                    "text": "⏳ Generating postmortem report... I'll post it here soon."
                },
                status_code=200,
            )

        return JSONResponse(
            content={"text": f"Unknown command `{command_text}`"}, status_code=200
        )

    return app





def run_postmortem_generation(channel_id: str, user_id: str):
    """Simulated background postmortem generation"""
    print(f"🧠 Running fake postmortem generation for channel={channel_id}, user={user_id}")
    time.sleep(2)
    print("✅ Postmortem generation complete!")





if __name__ == "__main__":
    app = create_app()
    print("🚀 Starting local server at http://127.0.0.1:8000 ...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)