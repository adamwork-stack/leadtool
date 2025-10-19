"""
Pydantic schemas for LeadTool API
"""
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime


# Company schemas
class CompanyBase(BaseModel):
    name: str
    domain: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    location: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    location: Optional[str] = None


class Company(CompanyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Contact schemas
class ContactBase(BaseModel):
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    address: Optional[str] = None
    linkedin: Optional[str] = None
    is_primary: bool = False


class ContactCreate(ContactBase):
    company_id: int


class ContactUpdate(BaseModel):
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    address: Optional[str] = None
    linkedin: Optional[str] = None
    is_primary: Optional[bool] = None


class Contact(ContactBase):
    id: int
    company_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Monthly data schemas
class MonthlyDataBase(BaseModel):
    month_key: str
    data_type: str
    raw_data: Optional[str] = None
    source_url: Optional[str] = None
    is_active: bool = True


class MonthlyDataCreate(MonthlyDataBase):
    company_id: int


class MonthlyData(MonthlyDataBase):
    id: int
    company_id: int
    scraped_at: datetime
    
    class Config:
        from_attributes = True


# Response schemas
class CompanyWithContacts(Company):
    contacts: List[Contact] = []


class CompanyWithMonthlyData(Company):
    monthly_data: List[MonthlyData] = []


# Filter and search schemas
class CompanyFilter(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    month_key: Optional[str] = None


class ContactFilter(BaseModel):
    company_id: Optional[int] = None
    title: Optional[str] = None
    department: Optional[str] = None
    is_primary: Optional[bool] = None


# Export schemas
class ExportRequest(BaseModel):
    format: str = "csv"  # csv or excel
    filters: Optional[CompanyFilter] = None
    month_key: Optional[str] = None
