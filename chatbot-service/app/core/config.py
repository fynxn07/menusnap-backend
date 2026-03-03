from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "chatbot-service"
    ENV: str = "development"

    # 🔹 LLM / API keys
    OPENAI_API_KEY: str | None = None

    # 🔥 AWS Analytics Configuration
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_DEFAULT_REGION: str | None = None
    ANALYTICS_SQS_URL: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()