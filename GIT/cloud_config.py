"""
Cloud configuration for free deployment
Use this configuration for Streamlit Community Cloud or other free hosting
"""

import os
import tempfile

# For cloud deployment, use a temporary directory that persists during the session
# Note: This will reset between deployments, but works for free hosting
if os.environ.get('STREAMLIT_CLOUD') or os.environ.get('VERCEL') or os.environ.get('REPLIT'):
    # We're on a cloud platform
    BASE_DIR = tempfile.gettempdir()
    DATABASE_PATH = os.path.join(BASE_DIR, 'anfrage.db')
else:
    # Local development
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, 'anfrage.db')

# Other configuration
DELAY = int(os.getenv('DELAY', '5'))
BOUNCE_CHECK_EVERY = int(os.getenv('BOUNCE_CHECK_EVERY', '20'))

# For Streamlit Community Cloud, we need to handle database initialization
def ensure_database_exists():
    """Ensure database exists, create if it doesn't"""
    if not os.path.exists(DATABASE_PATH):
        import db
        print(f"Creating database at {DATABASE_PATH}")
        db.init_db(db_path=DATABASE_PATH)
        print("Database created successfully")

# Auto-initialize database on import
try:
    ensure_database_exists()
except Exception as e:
    print(f"Warning: Could not auto-initialize database: {e}")