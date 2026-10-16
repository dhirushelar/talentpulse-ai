import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "resume-parser-secret-key-2026")
    
    # Database configuration
    # Default to PostgreSQL, with fallback capability if local PostgreSQL service is not running
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", 
        "postgresql+psycopg2://postgres:postgres@localhost:5432/resume_parser"
    )
    # Optional fallback for local dev when PostgreSQL is not yet spun up
    SQLITE_FALLBACK_URI = f"sqlite:///{BASE_DIR / 'resume_parser.db'}"
    USE_SQLITE_FALLBACK = os.getenv("USE_SQLITE_FALLBACK", "true").lower() in ("true", "1", "yes")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Uploads
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt"}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    
    # spaCy model configuration
    SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_sm")

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
