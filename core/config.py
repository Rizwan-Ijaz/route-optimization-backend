from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    PROJECT_NAME: str = "Taxi Route Optimization"

    class Config:
        env_file = ".env"

settings = Settings()