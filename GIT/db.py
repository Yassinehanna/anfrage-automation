"""
Data access layer. SQLite for now (zero infra for a friend-group tool) --
swapping to Postgres later means changing this file and schema.sql, not
anything in core.py.
"""

import sqlite3
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from contextlib import contextmanager

# Try to import cloud configuration, fall back to local
try:
    from cloud_config import DATABASE_PATH as DB_PATH
except ImportError:
    DB_PATH = os.getenv('DATABASE_PATH', 'anfrage.db')


# ==================== Authentication Functions ====================

def hash_password(password):
    """Hash a password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${password_hash}"

def verify_password(password, password_hash):
    """Verify a password against its hash"""
    try:
        salt, hash = password_hash.split('$')
        computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return computed_hash == hash
    except:
        return False

def generate_session_token():
    """Generate a secure random session token"""
    return secrets.token_urlsafe(32)


def init_db(schema_path="schema.sql", db_path=DB_PATH):
    """Initialize database with schema"""
    # Make sure the directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    with open(schema_path) as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


@contextmanager
def get_conn(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ---------- users ----------

def get_user(conn, user_id):
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

def get_user_by_username(conn, username):
    return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

def create_user(conn, username, password, name, gmail_address, gmail_app_pass, is_admin=False):
    password_hash = hash_password(password)
    cur = conn.execute(
        "INSERT INTO users (username, password_hash, name, gmail_address, gmail_app_pass, is_admin) VALUES (?, ?, ?, ?, ?, ?)",
        (username, password_hash, name, gmail_address, gmail_app_pass, 1 if is_admin else 0),
    )
    return cur.lastrowid

def authenticate_user(conn, username, password):
    """Authenticate user and return user dict if successful, None otherwise"""
    user = get_user_by_username(conn, username)
    if user and verify_password(password, user['password_hash']):
        return dict(user)
    return None

# ---------- sessions ----------

def create_session(conn, user_id, expires_hours=24):
    """Create a new session for a user"""
    session_token = generate_session_token()
    expires_at = (datetime.now() + timedelta(hours=expires_hours)).strftime('%Y-%m-%d %H:%M:%S')
    cur = conn.execute(
        "INSERT INTO sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)",
        (user_id, session_token, expires_at)
    )
    return session_token

def validate_session(conn, session_token):
    """Validate a session token and return user if valid, None otherwise"""
    session = conn.execute(
        """SELECT s.*, u.* FROM sessions s 
           JOIN users u ON s.user_id = u.id 
           WHERE s.session_token = ? AND s.expires_at > datetime('now')""",
        (session_token,)
    ).fetchone()
    
    if session:
        return dict(session)
    return None

def delete_session(conn, session_token):
    """Delete a session (logout)"""
    conn.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))

def cleanup_expired_sessions(conn):
    """Clean up expired sessions"""
    conn.execute("DELETE FROM sessions WHERE expires_at < datetime('now')")

# ---------- admin functions ----------

def get_all_users(conn):
    """Get all users (admin only)"""
    return conn.execute("""
        SELECT id, username, name, gmail_address, is_admin, created_at 
        FROM users 
        ORDER BY created_at DESC
    """).fetchall()

def get_user_stats(conn, user_id):
    """Get statistics for a specific user"""
    stats = conn.execute("""
        SELECT 
            COUNT(*) as total_emails,
            SUM(CASE WHEN status = 'Sent' THEN 1 ELSE 0 END) as sent,
            SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed,
            SUM(CASE WHEN status = 'Bounced' THEN 1 ELSE 0 END) as bounced,
            SUM(CASE WHEN status = 'Skipped' THEN 1 ELSE 0 END) as skipped,
            MAX(sent_at) as last_sent
        FROM contacts 
        WHERE user_id = ?
    """, (user_id,)).fetchone()
    return dict(stats) if stats else {}

def get_system_stats(conn):
    """Get overall system statistics"""
    stats = conn.execute("""
        SELECT 
            (SELECT COUNT(*) FROM users) as total_users,
            (SELECT COUNT(*) FROM contacts) as total_emails,
            (SELECT COUNT(*) FROM companies) as total_companies,
            (SELECT COUNT(*) FROM blocked_domains) as blocked_domains
    """).fetchone()
    return dict(stats) if stats else {}


# ---------- companies cache (shared across users) ----------

def get_cached_companies(conn, beruf, region, max_age_days=7):
    """Returns cached rows for (beruf, region) if fresh enough, else []."""
    rows = conn.execute(
        """SELECT * FROM companies
           WHERE beruf = ? AND region = ?
           AND fetched_at >= datetime('now', ?)""",
        (beruf, region, f"-{max_age_days} days"),
    ).fetchall()
    return rows


def store_companies(conn, beruf, region, rows):
    """rows: list of dicts with name/website/email/phone/city."""
    for r in rows:
        conn.execute(
            """INSERT INTO companies (beruf, region, name, website, email, phone, city, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
               ON CONFLICT(beruf, region, name) DO UPDATE SET
                 website=excluded.website, email=excluded.email,
                 phone=excluded.phone, city=excluded.city,
                 fetched_at=excluded.fetched_at""",
            (beruf, region, r["name"], r.get("website", ""), r.get("email", ""),
             r.get("phone", ""), r.get("city", "")),
        )


# ---------- resolved email cache (shared across users) ----------

def get_resolved_email(conn, company_id):
    """Returns the row if this company's email was already looked up by
    ANY user's run before (direct, scraped, or confirmed 'none') --
    None if nobody has ever tried yet."""
    return conn.execute(
        "SELECT * FROM resolved_emails WHERE company_id = ?", (company_id,)
    ).fetchone()


def store_resolved_email(conn, company_id, email, source):
    conn.execute(
        """INSERT INTO resolved_emails (company_id, email, source)
           VALUES (?, ?, ?)
           ON CONFLICT(company_id) DO UPDATE SET
             email=excluded.email, source=excluded.source,
             resolved_at=datetime('now')""",
        (company_id, email, source),
    )


# ---------- blocklist (shared across users, automatic) ----------

def is_domain_blocked(conn, email):
    domain = email.split("@")[-1].lower()
    row = conn.execute(
        "SELECT 1 FROM blocked_domains WHERE domain = ?", (domain,)
    ).fetchone()
    return row is not None


def block_domain(conn, email, reason):
    """reason: 'bounced' | 'complaint'. Called automatically -- no manual
    review step, per the product decision."""
    domain = email.split("@")[-1].lower()
    conn.execute(
        """INSERT INTO blocked_domains (domain, reason)
           VALUES (?, ?)
           ON CONFLICT(domain) DO NOTHING""",
        (domain, reason),
    )


# ---------- contacts (per-user local + global dedup, replaces both .xlsx trackers) ----------

def already_contacted_company(conn, user_id, company_name, beruf_group_names, region):
    """Local-tracker equivalent: has THIS user already been logged against
    this company for this Beruf or an overlapping one, in this region?"""
    placeholders = ",".join("?" for _ in beruf_group_names)
    row = conn.execute(
        f"""SELECT 1 FROM contacts
            WHERE user_id = ? AND company_name = ? AND region = ?
            AND beruf IN ({placeholders})""",
        (user_id, company_name, region, *beruf_group_names),
    ).fetchone()
    return row is not None


def already_contacted_email(conn, user_id, email):
    """Global-tracker equivalent, now scoped per-user (different friends
    ARE allowed to reach the same company -- see the product decision)."""
    row = conn.execute(
        "SELECT status FROM contacts WHERE user_id = ? AND email = ?",
        (user_id, email.lower()),
    ).fetchone()
    return row is not None


def log_contact(conn, user_id, company_name, email, beruf, region, status):
    email_l = email.lower() if email else None
    if email_l is None:
        # partial unique index only covers non-null emails -- nothing to
        # dedup against, just insert.
        conn.execute(
            """INSERT INTO contacts (user_id, company_name, email, beruf, region, status)
               VALUES (?, ?, NULL, ?, ?, ?)""",
            (user_id, company_name, beruf, region, status),
        )
        return
    conn.execute(
        """INSERT INTO contacts (user_id, company_name, email, beruf, region, status, sent_at)
           VALUES (?, ?, ?, ?, ?, ?, CASE WHEN ? = 'Sent' THEN datetime('now') ELSE NULL END)
           ON CONFLICT(user_id, email) WHERE email IS NOT NULL DO UPDATE SET
             status=excluded.status, updated_at=datetime('now')""",
        (user_id, company_name, email_l, beruf, region, status, status),
    )


def sent_emails_for_bounce_check(conn, user_id, job_id_not_used=None):
    """Every address this user has a 'Sent' status for -- what the IMAP
    bounce scan checks against."""
    return [r["email"] for r in conn.execute(
        "SELECT email FROM contacts WHERE user_id = ? AND status = 'Sent'", (user_id,)
    ).fetchall()]


def mark_bounced(conn, user_id, email):
    conn.execute(
        "UPDATE contacts SET status = 'Bounced', updated_at = datetime('now') "
        "WHERE user_id = ? AND email = ?",
        (user_id, email.lower()),
    )
    block_domain(conn, email, reason="bounced")  # shared, automatic


# ---------- jobs (run history, powers the dashboard) ----------

def start_job(conn, user_id, beruf, region):
    cur = conn.execute(
        "INSERT INTO jobs (user_id, beruf, region) VALUES (?, ?, ?)",
        (user_id, beruf, region),
    )
    return cur.lastrowid


def update_job_counts(conn, job_id, **counts):
    sets = ", ".join(f"{k} = ?" for k in counts)
    conn.execute(f"UPDATE jobs SET {sets} WHERE id = ?", (*counts.values(), job_id))


def finish_job(conn, job_id, status):
    conn.execute(
        "UPDATE jobs SET status = ?, finished_at = datetime('now') WHERE id = ?",
        (status, job_id),
    )
