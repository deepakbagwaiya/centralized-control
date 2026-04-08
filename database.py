import mysql.connector
import streamlit as st
import certifi

@st.cache_resource
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=st.secrets["DB_HOST"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASS"],
            database=st.secrets["DB_NAME"],
            port=st.secrets["DB_PORT"],
            ssl_verify_cert=True,
            ssl_verify_identity=True,
            ssl_ca=certifi.where()   # <--- This securely verifies the connection!
        )
    except mysql.connector.Error as err:
        st.error(f"Database connection failed: {err}")
        return None