from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "unify"
    environment: str = "dev"
    database_url: str = "sqlite:///./unify.db"
    api_token: str = "dev-token-change-me"
    ui_password: str = "dev-password-change-me"
    session_secret: str = "dev-session-secret-change-me"

    model_config = SettingsConfigDict(env_prefix="UNIFY_", env_file=".env")

    @model_validator(mode="after")
    def reject_default_token_outside_development(self) -> "Settings":
        if self.environment != "dev" and self.api_token == "dev-token-change-me":
            raise ValueError("refusing to start in non-dev with default token")
        if self.environment != "dev" and (
            self.ui_password.startswith("dev-") or self.session_secret.startswith("dev-")
        ):
            raise ValueError("refusing to start in non-dev with default UI credentials")
        return self


settings = Settings()
