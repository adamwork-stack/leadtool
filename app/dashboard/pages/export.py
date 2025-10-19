"""
Export page for LeadTool dashboard
"""
import streamlit as st
import requests
from datetime import datetime

API_BASE_URL = st.session_state.get("API_BASE_URL", "http://localhost:8000/api/v1")

def show_export():
    """Show export page content"""
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
