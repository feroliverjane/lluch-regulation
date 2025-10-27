"""
Production configuration for Railway deployment
"""
import os
from .config import Settings

class ProductionSettings(Settings):
    """Production settings with environment variables"""
    
    # Override with production values
    DEBUG: bool = False
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production")
    
    # Database from Railway
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost:5432/lluch_regulation")
    
    # CORS for production
    ALLOWED_ORIGINS: list = [
        "https://your-netlify-site.netlify.app",  # Replace with your actual Netlify URL
        "http://localhost:5173",  # Keep for local development
    ]
    
    # Redis (optional for production)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # File uploads
    UPLOAD_DIR: str = "/tmp/uploads"  # Railway uses /tmp for file storage
    
    # Email settings
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "noreply@lluchregulation.com")
    
    # Integration APIs
    CHEMSD_API_URL: str = os.getenv("CHEMSD_API_URL", "")
    CHEMSD_API_KEY: str = os.getenv("CHEMSD_API_KEY", "")
    ERP_API_URL: str = os.getenv("ERP_API_URL", "")
    ERP_API_KEY: str = os.getenv("ERP_API_KEY", "")
    CRM_API_URL: str = os.getenv("CRM_API_URL", "")
    CRM_API_KEY: str = os.getenv("CRM_API_KEY", "")

# Use production settings in production
if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("PRODUCTION"):
    settings = ProductionSettings()
else:
    from .config import settings


