"""
Scrapy pipelines for LeadTool data processing
"""
import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func
from app.models.database import Company, Contact, MonthlyData, Base
from app.models.schemas import CompanyCreate, ContactCreate
import logging

logger = logging.getLogger(__name__)


class DatabasePipeline:
    """Pipeline to store scraped data in database"""
    
    def __init__(self):
        self.engine = None
        self.Session = None
    
    def open_spider(self, spider):
        """Initialize database connection when spider opens"""
        try:
            # Get database URL from spider settings
            database_url = spider.settings.get('DATABASE_URL', 'sqlite:///./data/leadtool.db')
            
            # Create engine and session
            self.engine = create_engine(database_url)
            self.Session = sessionmaker(bind=self.engine)
            
            # Create tables if they don't exist
            Base.metadata.create_all(bind=self.engine)
            
            logger.info(f"Database pipeline initialized with URL: {database_url}")
        except Exception as e:
            logger.error(f"Failed to initialize database pipeline: {e}")
            raise
    
    def close_spider(self, spider):
        """Clean up database connection when spider closes"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database pipeline closed")
    
    def process_item(self, item, spider):
        """Process scraped item and store in database"""
        try:
            session = self.Session()
            
            if item['type'] == 'company':
                self.process_company_item(item, session)
            elif item['type'] == 'contact':
                self.process_contact_item(item, session)
            
            session.commit()
            session.close()
            
        except Exception as e:
            logger.error(f"Error processing item: {e}")
            if 'session' in locals():
                session.rollback()
                session.close()
            raise
        
        return item
    
    def process_company_item(self, item, session):
        """Process and store company data"""
        try:
            company_data = item['data']
            month_key = item['month_key']
            source_url = item['source_url']
            query_name = item.get('query_name', '')
            
            # Check if company already exists (by name and address for Google Maps)
            existing_company = None
            if company_data.get('address'):
                existing_company = session.query(Company).filter(
                    Company.name == company_data['name'],
                    Company.address == company_data.get('address')
                ).first()
            else:
                existing_company = session.query(Company).filter(
                    Company.name == company_data['name']
                ).first()
            
            if existing_company:
                company = existing_company
                # Update existing company with new data
                for key, value in company_data.items():
                    if value and hasattr(company, key):
                        setattr(company, key, value)
                company.updated_at = func.now()
            else:
                # Create new company
                company = Company(**company_data)
                session.add(company)
                session.flush()  # Get the ID
            
            # Store monthly data
            monthly_data = MonthlyData(
                company_id=company.id,
                month_key=month_key,
                data_type='company',
                raw_data=json.dumps(company_data),
                source_url=source_url,
                query_name=query_name
            )
            session.add(monthly_data)
            
            logger.info(f"Processed company: {company.name} from query: {query_name}")
            
        except Exception as e:
            logger.error(f"Error processing company item: {e}")
            raise
    
    def process_contact_item(self, item, session):
        """Process and store contact data"""
        try:
            contact_data = item['data']
            company_data = item['company_data']
            month_key = item['month_key']
            source_url = item['source_url']
            
            # Find the company
            company = session.query(Company).filter(
                Company.name == company_data['name']
            ).first()
            
            if not company:
                logger.warning(f"Company not found for contact: {company_data['name']}")
                return
            
            # Check if contact already exists
            existing_contact = None
            if contact_data.get('phone'):
                existing_contact = session.query(Contact).filter(
                    Contact.phone == contact_data['phone'],
                    Contact.company_id == company.id
                ).first()
            
            if existing_contact:
                contact = existing_contact
                # Update existing contact
                for key, value in contact_data.items():
                    if value and hasattr(contact, key):
                        setattr(contact, key, value)
            else:
                # Create new contact
                contact_data['company_id'] = company.id
                contact = Contact(**contact_data)
                session.add(contact)
                session.flush()  # Get the ID
            
            # Store monthly data
            monthly_data = MonthlyData(
                company_id=company.id,
                month_key=month_key,
                data_type='contact',
                raw_data=json.dumps(contact_data),
                source_url=source_url
            )
            session.add(monthly_data)
            
            logger.info(f"Processed contact: {contact.phone}")
            
        except Exception as e:
            logger.error(f"Error processing contact item: {e}")
            raise
