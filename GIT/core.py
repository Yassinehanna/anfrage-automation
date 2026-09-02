"""
Multi-tenant core -- same mechanics as the original ANFRAGE.py run() loop
(Overpass sourcing, direct-email-first / scrape-fallback resolution, SMTP
send, IMAP bounce check, GmailDailyLimitExceeded handling), but:

  - no hardcoded GMAIL_ADDRESS/GMAIL_APP_PASS/BEWERBER_NAME -- passed in
    via a `user` row from the users table
  - no .xlsx trackers -- all reads/writes go through db.py
  - company sourcing and email resolution are SHARED caches (db.py),
    so a second user searching the same Beruf+region doesn't re-hit
    Overpass or re-scrape a site another user already resolved
  - dedup ("have I contacted this company/email before") is scoped to
    the current user, not global across all users
  - bounces automatically add to the shared blocked_domains table
"""

import re
import time
import smtplib
import imaplib
import email as email_lib
import os
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
import urllib3
from bs4 import BeautifulSoup

import db
from categories import ALL_BERUFE

# Configuration from environment variables
DELAY = int(os.getenv('DELAY', '5'))
BOUNCE_CHECK_EVERY = int(os.getenv('BOUNCE_CHECK_EVERY', '20'))

# Same reasoning as the original script: we deliberately skip cert
# verification when scraping company sites (verify=False below), which
# is safe for reading a public page but makes urllib3 print a warning on
# every single request. This silences that noise -- same line the
# original ANFRAGE.py had in run().
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]
OVERPASS_HEADERS = {"User-Agent": "ANFRAGE-Bot/2.0 (multi-user)"}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}
CONTACT_KW = ["kontakt", "contact", "impressum", "imprint", "uber-uns", "ansprechpartner"]
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
SKIP_EMAIL = ["example", "sentry", "wix", ".png", ".jpg", "schema.org"]


class GmailDailyLimitExceeded(Exception):
    """Raised when Gmail's daily cap kicks in -- same signal as before."""
    pass


# ---------------- company sourcing (cached) ----------------

def _build_overpass_query(area_name, tags):
    tag_blocks = []
    for tag in tags:
        key, value = tag.split("=")
        tag_blocks.append(f'node["{key}"="{value}"](area.searchArea);')
        tag_blocks.append(f'way["{key}"="{value}"](area.searchArea);')
    return f"""
    [out:json][timeout:90];
    area["name"="{area_name}"]->.searchArea;
    ( {' '.join(tag_blocks)} );
    out center tags;
    """


def get_companies(conn, beruf_label, region, tags, max_retries=3):
    """Shared-cache-first: reuse another user's recent fetch for this exact
    Beruf+region before hitting Overpass again."""
    cached = db.get_cached_companies(conn, beruf_label, region)
    if cached:
        return cached

    query = _build_overpass_query(region, tags)
    response, last_error = None, None
    for url in OVERPASS_URLS:
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(url, data={"data": query},
                                          headers=OVERPASS_HEADERS, timeout=100)
                response.raise_for_status()
                break
            except requests.exceptions.RequestException as e:
                last_error = e
                response = None
                if attempt < max_retries:
                    time.sleep(5 * attempt)
        if response is not None:
            break
    if response is None:
        raise RuntimeError(f"All Overpass mirrors failed. Last error: {last_error}")

    elements = response.json().get("elements", [])
    rows, seen_names = [], set()
    for el in elements:
        t = el.get("tags", {})
        name = t.get("name")
        if not name or name in seen_names:
            continue
        website = t.get("website") or t.get("contact:website") or ""
        email = t.get("email") or t.get("contact:email") or ""
        if not website and not email:
            continue
        seen_names.add(name)
        rows.append({"name": name, "website": website, "email": email,
                      "phone": t.get("phone") or t.get("contact:phone") or "",
                      "city": t.get("addr:city", "")})

    db.store_companies(conn, beruf_label, region, rows)
    return db.get_cached_companies(conn, beruf_label, region)


