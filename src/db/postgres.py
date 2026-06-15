from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base

# Database URL (Docker Postgres)
DB_URL = "postgresql://atlas:atlas@localhost:5450/atlas"

# Create engine
engine = create_engine(DB_URL, echo=False)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# -----------------------------
# DB INITIALIZATION FUNCTION
# -----------------------------
def init_db():
    """
    Creates all tables defined in SQLAlchemy models.
    Safe to call multiple times (does not drop existing tables).
    """
    Base.metadata.create_all(bind=engine)