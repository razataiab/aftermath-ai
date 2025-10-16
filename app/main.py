from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slack_sdk.signature import SignatureVerifier
import uvicorn
from config import settings
from api import slack
from api.slack import verify_slack_signature, handle_slash_command

verifier = SignatureVerifier(settings.SLACK_SIGNING_SECRET)

def create_app() -> FastAPI:
    app = FastAPI(
        title="Aftermath AI - Incident Postmortem Generator",
        version="0.1.0",
        description="AI agent that turns incident discussions + deploy logs into postmortem reports",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def health():
        return {"status": "ok"}
    
    app.include_router(slack.router, prefix="", tags=["Slack Integration"])

    return app

if __name__ == "__main__":
    app = create_app()
    print("Starting local server at http://127.0.0.1:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)