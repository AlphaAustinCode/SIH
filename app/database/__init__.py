from app.database.base import Base
from app.database.session import engine, SessionLocal, get_db

def init_db() -> None:
    """
    Create database tables.
    """
    # Import models so SQLAlchemy registers them before creating tables
    from app.database import models  # noqa: F401
    
    Base.metadata.create_all(bind=engine)