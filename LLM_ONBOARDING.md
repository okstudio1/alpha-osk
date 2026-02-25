# LLM Onboarding

Quick reference for AI assistants working on Alpha-OSK.

---

## Project Overview

**Name:** Alpha-OSK  
**Purpose:** AI-powered on-screen keyboard for **Linux** accessibility  
**Status:** 🚀 Active Development — Core keyboard working, AI prediction integrated

---

## Philosophy

> *"Writing can be described as **zooming in on an alphabetical library, steering as you go**."*  
> — Dasher Project

Alpha-OSK is built on principles learned from decades of assistive technology research, particularly the [Dasher Project](https://dasher.at) from Cambridge University.

**Core Principles:**
1. **Information-efficient design** — Make probable text easier to find
2. **Accessibility first** — Built by a wheelchair user, for real needs
3. **Adaptive learning** — Gets better the more you use it
4. **Transparent and open** — Free, documented, community-driven

📖 **Read the full philosophy:** [`PHILOSOPHY.md`](PHILOSOPHY.md)

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
│   ├── keyboard_bridge.py # Python↔QML bridge (key synthesis, modifiers, predictions)
│   └── prediction/
│       ├── ngram_predictor.py       # Word-level frequency prediction (<10ms)
│       ├── ppm_predictor.py         # Character-level PPM (Dasher algorithm)
│       ├── fuzzy_recognizer.py      # Spatial error correction + 6 accessibility profiles
│       ├── transformer_predictor.py # Optional LLM re-ranking (disabled by default)
│       └── hybrid_predictor.py      # Orchestrates all predictors, emits Qt signals
├── qml/
│   ├── Main.qml           # Main keyboard window (modular layout)
│   └── components/
│       ├── KeyButton.qml         # Reusable key with animations
│       ├── AccessibilityPanel.qml # Motor control profile selector (♿)
│       ├── NavigationPanel.qml   # Insert/Delete/Home/End/PgUp/PgDn/Arrows
│       ├── NumpadPanel.qml       # Number pad
│       ├── FunctionRow.qml       # F1-F12 keys
│       ├── SettingsPanel.qml     # Toggle panels
│       └── PredictionSettingsPanel.qml # Prediction engine settings
├── data/
│   ├── base_dictionary.txt  # Common English words
│   └── training_corpus.txt  # Pre-loaded phrases for PPM training
└── templates/             # Project dashboard (HTML)
```

---

## Tech Stack

- **Language:** Python 3.9+
- **UI Framework:** PySide6 + QML6 (Qt Quick)
- **Key Synthesis:** xdotool (X11) / ydotool (Wayland)
- **Prediction:** Hybrid engine (n-gram + PPM + fuzzy recognition)
- **No AI/LLM required** — Transformer disabled by default (can re-enable if desired)

### Prediction Architecture

```
User types key → Fuzzy Recognition (spatial correction)
                      ↓
              ┌───────┴───────┐
              ↓               ↓
           N-gram           PPM
         (word freq)    (char context)
              ↓               ↓
              └───────┬───────┘
                      ↓
              Weighted Merge
                      ↓
              Final Predictions
```

**Why no AI?** N-gram + PPM + Fuzzy provides excellent predictions without:
- 300MB model download
- 10-second startup delay
- GPU/memory overhead

---

## Key Files

| File | Purpose |
|------|---------|
| `run.py` | Launcher — creates venv, installs deps, runs keyboard |
| `src/keyboard_bridge.py` | Python↔QML bridge — modifiers, key synthesis, predictions |
| `src/prediction/hybrid_predictor.py` | Orchestrates all predictors, Qt signals |
| `src/prediction/ppm_predictor.py` | Character-level PPM (Dasher algorithm) |
| `src/prediction/fuzzy_recognizer.py` | Spatial error correction + accessibility profiles |
| `qml/components/AccessibilityPanel.qml` | Motor control profile selector UI |
| `qml/Main.qml` | Main UI — modular with toggleable panels |
| `docs/PREDICTION_OPTIONS.md` | Comparison of prediction approaches |

---

## Current Features

- ✅ Full QWERTY layout with all symbols
- ✅ Modifiers: Shift, Caps, Ctrl, Alt, Win/Super (sticky)
- ✅ Toggleable panels: Function row, Navigation, Numpad
- ✅ Settings panel with layout toggles
- ✅ Compact mode option
- ✅ **Hybrid prediction** (n-gram + PPM + fuzzy recognition)
- ✅ **PPM Language Model** — Character-level prediction (Dasher algorithm)
- ✅ **Fuzzy/Spatial Recognition** — Corrects mistypes based on key proximity
- ✅ **6 Accessibility Profiles** — Precise, Normal, Mild/Moderate/Severe Tremor, Limited Mobility
- ✅ **Next-word prediction** — After selecting a word, suggests likely follow-ups
- ✅ **Training corpus** — Pre-loaded common phrases for better predictions
- ✅ Key hold/repeat for continuous typing (including backspace)
- ✅ Draggable window, stays on top, doesn't steal focus
- ✅ **5 Color Themes** — Dark, Light, Blue, Green, Purple (⚙ Settings)
- ✅ **Smart punctuation** — Removes space before ? ! . , ; :
- ✅ Accessibility settings panel (♿ button)
- ✅ Modern prediction bar with improved readability

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
python3 run.py
```

That's it! No AI/LLM download required. Predictions work out of the box with n-gram + PPM + fuzzy recognition.

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
| **Dasher** | `/home/owen/dev/dasher-website` | Philosophy, information-efficient design, accessibility principles |
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
