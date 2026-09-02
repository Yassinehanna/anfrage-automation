"""
Streamlit web interface for ANFRAGE Automation 2.0
Multi-user web application for sending German apprenticeship inquiries
"""

import streamlit as st
import os
import time
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import db
import core
from categories import CATEGORIES, ALL_BERUFE

# Configuration from environment variables
DELAY = int(os.getenv('DELAY', '5'))
BOUNCE_CHECK_EVERY = int(os.getenv('BOUNCE_CHECK_EVERY', '20'))
DATABASE_PATH = os.getenv('DATABASE_PATH', 'anfrage.db')

# Session management
if 'session_token' not in st.session_state:
    st.session_state.session_token = None
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# Page configuration
st.set_page_config(
    page_title="ANFRAGE Automation",
    page_icon="🇩🇪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1F3864;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #E2EFDA;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4CAF50;
    }
    .warning-box {
        background-color: #FFF3CD;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #FFC107;
    }
    .error-box {
        background-color: #FCE4D6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #F44336;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'job_running' not in st.session_state:
    st.session_state.job_running = False
if 'job_results' not in st.session_state:
    st.session_state.job_results = None

def check_database():
    """Check if database exists and is accessible, create if needed"""
    # Try to initialize database if it doesn't exist
    try:
        if not os.path.exists(db.DB_PATH):
            # Try to create database automatically
            db.init_db()
            st.success("✅ Database initialized automatically!")
            return True
        return True
    except Exception as e:
        st.error(f"❌ Database error: {e}")
        if st.button("🔧 Try to Initialize Database"):
            try:
                db.init_db()
                st.success("✅ Database initialized successfully!")
                st.rerun()
            except Exception as e2:
                st.error(f"❌ Failed to initialize database: {e2}")
        return False

def login_page():
    """Login page for existing users"""
    st.markdown('<h1 class="main-header">🇩🇪 ANFRAGE Automation</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("🔐 Login")
        
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        if st.button("Login", type="primary"):
            if not username or not password:
                st.error("❌ Please enter both username and password")
                return
            
            with db.get_conn() as conn:
                user = db.authenticate_user(conn, username, password)
                
                if user:
                    # Create session
                    session_token = db.create_session(conn, user['id'])
                    st.session_state.session_token = session_token
                    st.session_state.current_user = user
                    st.session_state.is_admin = bool(user.get('is_admin', 0))
                    st.session_state.page = 'dashboard'
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
        
        st.markdown("---")
        st.text("Don't have an account?")
        if st.button("Register new account"):
            st.session_state.page = 'register'
            st.rerun()

def register_page():
    """Registration page for new users"""
    st.markdown('<h1 class="main-header">🇩🇪 ANFRAGE Automation</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("� Create New Account")
        
        username = st.text_input("Username", placeholder="Choose a username")
        password = st.text_input("Password", type="password", placeholder="Choose a password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        name = st.text_input("Full Name", placeholder="Your full name")
        gmail_address = st.text_input("Gmail Address", placeholder="your@gmail.com")
        gmail_app_pass = st.text_input("Gmail App Password", type="password", placeholder="16-char app password from Google")
        
        if st.button("Create Account", type="primary"):
            # Validation
            if not all([username, password, confirm_password, name, gmail_address, gmail_app_pass]):
                st.error("❌ Please fill in all fields")
                return
            
            if password != confirm_password:
                st.error("❌ Passwords do not match")
                return
            
            if len(password) < 6:
                st.error("❌ Password must be at least 6 characters")
                return
            
            if len(gmail_app_pass) != 16:
                st.warning("⚠️ Gmail App Password should be 16 characters")
            
            # Create user
            try:
                with db.get_conn() as conn:
                    user_id = db.create_user(conn, username, password, name, gmail_address, gmail_app_pass)
                    st.success(f"✅ Account created successfully for {name}!")
                    st.info("👉 Please login with your new credentials")
                    st.session_state.page = 'login'
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to create account: {e}")
                if "UNIQUE constraint" in str(e):
                    st.error("Username or Gmail address already exists")
        
        st.markdown("---")
        st.text("Already have an account?")
        if st.button("Back to Login"):
            st.session_state.page = 'login'
            st.rerun()

def dashboard():
    """Main dashboard for authenticated users"""
    user = st.session_state.current_user
    
    # Header with user info and logout
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
        <h1 style="color: #1F3864; margin: 0;">🇩🇪 ANFRAGE Automation</h1>
        <div style="text-align: right;">
            <p style="margin: 0; font-weight: bold;">{user['name']}</p>
            <p style="margin: 0; color: #666;">{user['gmail_address']}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Logout button
    if st.button("🚪 Logout"):
        with db.get_conn() as conn:
            if st.session_state.session_token:
                db.delete_session(conn, st.session_state.session_token)
        st.session_state.session_token = None
        st.session_state.current_user = None
        st.session_state.is_admin = False
        st.session_state.page = 'login'
        st.rerun()
    
    # Admin button (only for admin users)
    if st.session_state.is_admin:
        st.markdown("---")
        if st.button("👨‍💼 Admin Dashboard"):
            st.session_state.page = 'admin'
            st.rerun()
    
    st.markdown("---")
    
    # Initialize session state for selections if not exists
    if 'selected_beruf' not in st.session_state:
        st.session_state.selected_beruf = None
    if 'selected_region' not in st.session_state:
        st.session_state.selected_region = None
    if 'target_emails' not in st.session_state:
        st.session_state.target_emails = 5
    
    # Beruf selection
    st.subheader("📋 Ausbildung Category")
    cat_options = {k: v['label'] for k, v in CATEGORIES.items()}
    cat_choice = st.selectbox("Select category:", cat_options.values())
    
    # Get selected category
    cat_key = next(k for k, v in cat_options.items() if v == cat_choice)
    category = CATEGORIES[cat_key]
    
    # Beruf selection within category
    st.subheader("🔧 Specific Profession")
    beruf_options = {k: v['beruf'] for k, v in category['berufe'].items()}
    beruf_choice = st.selectbox("Select profession:", beruf_options.values())
    
    # Get selected beruf
    beruf_key = next(k for k, v in beruf_options.items() if v == beruf_choice)
    beruf = category['berufe'][beruf_key]
    
    # Show coverage warning if weak
    if beruf['coverage'] == 'weak':
        st.warning("⚠️ Note: OpenStreetMap has weaker coverage for this trade - expect fewer/noisier results.")
    
    # Region selection
    st.subheader("🌍 German Region")
    BUNDESLAENDER = [
        "Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen",
        "Hamburg", "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen",
        "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland", "Sachsen",
        "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen",
    ]
    
    region_choice = st.selectbox("Select German state:", BUNDESLAENDER)
    custom_region = st.text_input("Or type a specific city:", "")
    
    region = custom_region if custom_region else region_choice
    
    # Email target
    st.subheader("🎯 Session Settings")
    target_emails = st.number_input("How many emails to send this session?", 
                                   min_value=1, max_value=500, value=5, step=1)
    
    # Preview email
    st.subheader("📧 Email Preview")
    email_body = beruf['body'].format(name=user['name'])
    st.text_area("Email that will be sent:", email_body, height=150, disabled=True)
    
    # Start button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 Start Sending Emails", type="primary", disabled=st.session_state.job_running):
            # Store selections in session state
            st.session_state.selected_beruf = beruf
            st.session_state.selected_region = region
            st.session_state.target_emails = target_emails
            st.session_state.job_running = True
            st.session_state.job_results = None
            st.rerun()
    


def run_job():
    """Execute the email sending job"""
    user = st.session_state.current_user
    beruf = st.session_state.selected_beruf
    region = st.session_state.selected_region
    target = st.session_state.target_emails
    
    # Progress display
    progress_container = st.container()
    status_container = st.container()
    
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    with status_container:
        log_area = st.empty()
    
    def progress_callback(progress, message):
        progress_bar.progress(progress)
        status_text.text(message)
        log_area.text(message)
    
    try:
        with db.get_conn() as conn:
            result = core.run_with_progress(
                conn, user, beruf, region, target,
                progress_callback=progress_callback
            )
        
        st.session_state.job_results = result
        st.session_state.job_running = False
        
    except Exception as e:
        st.error(f"❌ Error during job execution: {e}")
        st.session_state.job_running = False
    
    st.rerun()

def show_results():
    """Display job results"""
    result = st.session_state.job_results
    user = st.session_state.current_user
    
    st.markdown("---")
    st.subheader("📊 Session Results")
    
    # Summary cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("✅ Sent", result.get('sent', 0))
    with col2:
        st.metric("❌ Failed", result.get('failed', 0))
    with col3:
        st.metric("⏭️ Skipped", result.get('skipped', 0))
    with col4:
        st.metric("🔍 No Email", result.get('no_email', 0))
    
    if result.get('stopped'):
        st.warning(f"⚠️ Session stopped early: {result['stopped']}")
    
    # Show recent contacts
    st.subheader("📋 Recent Contact History")
    try:
        with db.get_conn() as conn:
            recent_contacts = conn.execute("""
                SELECT company_name, email, beruf, region, status, sent_at 
                FROM contacts 
                WHERE user_id = ? 
                ORDER BY sent_at DESC 
                LIMIT 10
            """, (user['id'],)).fetchall()
            
            if recent_contacts:
                df = pd.DataFrame([dict(c) for c in recent_contacts])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No recent contacts found.")
    except Exception as e:
        st.error(f"Error loading contact history: {e}")
    
    # New session button
    if st.button("🔄 Start New Session"):
        st.session_state.job_results = None
        st.rerun()

def admin_dashboard():
    """Admin dashboard to view all users and system statistics"""
    st.markdown('<h1 class="main-header">👨‍💼 Admin Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # System statistics
    st.subheader("📊 System Statistics")
    try:
        with db.get_conn() as conn:
            stats = db.get_system_stats(conn)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Users", stats.get('total_users', 0))
            with col2:
                st.metric("Total Emails Sent", stats.get('total_emails', 0))
            with col3:
                st.metric("Companies in Database", stats.get('total_companies', 0))
            with col4:
                st.metric("Blocked Domains", stats.get('blocked_domains', 0))
    except Exception as e:
        st.error(f"Error loading system statistics: {e}")
    
    st.markdown("---")
    
    # User management
    st.subheader("👥 Registered Users")
    try:
        with db.get_conn() as conn:
            users = db.get_all_users(conn)
            
            if users:
                user_data = []
                for user in users:
                    user_dict = dict(user)
                    # Get individual user stats
                    user_stats = db.get_user_stats(conn, user['id'])
                    user_dict.update(user_stats)
                    user_data.append(user_dict)
                
                df = pd.DataFrame(user_data)
                
                # Display columns
                display_columns = ['username', 'name', 'gmail_address', 'total_emails', 'sent', 'failed', 'bounced', 'last_sent']
                available_columns = [col for col in display_columns if col in df.columns]
                
                if available_columns:
                    # Rename columns for better display
                    column_mapping = {
                        'username': 'Username',
                        'name': 'Full Name', 
                        'gmail_address': 'Gmail',
                        'total_emails': 'Total Emails',
                        'sent': 'Sent',
                        'failed': 'Failed',
                        'bounced': 'Bounced',
                        'last_sent': 'Last Activity'
                    }
                    df_display = df[available_columns].rename(columns=column_mapping)
                    st.dataframe(df_display, use_container_width=True)
                else:
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("No users registered yet.")
    except Exception as e:
        st.error(f"Error loading user data: {e}")
    
    st.markdown("---")
    
    # Recent activity
    st.subheader("📋 Recent Email Activity")
    try:
        with db.get_conn() as conn:
            recent_contacts = conn.execute("""
                SELECT c.*, u.username, u.name as user_name
                FROM contacts c
                JOIN users u ON c.user_id = u.id
                ORDER BY c.sent_at DESC
                LIMIT 20
            """).fetchall()
            
            if recent_contacts:
                df = pd.DataFrame([dict(c) for c in recent_contacts])
                display_cols = ['username', 'user_name', 'company_name', 'email', 'beruf', 'region', 'status', 'sent_at']
                available_cols = [col for col in display_cols if col in df.columns]
                
                if available_cols:
                    col_mapping = {
                        'username': 'Username',
                        'user_name': 'Name',
                        'company_name': 'Company',
                        'email': 'Email',
                        'beruf': 'Profession',
                        'region': 'Region',
                        'status': 'Status',
                        'sent_at': 'Date'
                    }
                    df_display = df[available_cols].rename(columns=col_mapping)
                    st.dataframe(df_display, use_container_width=True)
            else:
                st.info("No email activity yet.")
    except Exception as e:
        st.error(f"Error loading recent activity: {e}")
    
    st.markdown("---")
    
    # Back to dashboard
    if st.button("🔙 Back to My Dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()

def main():
    """Main application flow"""
    # Check database
    if not check_database():
        st.stop()
    
    # Page routing
    if st.session_state.page == 'login':
        login_page()
    elif st.session_state.page == 'register':
        register_page()
    elif st.session_state.page == 'dashboard':
        # Check if user is authenticated
        if st.session_state.current_user is None:
            st.session_state.page = 'login'
            st.rerun()
        else:
            # Dashboard flow
            if 'selected_beruf' not in st.session_state:
                st.session_state.selected_beruf = None
            if 'selected_region' not in st.session_state:
                st.session_state.selected_region = None
            if 'target_emails' not in st.session_state:
                st.session_state.target_emails = 5
            
            if st.session_state.job_running:
                # Currently running a job
                if st.session_state.selected_beruf and st.session_state.selected_region:
                    run_job()
                else:
                    st.error("❌ Missing job configuration. Please select a profession and region.")
                    st.session_state.job_running = False
                    st.rerun()
            elif st.session_state.job_results:
                # Show results
                dashboard()
                show_results()
            else:
                # Main dashboard
                dashboard()
    elif st.session_state.page == 'admin':
        # Check if user is admin
        if st.session_state.current_user is None or not st.session_state.is_admin:
            st.error("❌ Access denied. Admin privileges required.")
            st.session_state.page = 'dashboard'
            st.rerun()
        else:
            admin_dashboard()
    else:
        # Default to login page
        st.session_state.page = 'login'
        st.rerun()


if __name__ == "__main__":
    main()