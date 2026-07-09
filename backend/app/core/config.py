from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # OpenAI (used from Phase 6)
    openai_api_key: str = "sk-REPLACE_ME"
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    chat_prompt_limit: int = 5

    # Database / Redis (Docker hostnames overridden via env in compose)
    database_url: str = "mysql+pymysql://shop:shop@localhost:3306/shopdb"
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 1440


settings = Settings()
