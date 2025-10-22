from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SLACK_TOKEN: str
    SLACK_SIGNING_SECRET: str
    OPENAI_API_KEY: str
    CORS_ORIGINS: list[str] = ["*"]
    ENV: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
