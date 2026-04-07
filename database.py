import mysql.connector
import streamlit as st

@st.cache_resource
def get_db_connection():
    try:
        return mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="",
            database="deeprail",
            port=3306
        )
    except mysql.connector.Error as err:
        st.error(f"Database connection failed: {err}")
        return None