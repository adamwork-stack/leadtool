"""
Export API endpoints for LeadTool
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
import csv
import io
import pandas as pd
from datetime import datetime

from app.models.database import get_db, Company, Contact, MonthlyData
from app.models.schemas import ExportRequest

router = APIRouter()

@router.get("/export/companies")
async def export_companies(
    format: str = Query("csv", regex="^(csv|excel)$"),
    name: Optional[str] = None,
    domain: Optional[str] = None,
    industry: Optional[str] = None,
    location: Optional[str] = None,
    month_key: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Export companies to CSV or Excel"""
    query = db.query(Company)
    
    # Apply filters
    if name:
        query = query.filter(Company.name.ilike(f"%{name}%"))
    if domain:
        query = query.filter(Company.domain.ilike(f"%{domain}%"))
    if industry:
        query = query.filter(Company.industry.ilike(f"%{industry}%"))
    if location:
        query = query.filter(Company.location.ilike(f"%{location}%"))
    
    # Filter by month if specified
    if month_key:
        query = query.join(MonthlyData).filter(
            MonthlyData.month_key == month_key,
            MonthlyData.is_active == True
        )
    
    companies = query.all()
    
    if format == "csv":
        return export_companies_csv(companies)
    else:
        return export_companies_excel(companies)

@router.get("/export/contacts")
async def export_contacts(
    format: str = Query("csv", regex="^(csv|excel)$"),
    company_id: Optional[int] = None,
    title: Optional[str] = None,
    department: Optional[str] = None,
    is_primary: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Export contacts to CSV or Excel"""
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
    
    contacts = query.all()
    
    if format == "csv":
        return export_contacts_csv(contacts)
    else:
        return export_contacts_excel(contacts)

@router.get("/export/combined")
async def export_combined(
    format: str = Query("csv", regex="^(csv|excel)$"),
    month_key: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Export combined company and contact data"""
    # Get companies with their contacts
    query = db.query(Company)
    
    if month_key:
        query = query.join(MonthlyData).filter(
            MonthlyData.month_key == month_key,
            MonthlyData.is_active == True
        )
    
    companies = query.all()
    
    if format == "csv":
        return export_combined_csv(companies)
    else:
        return export_combined_excel(companies)

def export_companies_csv(companies):
    """Export companies to CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Name', 'Domain', 'Description', 'Website', 
        'Industry', 'Size', 'Location', 'Created At', 'Updated At'
    ])
    
    # Write data
    for company in companies:
        writer.writerow([
            company.id,
            company.name,
            company.domain,
            company.description,
            company.website,
            company.industry,
            company.size,
            company.location,
            company.created_at.isoformat() if company.created_at else '',
            company.updated_at.isoformat() if company.updated_at else ''
        ])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename=companies.csv'}
    )

def export_contacts_csv(contacts):
    """Export contacts to CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Company ID', 'Phone', 'First Name', 'Last Name',
        'Title', 'Department', 'Address', 'LinkedIn', 'Is Primary', 'Created At'
    ])
    
    # Write data
    for contact in contacts:
        writer.writerow([
            contact.id,
            contact.company_id,
            contact.phone,
            contact.first_name,
            contact.last_name,
            contact.title,
            contact.department,
            contact.address,
            contact.linkedin,
            contact.is_primary,
            contact.created_at.isoformat() if contact.created_at else ''
        ])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename=contacts.csv'}
    )

def export_combined_csv(companies):
    """Export combined data to CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Company ID', 'Company Name', 'Company Domain', 'Company Industry', 'Company Location',
        'Contact ID', 'Contact Phone', 'Contact Name', 'Contact Title',
        'Contact Department', 'Is Primary Contact'
    ])
    
    # Write data
    for company in companies:
        if company.contacts:
            for contact in company.contacts:
                writer.writerow([
                    company.id,
                    company.name,
                    company.domain,
                    company.industry,
                    company.location,
                    contact.id,
                    contact.phone,
                    f"{contact.first_name} {contact.last_name}".strip(),
                    contact.title,
                    contact.department,
                    contact.is_primary
                ])
        else:
            # Company without contacts
            writer.writerow([
                company.id,
                company.name,
                company.domain,
                company.industry,
                company.location,
                '', '', '', '', '', '', ''
            ])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename=combined_data.csv'}
    )

def export_companies_excel(companies):
    """Export companies to Excel"""
    df = pd.DataFrame([{
        'ID': company.id,
        'Name': company.name,
        'Domain': company.domain,
        'Description': company.description,
        'Website': company.website,
        'Industry': company.industry,
        'Size': company.size,
        'Location': company.location,
        'Created At': company.created_at.isoformat() if company.created_at else '',
        'Updated At': company.updated_at.isoformat() if company.updated_at else ''
    } for company in companies])
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Companies', index=False)
    
    output.seek(0)
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=companies.xlsx'}
    )

def export_contacts_excel(contacts):
    """Export contacts to Excel"""
    df = pd.DataFrame([{
        'ID': contact.id,
        'Company ID': contact.company_id,
        'Phone': contact.phone,
        'First Name': contact.first_name,
        'Last Name': contact.last_name,
        'Title': contact.title,
        'Department': contact.department,
        'Address': contact.address,
        'LinkedIn': contact.linkedin,
        'Is Primary': contact.is_primary,
        'Created At': contact.created_at.isoformat() if contact.created_at else ''
    } for contact in contacts])
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Contacts', index=False)
    
    output.seek(0)
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=contacts.xlsx'}
    )

def export_combined_excel(companies):
    """Export combined data to Excel"""
    data = []
    for company in companies:
        if company.contacts:
            for contact in company.contacts:
                data.append({
                    'Company ID': company.id,
                    'Company Name': company.name,
                    'Company Domain': company.domain,
                    'Company Industry': company.industry,
                    'Company Location': company.location,
                    'Contact ID': contact.id,
                    'Contact Phone': contact.phone,
                    'Contact Name': f"{contact.first_name} {contact.last_name}".strip(),
                    'Contact Title': contact.title,
                    'Contact Department': contact.department,
                    'Is Primary Contact': contact.is_primary
                })
        else:
            data.append({
                'Company ID': company.id,
                'Company Name': company.name,
                'Company Domain': company.domain,
                'Company Industry': company.industry,
                'Company Location': company.location,
                'Contact ID': '',
                'Contact Phone': '',
                'Contact Name': '',
                'Contact Title': '',
                'Contact Department': '',
                'Is Primary Contact': ''
            })
    
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Combined Data', index=False)
    
    output.seek(0)
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=combined_data.xlsx'}
    )
