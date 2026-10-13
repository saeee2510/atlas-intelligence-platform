import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base

load_dotenv()

# Docker Postgres from docker-compose.yml (port 5451, so it can run beside other local Postgres containers)
DB_URL = os.getenv("DATABASE_URL", "postgresql://atlas:atlas@localhost:5451/atlas")

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