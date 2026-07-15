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

    # CORS — origins allowed to call the API from a browser (the Next.js app).
    # Comma-separated in env; sensible localhost defaults for dev.
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
