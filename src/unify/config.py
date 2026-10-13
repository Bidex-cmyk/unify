from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "unify"
    environment: str = "dev"
    database_url: str = "sqlite:///./unify.db"
    api_token: str = "dev-token-change-me"

    model_config = SettingsConfigDict(env_prefix="UNIFY_", env_file=".env")


settings = Settings()
