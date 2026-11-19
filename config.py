from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_name: str = "ALONE CLOUD"
    environment: str = "production"
    database_url: str
    admin_api_key: str
    cloud_api_key: str
    ai_base_url: str = "https://api.openai.com/v1"
    ai_api_key: str
    ai_model: str = "gpt-4o-mini"
    cors_origins: str = "*"
    max_request_chars: int = 20000

settings = Settings()
