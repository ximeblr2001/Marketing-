import streamlit as st
import psycopg2
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# --- Database Connection ---
@st.cache_resource
def get_db_connection():
    """Establishes and caches a connection to the PostgreSQL database."""
    return psycopg2.connect(
        dbname="marketing_MR",
        user="postgres",
        password="Yash",
        host="localhost"
    )

# --- Helper Functions ---
def run_sql_query(query, params=None):
    """Executes a SQL query and returns the results as a DataFrame."""
    conn = get_db_connection()
    try:
        df = pd.read_sql(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

# --- Streamlit UI ---
st.set_page_config(layout="wide")
st.title("📈 Marketing Campaign Manager")

# --- Sidebar for Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Create Campaign", "Manage Campaigns", "Manage Customers"])

# --- Dashboard View ---
if page == "Dashboard":
    st.header("Campaign Performance Dashboard")
    df_campaigns = run_sql_query("SELECT campaign_id, name FROM campaign ORDER BY start_date DESC")
    if not df_campaigns.empty:
        campaign_name = st.selectbox("Select a Campaign", df_campaigns['name'])
        selected_campaign_id = df_campaigns[df_campaigns['name'] == campaign_name]['campaign_id'].iloc[0]
        
        # Fetch key metrics for the selected campaign
        df_performance = run_sql_query(f"""
            SELECT metric_name, SUM(metric_value) as total_value
            FROM performance_data pd
            JOIN campaign_channel cc ON pd.channel_id = cc.channel_id
            WHERE cc.campaign_id = {selected_campaign_id}
            GROUP BY metric_name;
        """)

        if not df_performance.empty:
            metrics = {row['metric_name']: row['total_value'] for _, row in df_performance.iterrows()}
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Emails Sent", metrics.get('Emails Sent', 0))
            with col2:
                st.metric("Open Rate (%)", f"{metrics.get('Open Rate', 0):.2f}%")
            with col3:
                st.metric("Click-Through Rate (%)", f"{metrics.get('Click-Through Rate', 0):.2f}%")

            # Visualize performance data with Plotly
            fig = px.bar(df_performance, x='metric_name', y='total_value', title='Key Performance Metrics')
            st.plotly_chart(fig)
        else:
            st.info("No performance data available for this campaign.")
    else:
        st.warning("No campaigns found. Please create one.")

# --- Create Campaign Page ---
elif page == "Create Campaign":
    st.header("Create a New Campaign")
    with st.form("create_campaign_form"):
        name = st.text_input("Campaign Name")
        budget = st.number_input("Budget", min_value=0.0, format="%.2f")
        start_date = st.date_input("Start Date", datetime.now().date())
        end_date = st.date_input("End Date", datetime.now().date())
        description = st.text_area("Description")
        
        submitted = st.form_submit_button("Create Campaign")
        if submitted:
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                # Assuming a single user with ID 1
                cursor.execute(
                    "INSERT INTO campaign (user_id, name, budget, start_date, end_date, description) VALUES (%s, %s, %s, %s, %s, %s);",
                    (1, name, budget, start_date, end_date, description)
                )
                conn.commit()
                st.success("Campaign created successfully!")
            except Exception as e:
                st.error(f"Failed to create campaign: {e}")
                conn.rollback()
            finally:
                cursor.close()

# --- Manage Campaigns Page ---
elif page == "Manage Campaigns":
    st.header("Manage Campaigns")
    df_campaigns = run_sql_query("SELECT * FROM campaign ORDER BY start_date DESC")
    if not df_campaigns.empty:
        st.dataframe(df_campaigns, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Update Campaign")
            campaign_id_to_update = st.number_input("Enter Campaign ID to update", min_value=1)
            # Add update form here (omitted for brevity)
        
        with col2:
            st.subheader("Delete Campaign")
            campaign_id_to_delete = st.number_input("Enter Campaign ID to delete", min_value=1)
            if st.button("Delete Campaign"):
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("DELETE FROM campaign WHERE campaign_id = %s", (campaign_id_to_delete,))
                    conn.commit()
                    st.success(f"Campaign {campaign_id_to_delete} deleted.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error deleting campaign: {e}")
                    conn.rollback()
                finally:
                    cursor.close()
    else:
        st.info("No campaigns to manage.")

# --- Customer Management ---
elif page == "Manage Customers":
    st.header("Manage Customers & Segments")
    df_customers = run_sql_query("SELECT * FROM customer")
    if not df_customers.empty:
        st.subheader("Customer Database")
        st.dataframe(df_customers, use_container_width=True)
    
    st.subheader("Create a New Customer")
    with st.form("create_customer_form"):
        name = st.text_input("Customer Name")
        email = st.text_input("Email")
        submitted_cust = st.form_submit_button("Add Customer")
        if submitted_cust:
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO customer (name, email) VALUES (%s, %s);", (name, email))
                conn.commit()
                st.success("Customer added successfully!")
            except Exception as e:
                st.error(f"Failed to add customer: {e}")
                conn.rollback()
            finally:
                cursor.close()
