from sqlalchemy import Column, String, Float, Integer, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    normalized_name = Column(String)
    website = Column(String)
    description = Column(Text)

    embedding = Column(Text)  # we store vector as string for now