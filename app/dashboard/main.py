"""
Streamlit dashboard for LeadTool
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Configure page
st.set_page_config(
    page_title="LeadTool Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

def main():
    """Main dashboard application"""
    st.title("📊 LeadTool Dashboard")
    st.markdown("Unified Lead Generation and Management System")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Overview", "Search & Filter", "Export Data"]
    )
    
    # Route to appropriate page
    if page == "Overview":
        show_overview()
    elif page == "Search & Filter":
        show_search()
    else:
        show_export()

def show_overview():
    """Overview tab with metrics and charts"""
    st.header("📈 Overview")
    
    # Get statistics
    try:
        # Company stats
        company_stats = requests.get(f"{API_BASE_URL}/companies/stats").json()
        
        # Contact stats
        contact_stats = requests.get(f"{API_BASE_URL}/contacts/stats").json()
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Companies",
                value=company_stats.get("total_companies", 0)
            )
        
        with col2:
            st.metric(
                label="Total Contacts",
                value=contact_stats.get("total_contacts", 0)
            )
        
        with col3:
            st.metric(
                label="Contacts with Phones",
                value=contact_stats.get("contacts_with_phones", 0)
            )
        
        with col4:
            phone_rate = (contact_stats.get("contacts_with_phones", 0) / 
                         max(contact_stats.get("total_contacts", 1), 1)) * 100
            st.metric(
                label="Phone Coverage",
                value=f"{phone_rate:.1f}%"
            )
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Companies by Industry")
            if company_stats.get("by_industry"):
                industry_df = pd.DataFrame(company_stats["by_industry"])
                fig = px.pie(
                    industry_df, 
                    values='count', 
                    names='industry',
                    title="Company Distribution by Industry"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No industry data available")
        
        with col2:
            st.subheader("Companies by Location")
            if company_stats.get("by_location"):
                location_df = pd.DataFrame(company_stats["by_location"])
                fig = px.bar(
                    location_df, 
                    x='location', 
                    y='count',
                    title="Companies by Location"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No location data available")
        
        # Contact charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Contacts by Title")
            if contact_stats.get("by_title"):
                title_df = pd.DataFrame(contact_stats["by_title"])
                fig = px.bar(
                    title_df, 
                    x='title', 
                    y='count',
                    title="Contacts by Job Title"
                )
                fig.update_xaxis(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No title data available")
        
        with col2:
            st.subheader("Contacts by Department")
            if contact_stats.get("by_department"):
                dept_df = pd.DataFrame(contact_stats["by_department"])
                fig = px.pie(
                    dept_df, 
                    values='count', 
                    names='department',
                    title="Contact Distribution by Department"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No department data available")
        
    except Exception as e:
        st.error(f"Error loading overview data: {e}")
        st.info("Make sure the API server is running on http://localhost:8000")

def show_search():
    """Search and filter tab"""
    st.header("🔍 Search & Filter")
    
    # Search form
    with st.form("search_form"):
        st.subheader("Search Companies")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Company Name")
            domain = st.text_input("Domain")
            industry = st.text_input("Industry")
        
        with col2:
            location = st.text_input("Location")
            month_key = st.text_input("Month Key (e.g., 2025-01)", 
                                    value=datetime.now().strftime("%Y-%m"))
        
        search_button = st.form_submit_button("Search")
        
        if search_button:
            try:
                # Build query parameters
                params = {}
                if name:
                    params["name"] = name
                if domain:
                    params["domain"] = domain
                if industry:
                    params["industry"] = industry
                if location:
                    params["location"] = location
                if month_key:
                    params["month_key"] = month_key
                
                # Get companies
                response = requests.get(f"{API_BASE_URL}/companies", params=params)
                companies = response.json()
                
                if companies:
                    st.success(f"Found {len(companies)} companies")
                    
                    # Display results
                    for company in companies:
                        with st.expander(f"{company['name']} - {company.get('domain', 'No domain')}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Industry:** {company.get('industry', 'N/A')}")
                                st.write(f"**Location:** {company.get('location', 'N/A')}")
                                st.write(f"**Website:** {company.get('website', 'N/A')}")
                            
                            with col2:
                                st.write(f"**Size:** {company.get('size', 'N/A')}")
                                st.write(f"**Created:** {company.get('created_at', 'N/A')}")
                                if company.get('description'):
                                    st.write(f"**Description:** {company['description']}")
                else:
                    st.info("No companies found matching your criteria")
                    
            except Exception as e:
                st.error(f"Error searching companies: {e}")
    
    # Contact search
    st.subheader("Search Contacts")
    
    with st.form("contact_search_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            contact_phone = st.text_input("Phone")
            contact_company_id = st.number_input("Company ID", min_value=1, value=None)
        
        with col2:
            contact_title = st.text_input("Job Title")
            contact_department = st.text_input("Department")
        
        contact_search_button = st.form_submit_button("Search Contacts")
        
        if contact_search_button:
            try:
                # Build query parameters
                params = {}
                if contact_phone:
                    params["phone"] = contact_phone
                if contact_company_id:
                    params["company_id"] = contact_company_id
                if contact_title:
                    params["title"] = contact_title
                if contact_department:
                    params["department"] = contact_department
                
                # Get contacts
                response = requests.get(f"{API_BASE_URL}/contacts", params=params)
                contacts = response.json()
                
                if contacts:
                    st.success(f"Found {len(contacts)} contacts")
                    
                    # Display results in a table
                    contact_data = []
                    for contact in contacts:
                        contact_data.append({
                            "ID": contact["id"],
                            "Phone": contact.get("phone", ""),
                            "Name": f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
                            "Title": contact.get("title", ""),
                            "Department": contact.get("department", ""),
                            "Company ID": contact["company_id"],
                            "Primary": contact.get("is_primary", False)
                        })
                    
                    df = pd.DataFrame(contact_data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No contacts found matching your criteria")
                    
            except Exception as e:
                st.error(f"Error searching contacts: {e}")

def show_export():
    """Export data tab"""
    st.header("📤 Export Data")
    
    # Export options
    st.subheader("Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_type = st.selectbox(
            "Data Type",
            ["Companies", "Contacts", "Combined Data"]
        )
        
        export_format = st.selectbox(
            "Format",
            ["CSV", "Excel"]
        )
    
    with col2:
        month_filter = st.text_input(
            "Month Filter (optional)", 
            value=datetime.now().strftime("%Y-%m"),
            help="Leave empty to export all data"
        )
    
    # Additional filters for companies
    if export_type == "Companies":
        st.subheader("Company Filters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("Company Name Filter")
            company_domain = st.text_input("Domain Filter")
        
        with col2:
            company_industry = st.text_input("Industry Filter")
            company_location = st.text_input("Location Filter")
    
    # Additional filters for contacts
    elif export_type == "Contacts":
        st.subheader("Contact Filters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            contact_phone = st.text_input("Phone Filter")
            contact_title = st.text_input("Title Filter")
        
        with col2:
            contact_department = st.text_input("Department Filter")
            is_primary = st.selectbox("Primary Contact", ["All", "Yes", "No"])
    
    # Export button
    if st.button("Export Data", type="primary"):
        try:
            # Build export URL
            if export_type == "Companies":
                url = f"{API_BASE_URL}/export/companies"
                params = {
                    "format": export_format.lower()
                }
                if month_filter:
                    params["month_key"] = month_filter
                if company_name:
                    params["name"] = company_name
                if company_domain:
                    params["domain"] = company_domain
                if company_industry:
                    params["industry"] = company_industry
                if company_location:
                    params["location"] = company_location
                    
            elif export_type == "Contacts":
                url = f"{API_BASE_URL}/export/contacts"
                params = {
                    "format": export_format.lower()
                }
                if contact_phone:
                    params["phone"] = contact_phone
                if contact_title:
                    params["title"] = contact_title
                if contact_department:
                    params["department"] = contact_department
                if is_primary != "All":
                    params["is_primary"] = is_primary == "Yes"
                    
            else:  # Combined
                url = f"{API_BASE_URL}/export/combined"
                params = {
                    "format": export_format.lower()
                }
                if month_filter:
                    params["month_key"] = month_filter
            
            # Make request
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                # Get filename
                filename = f"{export_type.lower().replace(' ', '_')}.{export_format.lower()}"
                if export_format.lower() == "excel":
                    filename = filename.replace("csv", "xlsx")
                
                # Download file
                st.download_button(
                    label=f"Download {filename}",
                    data=response.content,
                    file_name=filename,
                    mime="application/octet-stream"
                )
                
                st.success("Export ready for download!")
            else:
                st.error(f"Export failed: {response.text}")
                
        except Exception as e:
            st.error(f"Error exporting data: {e}")

if __name__ == "__main__":
    main()
