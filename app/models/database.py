"""
Database models for LeadTool using SQLAlchemy
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Index, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
import os

Base = declarative_base()

# Database URL configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./data/leadtool.db')

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Company(Base):
    """Company information model"""
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    domain = Column(String(255), nullable=True, index=True)
    description = Column(Text, nullable=True)
    website = Column(String(500), nullable=True)
    industry = Column(String(100), nullable=True)
    size = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    
    # Google Maps specific fields
    category = Column(String(100), nullable=True)  # Business category/type
    address = Column(Text, nullable=True)  # Full business address
    phone = Column(String(50), nullable=True)  # Business phone number
    rating = Column(String(10), nullable=True)  # Google Maps rating
    review_count = Column(Integer, nullable=True)  # Number of reviews
    source = Column(String(50), nullable=True, default='Google Maps')  # Data source
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    contacts = relationship("Contact", back_populates="company", cascade="all, delete-orphan")
    monthly_data = relationship("MonthlyData", back_populates="company", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_company_name_domain', 'name', 'domain'),
        Index('idx_company_category', 'category'),
        Index('idx_company_location', 'location'),
        Index('idx_company_source', 'source'),
    )


class Contact(Base):
    """Contact information model"""
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    phone = Column(String(50), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    title = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    linkedin = Column(String(500), nullable=True)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="contacts")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_contact_company_id', 'company_id'),
    )


class MonthlyData(Base):
    """Monthly data versioning model"""
    __tablename__ = "monthly_data"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    month_key = Column(String(7), nullable=False, index=True)  # Format: "2025-01"
    data_type = Column(String(50), nullable=False)  # "company", "contact"
    raw_data = Column(Text, nullable=True)  # JSON string of scraped data
    source_url = Column(String(1000), nullable=True)
    query_name = Column(String(255), nullable=True)  # Google Maps search query name
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    company = relationship("Company", back_populates="monthly_data")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_monthly_company_month', 'company_id', 'month_key'),
        Index('idx_monthly_type_month', 'data_type', 'month_key'),
        Index('idx_monthly_query', 'query_name'),
    )

# Create tables
Base.metadata.create_all(bind=engine)