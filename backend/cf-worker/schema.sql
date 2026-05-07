-- Alpha-OSK telemetry schema for Cloudflare D1.
--
-- One row per opted-in user (keyed by random anon_id). The latest
-- submission overwrites the previous one because lifetime counters
-- are monotonic, so "latest = greatest" and we don't need history.
--
-- Apply with:
--   wrangler d1 execute alpha-osk-telemetry --file schema.sql
-- (or --local for the local dev DB).

CREATE TABLE IF NOT EXISTS users (
    anon_id     TEXT PRIMARY KEY,
    first_seen  INTEGER NOT NULL,   -- unix seconds, server-set on first POST
    last_seen   INTEGER NOT NULL,   -- unix seconds, server-set on every POST
    app_version TEXT,
    os          TEXT
);

CREATE TABLE IF NOT EXISTS submissions_latest (
    anon_id            TEXT PRIMARY KEY,
    ts                 INTEGER NOT NULL,
    keystrokes         INTEGER NOT NULL,
    words              INTEGER NOT NULL,
    predictions        INTEGER NOT NULL,
    keystrokes_saved   INTEGER NOT NULL,
    minutes            REAL    NOT NULL,
    sessions           INTEGER NOT NULL,
    prediction_offers  INTEGER NOT NULL,
    FOREIGN KEY (anon_id) REFERENCES users(anon_id) ON DELETE CASCADE
);

-- last_seen index supports the daily GC cron that prunes inactive
-- installs (last_seen older than 365 days).
CREATE INDEX IF NOT EXISTS idx_users_last_seen ON users(last_seen);
