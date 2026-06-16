from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Text,
    ForeignKey
)
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    normalized_name = Column(String)
    website = Column(String)
    description = Column(Text)

    embedding = Column(Vector(1536))


class CanonicalCompany(Base):
    __tablename__ = "canonical_companies"

    id = Column(Integer, primary_key=True)

    canonical_name = Column(String)
    website = Column(String)

    industry = Column(String)
    subcategory = Column(String)
    business_model = Column(String)
    company_size = Column(String)

    confidence = Column(Float)


class CompanyMapping(Base):
    __tablename__ = "company_mappings"

    id = Column(Integer, primary_key=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id")
    )

    canonical_company_id = Column(
        Integer,
        ForeignKey("canonical_companies.id")
    )

    match_score = Column(Float)

class CompanyRelationship(Base):
    __tablename__ = "company_relationships"

    id = Column(Integer, primary_key=True)

    source_company = Column(Integer, ForeignKey("canonical_companies.id"))
    target_company = Column(Integer, ForeignKey("canonical_companies.id"))

    relationship_type = Column(String)  # competitor, partner, acquired, etc.
    confidence = Column(Float)

