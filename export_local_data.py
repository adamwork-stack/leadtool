#!/usr/bin/env python
"""
Export data from local SQLite database to JSON
"""
import json
import os
import sys
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.models.database import SessionLocal, Company, Contact, MonthlyData
    print("✅ Database models imported successfully")
except ImportError as e:
    print(f"❌ Error importing database models: {e}")
    sys.exit(1)

def export_data():
    """Export all data from local database to JSON"""
    print("📤 Exporting data from local database...")
    
    db = SessionLocal()
    try:
        # Get all companies
        companies = db.query(Company).all()
        print(f"Found {len(companies)} companies")
        
        # Get all contacts
        contacts = db.query(Contact).all()
        print(f"Found {len(contacts)} contacts")
        
        # Get all monthly data
        monthly_data = db.query(MonthlyData).all()
        print(f"Found {len(monthly_data)} monthly data entries")
        
        # Convert to dictionaries
        companies_data = []
        for company in companies:
            companies_data.append({
                'name': company.name,
                'domain': company.domain,
                'description': company.description,
                'website': company.website,
                'industry': company.industry,
                'size': company.size,
                'location': company.location,
                'category': company.category,
                'address': company.address,
                'phone': company.phone,
                'rating': company.rating,
                'review_count': company.review_count,
                'source': company.source,
                'created_at': company.created_at.isoformat() if company.created_at else None,
                'updated_at': company.updated_at.isoformat() if company.updated_at else None
            })
        
        contacts_data = []
        for contact in contacts:
            contacts_data.append({
                'phone': contact.phone,
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'title': contact.title,
                'department': contact.department,
                'company_id': contact.company_id,
                'is_primary': contact.is_primary,
                'created_at': contact.created_at.isoformat() if contact.created_at else None,
                'updated_at': contact.updated_at.isoformat() if contact.updated_at else None
            })
        
        monthly_data_list = []
        for data in monthly_data:
            monthly_data_list.append({
                'company_id': data.company_id,
                'month_key': data.month_key,
                'data_type': data.data_type,
                'raw_data': data.raw_data,
                'source_url': data.source_url,
                'query_name': data.query_name,
                'scraped_at': data.scraped_at.isoformat() if data.scraped_at else None,
                'is_active': data.is_active
            })
        
        # Create export data
        export_data = {
            'export_date': datetime.now().isoformat(),
            'companies': companies_data,
            'contacts': contacts_data,
            'monthly_data': monthly_data_list
        }
        
        # Save to file
        filename = f"leadtool_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Data exported to {filename}")
        print(f"📊 Summary:")
        print(f"   - Companies: {len(companies_data)}")
        print(f"   - Contacts: {len(contacts_data)}")
        print(f"   - Monthly Data: {len(monthly_data_list)}")
        
        return filename
        
    except Exception as e:
        print(f"❌ Error exporting data: {e}")
        return None
    finally:
        db.close()

def main():
    """Main function"""
    print("LeadTool Data Export")
    print("=" * 30)
    
    filename = export_data()
    
    if filename:
        print(f"\n🎉 Export completed successfully!")
        print(f"📁 File: {filename}")
        print(f"\n📋 Next steps:")
        print(f"1. Upload {filename} to your Render service")
        print(f"2. Use the import script to load data into Render database")
        print(f"3. Or use the scraping button on the Render dashboard")
    else:
        print(f"\n❌ Export failed")

if __name__ == "__main__":
    main()