# ---------------- email resolution (cached) ----------------

def _find_email_on_website(website):
    if not website:
        return None
    if not website.startswith("http"):
        website = "https://" + website
    try:
        r = requests.get(website, headers=HEADERS, timeout=10, verify=False)
    except requests.exceptions.RequestException:
        return None
    email = _extract_email(r.text)
    if email:
        return email

    try:
        soup = BeautifulSoup(r.text, "lxml")
    except Exception:
        return None
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(kw in href.lower() for kw in CONTACT_KW):
            full = href if href.startswith("http") else website.rstrip("/") + "/" + href.lstrip("/")
            links.add(full)

    for link in list(links)[:4]:
        try:
            r2 = requests.get(link, headers=HEADERS, timeout=10, verify=False)
            email = _extract_email(r2.text)
            if email:
                return email
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    return None


def _extract_email(text):
    candidates = [e for e in EMAIL_REGEX.findall(text)
                  if not any(skip in e.lower() for skip in SKIP_EMAIL)]
    return sorted(candidates)[0] if candidates else None


def resolve_email(conn, company_row):
    """direct email (from Overpass tags) -> shared resolved-email cache
    -> scrape -> store result in cache either way, even 'none', so no
    future run re-scrapes this site."""
    if company_row["email"]:
        return company_row["email"]

    cached = db.get_resolved_email(conn, company_row["id"])
    if cached is not None:
        return cached["email"]  # may legitimately be None ("scraped, found nothing")

    found = _find_email_on_website(company_row["website"])
    db.store_resolved_email(conn, company_row["id"],
                             found, "scraped" if found else "none")
    return found


# ---------------- sending ----------------

def send_email(user, to_addr, subject, body):
    msg = MIMEMultipart()
    msg["From"] = user["gmail_address"]
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(user["gmail_address"], user["gmail_app_pass"])
            smtp.send_message(msg)
        return True
    except Exception as e:
        msg_text = str(e).lower()
        if "5.4.5" in msg_text or "daily user sending limit" in msg_text:
            raise GmailDailyLimitExceeded(str(e))
        return False


def _decode_maybe(s):
    parts = decode_header(s)
    out = []
    for text, enc in parts:
        if isinstance(text, bytes):
            out.append(text.decode(enc or "utf-8", errors="ignore"))
        else:
            out.append(text)
    return "".join(out)


def _extract_text(msg):
    out = []
    for part in msg.walk():
        ctype = part.get_content_type()
        if ctype in ("text/plain", "text/html"):
            try:
                charset = part.get_content_charset() or "utf-8"
                text = part.get_payload(decode=True).decode(charset, errors="ignore")
            except Exception:
                continue
            if ctype == "text/html":
                text = re.sub(r"<[^>]+>", " ", text)
            out.append(text)
    return " ".join(out)


def check_bounces(conn, user):
    """Same IMAP mechanism as before, but marks bounces via db.mark_bounced,
    which also auto-adds the domain to the shared blocklist."""
    sent_addrs = {a.lower() for a in db.sent_emails_for_bounce_check(conn, user["id"])}
    if not sent_addrs:
        return []

    bounced = []
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(user["gmail_address"], user["gmail_app_pass"])
    imap.select("inbox")
    for sender in ("mailer-daemon", "postmaster"):
        _, ids = imap.search(None, f'(FROM "{sender}")')
        for msg_id in ids[0].split():
            _, data = imap.fetch(msg_id, "(BODY.PEEK[])")
            raw = data[0][1]
            msg = email_lib.message_from_bytes(raw)
            text = _extract_text(msg)
            for addr in sent_addrs:
                if addr in text:
                    db.mark_bounced(conn, user["id"], addr)
                    bounced.append(addr)
    imap.logout()
    return bounced


# ---------------- orchestration ----------------

def run(conn, user, beruf, region, target):
    """beruf: one of the dicts from categories.ALL_BERUFE."""
    return run_with_progress(conn, user, beruf, region, target, progress_callback=None)


