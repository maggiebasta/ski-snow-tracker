from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .config import get_settings
from .models.weather import Base
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# Configure engine with proper PostgreSQL settings for Supabase
engine = create_engine(
    settings.database_url,
    pool_size=20,               # Increased for production
    max_overflow=10,            # Allow temporary additional connections
    pool_timeout=30,            # Seconds to wait for a connection
    pool_recycle=1800,         # Recycle connections every 30 minutes
    connect_args={
        "sslmode": "require",    # Required for Supabase
        "connect_timeout": 30,
        "options": "-c AddressFamily=ipv4"  # Force IPv4
    } if settings.is_production else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Successfully initialized database tables")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
