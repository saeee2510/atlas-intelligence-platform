from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.models import Base

DB_URL = "postgresql://atlas:atlas@localhost:5450/atlas"

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)