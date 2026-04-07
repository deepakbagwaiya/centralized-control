import streamlit as st
import mysql.connector
import bcrypt
import pandas as pd
from datetime import datetime

# ==========================================
# 1. PAGE CONFIGURATION & SETUP
# ==========================================
st.set_page_config(page_title="Western Railway - Dashboard", page_icon="🚂", layout="wide")

# Initialize session state variables if they don't exist
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'user_id': '', 'userid': '', 'role': '', 
        'division': '', 'shed': '', 'mobile': '', 'email': ''
    })

# ==========================================
# 2. DATABASE CONNECTION (Replaces db.php)
# ==========================================
@st.cache_resource
def init_connection():
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

conn = init_connection()

# ==========================================
# 3. AUTH & PERMISSION LOGIC (Replaces auth.php)
# ==========================================
def can_edit():
    return st.session_state.role in ['superadmin', 'hq_user']

def can_access_module(module):
    role = st.session_state.role
    permissions = {
        'superadmin': ['PCEE', 'HQ/TLC', 'DIV/TLC', 'SHED', 'USER_MANAGEMENT', 'REPORTS'],
        'hq_user':    ['PCEE', 'HQ/TLC', 'DIV/TLC', 'SHED', 'REPORTS'],
        'admin':      ['PCEE', 'HQ/TLC', 'DIV/TLC', 'SHED', 'REPORTS'], 
        'tlc':        ['PCEE', 'DIV/TLC', 'REPORTS'],
        'shed':       ['PCEE', 'SHED', 'REPORTS'],
        'user':       ['PCEE', 'REPORTS']
    }
    return module in permissions.get(role, [])

def logout():
    st.session_state.clear()
    st.rerun()

# ==========================================
# 4. LOGIN SCREEN (Replaces login.php)
# ==========================================
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<h2 style='text-align: center; color: #004d99;'>Indian Railways</h2>", unsafe_allow_html=True)
        st.write("### Login")
        
        with st.form("login_form"):
            userid_input = st.text_input("User ID")
            password_input = st.text_input("Password", type="password")
            submit_btn = st.form_submit_button("Login", use_container_width=True)
            
            if submit_btn:
                if conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT id, userid, password, role, division, shed FROM users WHERE userid = %s", (userid_input,))
                    user = cursor.fetchone()
                    
                    if user and bcrypt.checkpw(password_input.encode('utf-8'), user['password'].encode('utf-8')):
                        st.session_state.update({
                            'logged_in': True,
                            'user_id': user['id'],
                            'userid': user['userid'],
                            'role': user['role'],
                            'division': user['division'],
                            'shed': user['shed']
                        })
                        st.rerun()
                    else:
                        st.error("Invalid User ID or Password.")

# ==========================================
# 5. MAIN DASHBOARD (Replaces dashboard.php)
# ==========================================
else:
    # --- SIDEBAR MENU ---
    with st.sidebar:
        st.markdown("## WR MENU")
        st.markdown(f"**User:** {st.session_state.userid}")
        st.markdown(f"**Role:** {st.session_state.role.upper()}")
        if st.session_state.shed: st.markdown(f"**Shed:** {st.session_state.shed}")
        
        if can_edit():
            st.success("✏️ EDIT ACCESS")
        else:
            st.info("👁️ READ ONLY")
            
        st.divider()
        
        # Navigation (In Streamlit, you usually use a selectbox for "pages" if staying in one script)
        page = st.radio("Navigation", ["Dashboard", "Reports", "Manage Users"])
        
        st.divider()
        if st.button("↻ Logout", use_container_width=True):
            logout()

    # --- DASHBOARD CONTENT ---
    if page == "Dashboard":
        st.title("🚂 WESTERN RAILWAY - LOCO CONTROL")
        st.caption("Real-time Locomotive Monitoring & Management System")

        selected_date = st.date_input("Select Date", datetime.today())

        # Fetch Data
        if conn:
            cursor = conn.cursor(dictionary=True)
            
            # Fetch Holding
            cursor.execute("""
                SELECT SUM(total_holding) as val FROM outage_domain_service 
                WHERE table_name = 'OUTAGE_141_GOODS' 
                AND entry_date = (SELECT MAX(entry_date) FROM outage_domain_service WHERE table_name = 'OUTAGE_141_GOODS')
            """)
            wr_holding = cursor.fetchone()['val'] or 0

            # Fetch 141 Goods
            cursor.execute("SELECT SUM(value) as val FROM outage_domain_service WHERE entry_date = %s AND table_name = 'OUTAGE_141_GOODS'", (selected_date,))
            outage_141_goods = cursor.fetchone()['val'] or 0

            # Fetch 229 Goods
            cursor.execute("SELECT SUM(value) as val FROM outage_domain_service WHERE entry_date = %s AND table_name = 'OUTAGE_229_GOODS'", (selected_date,))
            outage_229_goods = cursor.fetchone()['val'] or 0

            # Fetch Territorial Outage
            cursor.execute("SELECT metric_name, total FROM territorial_outage WHERE entry_date = %s", (selected_date,))
            outage_data = {row['metric_name']: row['total'] for row in cursor.fetchall()}
            
            freight = outage_data.get('freight_outage', 0)
            coaching = outage_data.get('coaching_outage', 0)
            inferior = outage_data.get('inferior', 0)

            # Fetch Loco in Shed
            cursor.execute("SELECT SUM(total) as val FROM ineffective_midnight_count WHERE entry_date = %s", (selected_date,))
            loco_shed = cursor.fetchone()['val'] or 0
            
            # Display Metrics
            st.subheader(f"📊 Detailed Statistics ({selected_date.strftime('%d-%m-%Y')})")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("WR Holding", wr_holding)
            col2.metric("141 Goods", outage_141_goods)
            col3.metric("229 Goods", outage_229_goods)
            col4.metric("Loco in Shed", loco_shed)

            col5, col6, col7, col8 = st.columns(4)
            col5.metric("Freight Outage", freight)
            col6.metric("Coaching Outage", coaching)
            col7.metric("Inferior", inferior)
            
    elif page == "Reports":
        if can_access_module('REPORTS'):
            st.title("📄 Reports")
            st.write("Report module coming soon...")
        else:
            st.error("🚫 Access Denied: You do not have permission to view Reports.")
            
    elif page == "Manage Users":
        if can_access_module('USER_MANAGEMENT'):
            st.title("👥 Manage Users")
            st.write("User management module coming soon...")
        else:
            st.error("🚫 Access Denied: Only superadmins can manage users.")