from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str
    env: str
    database_url: str
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

