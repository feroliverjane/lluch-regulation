from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import field_validator
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "Lluch Regulation - Composite Management"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    # Database
    DATABASE_URL: str = "postgresql://lluch_user:lluch_pass@localhost:5432/lluch_regulation"
    TEST_DATABASE_URL: str = "postgresql://lluch_user:lluch_pass@localhost:5432/lluch_regulation_test"
    
    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://localhost:3000"]
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    UPLOAD_DIR: str = "../data/uploads"
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@lluchregulation.com"
    
    # Integration APIs
    CHEMSD_API_URL: str = ""
    CHEMSD_API_KEY: str = ""
    ERP_API_URL: str = ""
    ERP_API_KEY: str = ""
    CRM_API_URL: str = ""
    CRM_API_KEY: str = ""
    
    # OpenAI API (for document extraction)
    OPENAI_API_KEY: str = ""
    USE_OPENAI_FOR_EXTRACTION: bool = False  # Set to True to use OpenAI instead of OCR
    
    # Composite Settings
    COMPOSITE_THRESHOLD_PERCENT: float = 5.0
    REVIEW_PERIOD_DAYS: int = 90
    
    # Blue Line Settings
    BLUE_LINE_PURCHASE_LOOKBACK_YEARS: int = 3
    BLUE_LINE_AUTO_SYNC_ENABLED: bool = True
    BLUE_LINE_SYNC_INTERVAL_MINUTES: int = 60
    SAP_COMPOSITE_API_URL: str = ""
    SAP_COMPOSITE_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

