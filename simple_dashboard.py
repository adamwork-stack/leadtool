#!/usr/bin/env python
"""
Simple dashboard that reads directly from database
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import subprocess
import os
import sys
import yaml
from datetime import datetime
from app.models.database import SessionLocal, Company, Contact, MonthlyData

def load_config():
    """Load scraping configuration"""
    config_path = 'config/sites.yaml'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {'search_queries': []}

def save_config(config):
    """Save configuration to file"""
    config_path = 'config/sites.yaml'
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

def run_scraper():
    """Run the scraper with visual browser tabs"""
    try:
        # Load current queries
        config = load_config()
        current_queries = config.get('search_queries', [])
        
        if not current_queries:
            return False, "No search queries configured"
        
        st.subheader("🌐 Opening Google Maps in Browser")
        
        # Create progress tracking
        progress_placeholder = st.empty()
        output_placeholder = st.empty()
        
        # Show URLs for manual opening (optional)
        st.write("**Google Maps URLs (open manually if you want to watch):**")
        for i, query in enumerate(current_queries):
            keywords = query.get('keywords', '')
            location = query.get('location', '')
            query_name = query.get('name', f'Query {i+1}')
            
            # Build Google Maps URL
            search_query = f"{keywords} in {location}"
            encoded_query = search_query.replace(' ', '%20')
            maps_url = f"https://www.google.com/maps/search/{encoded_query}"
            
            st.write(f"**{query_name}:** {maps_url}")
            
            # Optional: Open in browser if user wants
            if st.button(f"Open {query_name} in Browser", key=f"open_{i}"):
                try:
                    import webbrowser
                    webbrowser.open_new_tab(maps_url)
                    st.write(f"✅ Opened: {query_name}")
                except Exception as e:
                    st.write(f"❌ Failed to open: {str(e)}")
        
        # Now run the actual scraper
        st.write("**Now running the scraper in the background...**")
        
        # Run scraper command
        process = subprocess.Popen(
            [sys.executable, "run.py", "scraper"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=os.getcwd(),
            bufsize=1,
            universal_newlines=True
        )
        
        output_lines = []
        
        # Read output line by line
        for line in iter(process.stdout.readline, ''):
            if line:
                output_lines.append(line.strip())
                # Show last 10 lines
                recent_output = '\n'.join(output_lines[-10:])
                output_placeholder.text_area("Scraper Output", recent_output, height=200)
        
        process.wait()
        
        if process.returncode == 0:
            return True, "Scraper completed successfully! The Playwright browser has been closed automatically. Check the dashboard for scraped data."
        else:
            return False, f"Scraper failed with return code {process.returncode}"
            
    except Exception as e:
        return False, f"Error running scraper: {str(e)}"

def main():
    """Simple dashboard that reads directly from database"""
    st.title("📊 LeadTool Dashboard")
    st.markdown("Unified Lead Generation and Management System")
        
    
    # Show last scraping info
    st.sidebar.markdown("---")
    st.sidebar.subheader("Last Scraping")
    
    # Get last scraping time from database
    db = SessionLocal()
    try:
        last_scraping = db.query(MonthlyData).order_by(MonthlyData.scraped_at.desc()).first()
        if last_scraping:
            st.sidebar.info(f"Last run: {last_scraping.scraped_at.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.sidebar.info("No scraping data found")
    except Exception as e:
        st.sidebar.error(f"Error getting last scraping info: {e}")
    finally:
        db.close()
    
    # Add manual scraping options
    st.sidebar.markdown("---")
    st.sidebar.subheader("Manual Search")
    
    # Load current configuration
    config = load_config()
    current_queries = config.get('search_queries', [])
    
    # Add new search query form
    with st.sidebar.form("add_search_query"):
        st.write("**Add Search Query**")
        query_name = st.text_input("Query Name", placeholder="e.g., Restaurants in NYC")
        keywords = st.text_input("Keywords", placeholder="e.g., restaurants")
        location = st.text_input("Location", placeholder="e.g., New York, NY")
        
        if st.form_submit_button("Add Query"):
            if query_name and keywords and location:
                new_query = {
                    'name': query_name,
                    'keywords': keywords,
                    'location': location
                }
                current_queries.append(new_query)
                config['search_queries'] = current_queries
                save_config(config)
                st.success(f"Added: {query_name}")
                st.rerun()
            else:
                st.error("Please fill in all fields")
    
    # Display current queries
    if current_queries:
        st.sidebar.write("**Current Queries:**")
        for i, query in enumerate(current_queries):
            with st.sidebar.expander(f"{query.get('name', 'Unnamed')}"):
                st.write(f"Keywords: {query.get('keywords', 'N/A')}")
                st.write(f"Location: {query.get('location', 'N/A')}")
                if st.button("Delete", key=f"delete_{i}"):
                    current_queries.pop(i)
                    config['search_queries'] = current_queries
                    save_config(config)
                    st.rerun()
    
    # Scraper button
    if st.sidebar.button("🚀 Run Scraper", type="primary"):
        if not current_queries:
            st.sidebar.warning("Please add search queries first")
        else:
            with st.spinner("Running scraper..."):
                success, message = run_scraper()
                if success:
                    st.sidebar.success(message)
                    st.rerun()  # Refresh the page to show new data
                else:
                    st.sidebar.error(message)
    
    # Show query count
    st.sidebar.write(f"**Total Queries:** {len(current_queries)}")
    
    # Get data directly from database
    db = SessionLocal()
    try:
        # Get companies
        companies = db.query(Company).all()
        
        # Get contacts
        contacts = db.query(Contact).all()
        
        # Get monthly data
        monthly_data = db.query(MonthlyData).all()
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Companies", len(companies))
        
        with col2:
            st.metric("Total Contacts", len(contacts))
        
        with col3:
            contacts_with_phones = len([c for c in contacts if c.phone])
            st.metric("Contacts with Phones", contacts_with_phones)
        
        with col4:
            phone_rate = (contacts_with_phones / max(len(contacts), 1)) * 100
            st.metric("Phone Coverage", f"{phone_rate:.1f}%")
        
        # Display companies table
        st.subheader("Companies")
        if companies:
            company_data = []
            for company in companies:
                company_data.append({
                    "ID": company.id,
                    "Name": company.name,
                    "Category": company.category or "N/A",
                    "Address": company.address or "N/A",
                    "Website": company.website or "N/A",
                    "Phone": company.phone or "N/A",
                    "Rating": company.rating or "N/A",
                    "Review Count": company.review_count or "N/A",
                    "Source": company.source or "N/A"
                })
            
            df = pd.DataFrame(company_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No companies found")
        
        # Display monthly data
        st.subheader("Monthly Data")
        if monthly_data:
            monthly_data_list = []
            for data in monthly_data:
                monthly_data_list.append({
                    "ID": data.id,
                    "Company ID": data.company_id,
                    "Month": data.month_key,
                    "Type": data.data_type,
                    "Query": data.query_name or "N/A",
                    "Source URL": data.source_url or "N/A",
                    "Scraped At": data.scraped_at.strftime("%Y-%m-%d %H:%M:%S") if data.scraped_at else "N/A",
                    "Active": data.is_active
                })
            
            monthly_df = pd.DataFrame(monthly_data_list)
            st.dataframe(monthly_df, use_container_width=True)
        else:
            st.info("No monthly data found")
        
        # Charts
        if companies:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Companies by Category")
                if any(c.category for c in companies):
                    category_counts = {}
                    for company in companies:
                        if company.category:
                            category_counts[company.category] = category_counts.get(company.category, 0) + 1
                    
                    if category_counts:
                        fig = px.pie(
                            values=list(category_counts.values()),
                            names=list(category_counts.keys()),
                            title="Companies by Category"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No category data available")
                else:
                    st.info("No category data available")
            
            with col2:
                st.subheader("Companies by Source")
                source_counts = {}
                for company in companies:
                    source = company.source or "Unknown"
                    source_counts[source] = source_counts.get(source, 0) + 1
                
                if source_counts:
                    fig = px.bar(
                        x=list(source_counts.keys()),
                        y=list(source_counts.values()),
                        title="Companies by Source"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No source data available")
        
        # Scraping Status Section
        st.markdown("---")
        st.subheader("🕷️ Scraping Status")
        
        # Show scraping statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_scraped = len(monthly_data)
            st.metric("Total Scraped Items", total_scraped)
        
        with col2:
            active_items = len([d for d in monthly_data if d.is_active])
            st.metric("Active Items", active_items)
        
        with col3:
            unique_queries = len(set([d.query_name for d in monthly_data if d.query_name]))
            st.metric("Search Queries", unique_queries)
        
        # Show recent scraping activity
        if monthly_data:
            st.subheader("Recent Scraping Activity")
            recent_data = sorted(monthly_data, key=lambda x: x.scraped_at or datetime.min, reverse=True)[:10]
            
            activity_data = []
            for data in recent_data:
                activity_data.append({
                    "Time": data.scraped_at.strftime("%Y-%m-%d %H:%M:%S") if data.scraped_at else "Unknown",
                    "Query": data.query_name or "Unknown",
                    "Type": data.data_type,
                    "Active": "✅" if data.is_active else "❌"
                })
            
            activity_df = pd.DataFrame(activity_data)
            st.dataframe(activity_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
