"""
Database Client Utility
Shared database connection utility for all services
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from typing import Generator
import logging

logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dcf_user:dcf_password@postgres:5432/dcf_db"
)

# Global engine and session factory
_engine = None
_SessionLocal = None


def get_database_url() -> str:
    """Get database URL from environment"""
    return DATABASE_URL


def init_database_connection():
    """Initialize database connection"""
    global _engine, _SessionLocal
    
    if _engine is None:
        try:
            _engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                poolclass=NullPool if "test" in DATABASE_URL else None,
                echo=False
            )
            _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
            logger.info(f"Database connection initialized: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise
    
    return _engine, _SessionLocal


def get_db_session():
    """Get database session factory"""
    if _SessionLocal is None:
        init_database_connection()
    return _SessionLocal()


@contextmanager
def get_db() -> Generator:
    """Dependency for getting database session (context manager)"""
    session = get_db_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def check_database_connection() -> bool:
    """Check if database connection is available"""
    try:
        engine, _ = init_database_connection()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


def get_database_info() -> dict:
    """Get database information"""
    try:
        engine, _ = init_database_connection()
        with engine.connect() as conn:
            # Get PostgreSQL version
            version_result = conn.execute(text("SELECT version()"))
            version = version_result.scalar()
            
            # Get database name
            db_result = conn.execute(text("SELECT current_database()"))
            db_name = db_result.scalar()
            
            # Get connection count
            conn_result = conn.execute(text(
                "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
            ))
            conn_count = conn_result.scalar()
            
            return {
                "connected": True,
                "database": db_name,
                "version": version.split(",")[0] if version else "Unknown",
                "active_connections": conn_count,
                "url": DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "local"
            }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }


# Initialize on import
try:
    init_database_connection()
except Exception as e:
    logger.warning(f"Database connection not available on startup: {e}")