def run_with_progress(conn, user, beruf, region, target, progress_callback=None):
    """Same as run() but accepts an optional progress_callback(progress, message)
    for web UI progress updates."""
    group = beruf["group"]
    group_names = [b["beruf"] for b in ALL_BERUFE.values() if b["group"] == group]

    if progress_callback:
        progress_callback(0, "Fetching companies from Overpass API...")
    
    companies = get_companies(conn, beruf["beruf"], region, beruf["tags"])
    job_id = db.start_job(conn, user["id"], beruf["beruf"], region)

    body = beruf["body"].format(name=user["name"])
    sent = failed = skipped = no_email = sent_count = 0
    total_companies = len(companies)

    for i, c in enumerate(companies):
        if sent_count >= target:
            if progress_callback:
                progress_callback(1.0, f"Target reached: {sent_count} emails sent")
            break

        progress = (i + 1) / total_companies if total_companies > 0 else 0
        if progress_callback:
            progress_callback(progress, f"Processing {c['name']} ({i+1}/{total_companies})...")

        if db.already_contacted_company(conn, user["id"], c["name"], group_names, region):
            skipped += 1
            if progress_callback:
                progress_callback(progress, f"Skipped {c['name']} (already contacted)")
            continue

        email = resolve_email(conn, c)
        if not email:
            db.log_contact(conn, user["id"], c["name"], None, beruf["beruf"], region, "No email found")
            no_email += 1
            if progress_callback:
                progress_callback(progress, f"No email found for {c['name']}")
            continue

        if db.is_domain_blocked(conn, email):
            db.log_contact(conn, user["id"], c["name"], email, beruf["beruf"], region,
                            "Skipped (blocked domain)")
            skipped += 1
            if progress_callback:
                progress_callback(progress, f"Skipped {c['name']} (blocked domain)")
            continue

        if db.already_contacted_email(conn, user["id"], email):
            db.log_contact(conn, user["id"], c["name"], email, beruf["beruf"], region,
                            "Skipped (already contacted)")
            skipped += 1
            if progress_callback:
                progress_callback(progress, f"Skipped {email} (already contacted)")
            continue

        if progress_callback:
            progress_callback(progress, f"Sending email to {email}...")

        try:
            ok = send_email(user, email, beruf["subject"], body)
        except GmailDailyLimitExceeded:
            db.log_contact(conn, user["id"], c["name"], email, beruf["beruf"], region, "Failed")
            failed += 1
            db.update_job_counts(conn, job_id, sent_count=sent, failed_count=failed,
                                  skipped_count=skipped, no_email_count=no_email)
            db.finish_job(conn, job_id, "stopped_daily_limit")
            if progress_callback:
                progress_callback(progress, "Daily limit reached - stopping")
            return {"sent": sent, "failed": failed, "skipped": skipped,
                    "no_email": no_email, "stopped": "daily_limit"}

        status = "Sent" if ok else "Failed"
        db.log_contact(conn, user["id"], c["name"], email, beruf["beruf"], region, status)
        if ok:
            sent += 1
            sent_count += 1
            if progress_callback:
                progress_callback(progress, f"✅ Email sent to {email} ({sent_count}/{target})")
            if sent_count % BOUNCE_CHECK_EVERY == 0:
                if progress_callback:
                    progress_callback(progress, "Checking for bounces...")
                check_bounces(conn, user)
            time.sleep(DELAY)
        else:
            failed += 1
            if progress_callback:
                progress_callback(progress, f"❌ Failed to send to {email}")

    db.update_job_counts(conn, job_id, sent_count=sent, failed_count=failed,
                          skipped_count=skipped, no_email_count=no_email)
    
    if progress_callback:
        progress_callback(1.0, "Final bounce check...")
    
    check_bounces(conn, user)
    db.finish_job(conn, job_id, "done")
    
    if progress_callback:
        progress_callback(1.0, "Job completed successfully")
    
    return {"sent": sent, "failed": failed, "skipped": skipped, "no_email": no_email}
