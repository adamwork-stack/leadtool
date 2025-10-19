"""
Search page for LeadTool dashboard
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_BASE_URL = st.session_state.get("API_BASE_URL", "http://localhost:8000/api/v1")

def show_search():
    """Show search page content"""
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
