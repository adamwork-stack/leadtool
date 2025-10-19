"""
Overview page for LeadTool dashboard
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

API_BASE_URL = st.session_state.get("API_BASE_URL", "http://localhost:8000/api/v1")

def show_overview():
    """Show overview page content"""
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
