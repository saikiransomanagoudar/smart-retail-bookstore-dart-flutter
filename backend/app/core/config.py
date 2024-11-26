import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path)

class Settings(BaseSettings):
    PROJECT_NAME: str = "Book Recommendation System"
    PROJECT_VERSION: str = "1.0.0"
    DATABASE_URL: str = "postgresql://postgres:admin@localhost/book_recommendations"
    OPENAI_API_KEY: str
    JWT_SECRET_KEY: str = "6034eed2f5c1e735aca0ec8e37edef3c8b4233606a0a0233734e0bcb826b5704"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    GOOGLE_BOOKS_API_KEY: str

    class Config:
        env_file = dotenv_path
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()

print(f"Loaded settings: DATABASE_URL={settings.DATABASE_URL}, GOOGLE_BOOKS_API_KEY={settings.GOOGLE_BOOKS_API_KEY}, OPENAI_API_KEY={settings.OPENAI_API_KEY}")