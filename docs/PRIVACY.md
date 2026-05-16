# Alpha-OSK Privacy

The short version: by default, **nothing leaves your computer**. Alpha-OSK predicts and learns entirely on your machine. Your typed text, vocabulary, keystroke history, and prediction model never touch a server.

## Optional usage telemetry

Settings → Data & Privacy → Privacy has one toggle: **"Share anonymous usage stats"**. It is off by default. If you turn it on, Alpha-OSK sends a small weekly report so we can track total impact across the community (e.g. "X million keystrokes saved across Y users").

### What's in the report

Nine numbers, sent once a week:

| Field | Example | What it is |
|-------|---------|------------|
| `anon_id` | `8f2a-4c1b-...` | A random ID generated when you first turn the toggle on. Not your username, email, or any system identifier. |
| `app_version` | `1.0.16` | Which version you're running. |
| `os` | `windows` | Your operating system (Windows or Linux). |
| `keystrokes` | `18523` | How many keys you've pressed total. |
| `words` | `3421` | How many words you've typed total. |
| `predictions` | `2671` | How many times you've clicked a suggestion. |
| `keystrokes_saved` | `10342` | How many keys the suggestions saved you. |
| `minutes` | `6366` | Total time spent typing. |
| `sessions` | `43` | How many times you've launched Alpha-OSK. |
| `prediction_offers` | `9210` | How many times we showed you suggestions. |

These are exactly the lifetime numbers shown on your Analytics dashboard. Nothing more.

### What's NOT in the report

- The text you typed. Ever. No words, no sentences, no fragments.
- Your vocabulary. The list of words you've taught Alpha-OSK never leaves your machine.
- Per-key data. We don't send which letters you press most, common typos, or anything per-keystroke.
- Per-session data. Only your running totals.
- Your IP address. Not logged on the server.
- Your machine. No hostname, MAC address, hardware ID, or operating-system install ID.
- Anything from typing into a password field. Privacy mode (the "Learning" / "Paused" toggle in the title bar) blocks all tracking when a password field is focused, so password-field activity never enters the totals in the first place.

### Where the data goes

To a Cloudflare Worker that we control. The worker stores one row per `anon_id` (the latest report, replaced each week — no history kept) and exposes a public aggregate endpoint that returns the total across everyone. Individual rows are never exposed publicly.

### Opting out

Turn the toggle off in Settings → Data & Privacy → Privacy. Future weekly reports stop. Already-submitted data is **not** automatically deleted — your row in the database stays until either (a) you click "Delete my contributed data" in the same Settings section, or (b) you don't open Alpha-OSK for 365 days, after which the row is automatically removed.

If you opt back in later, you get a **new** `anon_id`. Your prior contribution and your new contribution cannot be linked. This is intentional.

### Reinstalling / clearing config

If you reinstall Alpha-OSK or delete `%APPDATA%\alpha-osk\` (Windows) or `~/.config/alpha-osk/` (Linux), you start fresh. New `anon_id`, lifetime counters back to zero. Your old row in the database becomes orphaned and gets cleaned up by the 365-day rule.

## Federated learning

A separate planned feature (`docs/FEDERATED_LEARNING.md`) that would share *learning updates* across users to improve prediction quality for everyone. **Not yet implemented.** When it ships, it will be a separate opt-in toggle with its own clear explanation, distinct from this telemetry toggle. Federated learning never sends raw text either, but it sends more than telemetry does (n-gram statistical updates, with differential-privacy noise added). Worth understanding the trade-off separately before opting in.

## Auto-update

Alpha-OSK checks GitHub Releases on startup if "Check for updates on startup" is enabled in Settings → Data & Privacy → Updates. This sends an HTTPS request to GitHub for the latest release metadata. GitHub sees the request the same way it would see any unauthenticated HTTPS visit (your IP, your User-Agent, the URL). No Alpha-OSK identity is attached. This is unrelated to the telemetry toggle.

## Questions or concerns

Open an issue on the project repo. We'll respond.
