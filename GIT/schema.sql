-- ============================================================
-- Schema for the multi-user version of ANFRAGE.py
-- Replaces: per-Beruf-region .xlsx trackers, global_contacted.xlsx
-- Adds: shared company cache, shared automatic blocklist
-- ============================================================

PRAGMA foreign_keys = ON;

-- One row per friend using the tool. Now with proper authentication.
CREATE TABLE users (
    id              INTEGER PRIMARY KEY,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    name            TEXT NOT NULL,
    gmail_address   TEXT NOT NULL UNIQUE,
    gmail_app_pass  TEXT NOT NULL,
    is_admin        INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Session management for web authentication
CREATE TABLE sessions (
    id              INTEGER PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    session_token   TEXT NOT NULL UNIQUE,
    expires_at      TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Shared cache of Overpass results per (beruf, region). Any user searching
-- "Kfz-Mechatroniker, Berlin" reuses this instead of re-hitting Overpass.
-- Refresh on a TTL (e.g. re-fetch if fetched_at is older than 7 days).
CREATE TABLE companies (
    id          INTEGER PRIMARY KEY,
    beruf       TEXT NOT NULL,
    region      TEXT NOT NULL,
    name        TEXT NOT NULL,
    website     TEXT,
    email       TEXT,          -- direct email from OSM tags, if any
    phone       TEXT,
    city        TEXT,
    fetched_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(beruf, region, name)
);

-- Shared cache of "we already scraped this company's website, here's what
-- we found (or that we found nothing)". Keyed by company, not by user --
-- once one user's run scrapes a site, no future user or run re-scrapes it.
CREATE TABLE resolved_emails (
    id           INTEGER PRIMARY KEY,
    company_id   INTEGER NOT NULL REFERENCES companies(id),
    email        TEXT,          -- NULL means "scraped, nothing found"
    source       TEXT NOT NULL, -- 'direct' | 'scraped' | 'none'
    resolved_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(company_id)
);

-- Replaces BOTH the local (.xlsx) and global (.xlsx) trackers.
--   local dedup   -> filter by user_id + beruf-group + region
--   global dedup  -> filter by user_id + email (per-user, per the decision
--                    that different friends ARE allowed to contact the
--                    same company -- they're different applicants)
CREATE TABLE contacts (
    id            INTEGER PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    company_name  TEXT NOT NULL,
    email         TEXT,
    beruf         TEXT NOT NULL,
    region        TEXT NOT NULL,
    status        TEXT NOT NULL,  -- Sent | Failed | Bounced | Skipped | No email found
    sent_at       TEXT,
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- One user can't be logged twice for the same real address (mirrors the
-- old "exact email, case-insensitive" global-tracker rule, just scoped
-- to this user instead of to everyone).
CREATE UNIQUE INDEX idx_contacts_user_email
    ON contacts(user_id, email)
    WHERE email IS NOT NULL;

-- The NEW shared safety net: any bounce or complaint blocks a domain for
-- EVERY user, automatically, forever. This is the piece that didn't exist
-- in the single-user version -- it's what keeps multiple friends emailing
-- overlapping company lists from turning into repeat contact of the same
-- annoyed business.
CREATE TABLE blocked_domains (
    id          INTEGER PRIMARY KEY,
    domain      TEXT NOT NULL UNIQUE,   -- e.g. "autohaus-berghorn.de"
    reason      TEXT NOT NULL,           -- 'bounced' | 'complaint'
    blocked_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- One row per run. Powers the future dashboard (live counts, history).
CREATE TABLE jobs (
    id              INTEGER PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    beruf           TEXT NOT NULL,
    region          TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'running', -- running | done | stopped_daily_limit | error
    sent_count      INTEGER NOT NULL DEFAULT 0,
    failed_count    INTEGER NOT NULL DEFAULT 0,
    skipped_count   INTEGER NOT NULL DEFAULT 0,
    no_email_count  INTEGER NOT NULL DEFAULT 0,
    started_at      TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at     TEXT
);
