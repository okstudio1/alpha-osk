# Telemetry — Design

Anonymous, opt-in usage statistics that aggregate into a public "X million keystrokes saved" counter. **Off by default.** Distinct from federated learning (`docs/FEDERATED_LEARNING.md`): telemetry collects a handful of integer counters; federated learning collects model deltas. They could share infrastructure later but currently do not.

## What goes over the wire

A weekly POST to the aggregation backend, carrying one row per user:

```jsonc
{
  "anon_id":            "8f2a...",   // UUID4, generated on first opt-in
  "app_version":        "1.0.16",
  "os":                 "windows",   // "windows" | "linux"
  "ts":                 1234567890,  // unix seconds, set server-side on receipt
  "keystrokes":         18523,       // alltimeKeystrokes
  "words":              3421,        // alltimeWords
  "predictions":        2671,        // alltimePredictionHits
  "keystrokes_saved":   10342,       // alltimeKeystrokesSaved
  "minutes":            6366.1,      // alltimeMinutes
  "sessions":           43,          // alltimeSessions
  "prediction_offers":  9210         // alltimePredictionOffers
}
```

That's it. No content, no word frequencies, no key frequencies, no per-session breakdown, no timestamps from the client. **Privacy mode counters are already excluded from these source values** by `keyboard_bridge.py` (privacy mode suppresses `_current_word`, prediction tracking, and learning), so passwords and other sensitive input never enter the analytics counters in the first place. Telemetry just forwards what the analytics dashboard already shows.

## What the backend stores

D1 schema (`backend/cf-worker/schema.sql`):

```sql
CREATE TABLE users (
    anon_id     TEXT PRIMARY KEY,
    first_seen  INTEGER NOT NULL,
    last_seen   INTEGER NOT NULL,
    app_version TEXT,
    os          TEXT
);

CREATE TABLE submissions_latest (
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
```

One row per user, replaced on each submit (lifetime totals are monotonic, so latest = greatest). No per-submission history. No IP logged. No User-Agent stored. The aggregate endpoint (`GET /v1/aggregate`, cached 5 min) returns sums over `submissions_latest`.

## anon_id

UUID4 generated on first opt-in. Persisted to `<config_dir>/analytics.json` under the key `telemetry_anon_id`. Never derived from machine identity (no MAC address, no hostname, no Windows install ID). If the user opts out and back in, **a new anon_id is generated** so opt-in/opt-out cycles can't be linked across the cycle. This is deliberate: an anon_id stable across opt-out periods would let a determined operator track a user even after they revoked consent.

If the user clears their config dir or reinstalls, they get a new anon_id and their lifetime totals reset (the prior row in `submissions_latest` becomes orphaned and gets garbage-collected by the cron job below). No mechanism to link the new id to the old one.

## Submit cadence

Two paths, both gated on consent:

1. **Weekly QTimer**: 7-day interval, fires from `KeyboardBridge` once telemetry is enabled. First submission lands ~7 days after opt-in (not immediately on toggle), so a user toggling out of curiosity doesn't accidentally send anything.
2. **`aboutToQuit`**: if any counter has changed since the last successful submit, send before exit.

If the user opts in, types for two days, then opts out: nothing was sent because the weekly window hadn't elapsed. This is fine. The counters are lifetime totals, so a delayed submit just means the public aggregate lags reality by up to a week.

## Failure handling

Submit uses `urllib.request` (stdlib, no new dependency) with a 5 s timeout. On HTTP 4xx other than 429: log and drop (the request was malformed; retrying won't help). On 429 / 5xx / network error: exponential backoff `[5 s, 30 s, 120 s]`, max three attempts within the same QTimer tick. After three failures: silent drop, retry next week. The keyboard never blocks on a telemetry call. There is no user-visible error toast (a network error is not the user's problem).

## Cloudflare Worker endpoints

`POST /v1/submit`:
- Validates payload shape (all required keys present, types correct, integer counters non-negative).
- Caps each counter at a sanity ceiling (e.g. 10^9 keystrokes) so a malformed client can't poison the aggregate.
- Upserts into `users` and `submissions_latest`.
- Returns 204 on success, 4xx with a one-line reason on validation failure.

`GET /v1/aggregate`:
- Returns `{users: N, keystrokes: ..., keystrokes_saved: ..., minutes: ..., predictions: ...}`.
- Cached at the edge for 5 min via `Cache-Control: public, max-age=300`.

`POST /v1/forget`:
- Body: `{anon_id: "..."}`.
- Deletes the row from both tables (CASCADE).
- Returns 204 always (don't reveal whether the id existed).
- Triggered by a "Delete my contributed data" button in Settings.

## Garbage collection

A daily Cloudflare cron deletes `users` rows where `last_seen < now - 365 days`. Inactive installs eventually drop out of the aggregate. This also cleans up the orphan rows from reinstalls. 365 days is a deliberate compromise: short enough that the public counter reflects active users, long enough that someone who uses the keyboard seasonally (e.g. a student during semesters) doesn't lose their contribution between sessions.

## Threat model

- **Operator can see**: anon_ids, app version distribution, OS distribution, lifetime counters per user. Cannot see content, individual keystrokes, words used, sessions when, or anything that would identify a user.
- **A passive network observer** can see that the user POSTed to the telemetry endpoint, plus the payload size (~200 bytes). Cannot see the content (TLS).
- **A compromised backend** could backfill submissions to fake the public aggregate. Sanity ceilings on each counter limit the blast radius. Rate-limiting per-IP at the Cloudflare edge limits volume.
- **An adversary trying to deanonymize a user** has very little to work with: the anon_id is opaque, no IP is stored, no User-Agent is stored, no submission timestamps are kept (only the latest), and the aggregate endpoint never exposes individual rows. Linking attempts would have to rely on the lifetime counter values being unique enough to fingerprint, which they aren't (two power users with similar usage have similar totals).

## Why not just use Plausible / Umami / Google Analytics?

- These tools are session-event-oriented. They model "user visited page X". The unit here is a user's lifetime running totals, which doesn't fit the page-view schema.
- They typically log IP address, User-Agent, screen resolution, etc. We don't want any of that. Building our own gives us a small, auditable surface.
- Cost: Plausible self-hosted needs a VPS; Cloudflare Worker free tier covers our expected volume comfortably (10M requests/month free).

## Public counter (deferred)

Eventually a static page at e.g. `alpha-osk.com/impact` reads `/v1/aggregate` and renders "X million keystrokes saved across Y users". Not in scope for v1. Build the pipeline first, prove the data is clean, then design the public surface.
