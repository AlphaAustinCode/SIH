from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Default to SQLite if nothing is provided in the .env file
    DATABASE_URL: str = "sqlite:///./railway_blocks.db"

    # Pydantic V2 uses model_config instead of the inner Config class
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  
    )

settings = Settings()