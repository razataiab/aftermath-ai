from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.app.core.config import settings
from src.app.api.v1.reports import router as reports_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Aftermath AI - Incident Postmortem Generator",
        version="0.2.0",
        description="AI agent that turns incident discussions + deploy logs into postmortem reports (Slack / Discord / Teams)",
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
    
    app.include_router(reports_router, prefix="/api/v1", tags=["Integrations"])

    return app

app = create_app()

if __name__ == "__main__":
    print("Starting local server at http://127.0.0.1:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)