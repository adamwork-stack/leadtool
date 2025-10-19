"""
Contacts API endpoints for LeadTool
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional

from app.models.database import get_db, Company, Contact, MonthlyData
from app.models.schemas import (
    Contact as ContactSchema, ContactCreate, ContactUpdate,
    ContactFilter
)

router = APIRouter()

@router.get("/contacts", response_model=List[ContactSchema])
async def get_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    company_id: Optional[int] = None,
    title: Optional[str] = None,
    department: Optional[str] = None,
    is_primary: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get contacts with optional filtering"""
    query = db.query(Contact)
    
    # Apply filters
    if company_id:
        query = query.filter(Contact.company_id == company_id)
    if title:
        query = query.filter(Contact.title.ilike(f"%{title}%"))
    if department:
        query = query.filter(Contact.department.ilike(f"%{department}%"))
    if is_primary is not None:
        query = query.filter(Contact.is_primary == is_primary)
    
    # Apply pagination
    contacts = query.offset(skip).limit(limit).all()
    return contacts

@router.get("/contacts/{contact_id}", response_model=ContactSchema)
async def get_contact(contact_id: int, db: Session = Depends(get_db)):
    """Get a specific contact"""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.post("/contacts", response_model=ContactSchema)
async def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    """Create a new contact"""
    # Check if company exists
    company = db.query(Company).filter(Company.id == contact.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    
    db_contact = Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@router.put("/contacts/{contact_id}", response_model=ContactSchema)
async def update_contact(
    contact_id: int, 
    contact: ContactUpdate, 
    db: Session = Depends(get_db)
):
    """Update a contact"""
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Update only provided fields
    update_data = contact.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_contact, field, value)
    
    db.commit()
    db.refresh(db_contact)
    return db_contact

@router.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    """Delete a contact"""
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    db.delete(db_contact)
    db.commit()
    return {"message": "Contact deleted successfully"}

@router.get("/contacts/search", response_model=List[ContactSchema])
async def search_contacts(
    q: str = Query(..., description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Search contacts by name or title"""
    query = db.query(Contact).filter(
        or_(
            Contact.first_name.ilike(f"%{q}%"),
            Contact.last_name.ilike(f"%{q}%"),
            Contact.title.ilike(f"%{q}%"),
            Contact.department.ilike(f"%{q}%")
        )
    )
    
    contacts = query.offset(skip).limit(limit).all()
    return contacts

@router.get("/contacts/stats")
async def get_contact_stats(db: Session = Depends(get_db)):
    """Get contact statistics"""
    total_contacts = db.query(Contact).count()
    
    # Get contacts by title
    title_stats = db.query(
        Contact.title, 
        db.func.count(Contact.id).label('count')
    ).group_by(Contact.title).all()
    
    # Get contacts by department
    department_stats = db.query(
        Contact.department, 
        db.func.count(Contact.id).label('count')
    ).group_by(Contact.department).all()
    
    # Get contacts with phones
    contacts_with_phones = db.query(Contact).filter(Contact.phone.isnot(None)).count()
    
    return {
        "total_contacts": total_contacts,
        "contacts_with_phones": contacts_with_phones,
        "by_title": [{"title": i[0], "count": i[1]} for i in title_stats if i[0]],
        "by_department": [{"department": i[0], "count": i[1]} for i in department_stats if i[0]]
    }
