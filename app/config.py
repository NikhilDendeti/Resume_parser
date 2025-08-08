import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Resume Parser API"
    
    # Redis Settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    CACHE_TTL: int = 3600  # 1 hour
    
    # LLM API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Processing Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    SUPPORTED_FORMATS: list = ["pdf", "docx", "doc", "txt", "png", "jpg", "jpeg"]
    
    # Rule-based Parser Confidence Threshold
    RULE_CONFIDENCE_THRESHOLD: float = 0.85
    
    # Queue Settings
    QUEUE_NAME: str = "resume_parsing"
    
    class Config:
        env_file = ".env"

settings = Settings()