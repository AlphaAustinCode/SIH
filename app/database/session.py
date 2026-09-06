from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.database.base import Base


engine = create_engine(
    settings.DATABASE_URL,
    future=True,
    # Required for SQLite when used with multi-threaded apps like FastAPI
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    """
    FastAPI database dependency.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Create database tables.
    """
    # Import models here so SQLAlchemy registers them before creation
    from app.database import models  # noqa: F401
    
    Base.metadata.create_all(bind=engine)