from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SLACK_TOKEN: str
    SLACK_SIGNING_SECRET: str
    OPENAI_API_KEY: str
    CORS_ORIGINS: list[str] = ["*"]
    ENV: str = "development"

    DISCORD_TOKEN: str
    DISCORD_PUBLIC_KEY: str
    TEAMS_CLIENT_ID: str
    TEAMS_CLIENT_SECRET: str
    TEAMS_TENANT_ID: str
    TEAMS_GRAPH_TOKEN: str
    class Config:
        env_file = ".env"

settings = Settings()
