import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import Config

logger = logging.getLogger(__name__)

Base = declarative_base()

def get_engine():
    """Attempts to connect to the configured database, falling back to SQLite if PostgreSQL fails."""
    primary_uri = Config.SQLALCHEMY_DATABASE_URI
    try:
        engine = create_engine(primary_uri, pool_pre_ping=True)
        # Test connection
        with engine.connect() as conn:
            pass
        logger.info(f"Connected to primary database: {primary_uri.split('@')[-1] if '@' in primary_uri else primary_uri}")
        return engine, "PostgreSQL" if "postgresql" in primary_uri else "Custom"
    except Exception as e:
        if Config.USE_SQLITE_FALLBACK and "postgresql" in primary_uri:
            logger.warning(
                f"Could not connect to PostgreSQL ({e}). Falling back to SQLite: {Config.SQLITE_FALLBACK_URI}"
            )
            fallback_engine = create_engine(
                Config.SQLITE_FALLBACK_URI,
                connect_args={"check_same_thread": False}
            )
            return fallback_engine, "SQLite (Fallback)"
        else:
            raise e

engine, DB_DIALECT = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Creates database tables if they do not exist."""
    import models  # Ensure all models are registered
    Base.metadata.create_all(bind=engine)
