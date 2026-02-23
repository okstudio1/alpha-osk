# LLM Onboarding

Quick reference for AI assistants working on Alpha-OSK.

---

## Project Overview

**Name:** Alpha-OSK  
**Purpose:** AI-powered on-screen keyboard for **Linux** accessibility  
**Status:** 🚀 Active Development — Core keyboard working, AI prediction integrated

---

## About the Owner

I'm Owen — a wheelchair user with muscular dystrophy.

- **Typing is hard** — Be proactive. Make decisions. Don't ask for confirmation on small things.
- **Offer A/B/C choices** — I can type one letter instead of explaining.
- **Linux environment** — Use bash syntax. This is a Linux project.
- **Accessibility matters** — This is a tool I actually need.

---

## Architecture

```
alpha-osk/
├── run.py                 # Smart launcher (venv + deps + launch)
├── src/
│   ├── keyboard_app.py    # QML engine setup, window flags
│   ├── keyboard_bridge.py # Python↔QML bridge (key synthesis, modifiers)
│   └── prediction/
│       ├── ngram_predictor.py      # Fast n-gram predictions (<10ms)
│       ├── transformer_predictor.py # LLM re-ranking (DistilGPT-2)
│       └── hybrid_predictor.py     # Combines both, emits Qt signals
├── qml/
│   ├── Main.qml           # Main keyboard window (modular layout)
│   └── components/
│       ├── KeyButton.qml      # Reusable key with animations
│       ├── NavigationPanel.qml # Insert/Delete/Home/End/PgUp/PgDn/Arrows
│       ├── NumpadPanel.qml    # Number pad
│       ├── FunctionRow.qml    # F1-F12 keys
│       ├── SettingsPanel.qml  # Toggle panels
│       └── SettingsToggle.qml # Toggle switch component
└── templates/             # Project dashboard (HTML)
```

---

## Tech Stack

- **Language:** Python 3.9+
- **UI Framework:** PySide6 + QML6 (Qt Quick)
- **Key Synthesis:** xdotool (X11) / ydotool (Wayland)
- **Prediction:** Hybrid n-gram + transformer (DistilGPT-2)
- **Dashboard:** HTML served via Python http.server

---

## Key Files

| File | Purpose |
|------|---------|
| `run.py` | Launcher — creates venv, installs deps, runs keyboard |
| `src/keyboard_bridge.py` | Python↔QML bridge — modifiers, key synthesis, predictions |
| `src/prediction/hybrid_predictor.py` | Prediction engine combining n-gram + LLM |
| `qml/Main.qml` | Main UI — modular with toggleable panels |
| `docs/PREDICTION_OPTIONS.md` | Comparison of prediction approaches |

---

## Current Features

- ✅ Full QWERTY layout with all symbols
- ✅ Modifiers: Shift, Caps, Ctrl, Alt, Win/Super (sticky)
- ✅ Toggleable panels: Function row, Navigation, Numpad
- ✅ Settings panel with layout toggles
- ✅ Compact mode option
- ✅ Hybrid prediction (n-gram instant + LLM refined)
- ✅ Next-word prediction after selecting a word
- ✅ Key hold/repeat for continuous typing
- ✅ Draggable window, stays on top, doesn't steal focus
- ✅ Dark theme with press animations

---

## Modular UI System

The keyboard has toggleable sections (via Settings ⚙ button):

| Panel | Keys | Default |
|-------|------|---------|
| Function Row | Esc, F1-F12, PrtSc, ScrLk, Pause | Off |
| Navigation | Ins, Del, Home, End, PgUp, PgDn, Arrows | Off |
| Numpad | Full number pad with NumLock | Off |
| Compact Mode | Smaller key sizes | Off |

---

## Quick Start

```bash
# Install system dependency
sudo apt install xdotool

# Run the keyboard (auto-creates venv, installs PySide6)
python run.py

# Optional: Install LLM for better predictions
./venv/bin/pip install transformers torch
```

---

## Git Commits

Use conventional commits:
```
feat: add new feature
fix: correct bug
docs: update documentation
refactor: restructure code
chore: maintenance tasks
```

```bash
git add -A && git commit -m "feat: description" && git push
```

---

## Inspiration Projects

| Project | Location | What We Borrowed |
|---------|----------|------------------|
| GNOME On-Board | `/home/owen/dev/onboard` | Accessibility features, layout ideas |
| Project-Nimbus | `/home/owen/dev/Project-Nimbus` | PySide6+QML architecture pattern |
| gitconnect | `/home/owen/dev/gitconnect` | Desktop app patterns |

---

## Constellation

This repo is tracked by [Constellation](https://github.com/owenpkent/constellation).

For the dashboard to pick up this project:
1. Have a `README.md` with a `## Status` section
2. Have a `TODO.md` with checkbox items (`- [ ]` / `- [x]`)
3. Add the repo path to Constellation's `projects.yaml`
