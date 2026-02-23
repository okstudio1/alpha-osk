# Alpha-OSK

**AI-Powered On-Screen Keyboard for Linux**

An accessible on-screen keyboard designed for users with motor disabilities, featuring AI-enabled predictive text, voice dictation, and federated learning for personalized adaptation.

---

## Status

**Phase:** � Active Development

| Area | Status |
|------|--------|
| Core Keyboard | ✅ Complete |
| AI Prediction | 🚧 In Progress |
| Voice Dictation | ⏳ Planned |
| Federated Learning | ⏳ Planned |
| Collaboration Features | ⏳ Planned |
| Dashboard | ✅ Complete |

---

## Vision

Current Linux on-screen keyboards (including GNOME On-Board) lack modern AI capabilities. Alpha-OSK builds on the accessibility-first approach of On-Board with:

- **Intelligent word prediction** that learns your vocabulary
- **Voice dictation** with low-latency transcription
- **Federated learning** for privacy-preserving personalization
- **Collaborative dictionaries** shared across disability communities
- **Adaptive layouts** optimized for limited mobility

---

## Key Features (Planned)

### 🧠 AI-Powered Prediction
- Context-aware word and phrase completion
- Personal vocabulary learning (on-device)
- Specialized dictionaries (medical terms, assistive tech jargon)

### 🎤 Voice Dictation
- Real-time speech-to-text (Whisper-based)
- Voice commands for navigation and editing
- Hybrid input: switch between voice and touch seamlessly

### 🔒 Federated Learning
- Model improves without sending raw data to servers
- Privacy-first personalization
- Opt-in aggregated learning across users

### 🤝 Collaboration
- Shared word lists and abbreviation expansions
- Community-contributed accessibility profiles
- Sync settings across devices

### 🎨 Adaptive Layout
- Customizable key sizes and spacing
- Dwell-click and scanning support
- High-contrast and low-vision themes

---

## Current Features

- ✅ **QWERTY layout** with shift/caps lock toggle
- ✅ **Number and symbol layers** (123/#+= toggle)
- ✅ **Sticky modifiers** — Ctrl, Alt (auto-release after next key)
- ✅ **Key synthesis** via xdotool (X11) or ydotool (Wayland)
- ✅ **Dark theme** with press animations
- ✅ **Draggable window** — stays on top, doesn't steal focus
- ✅ **Prediction bar** — UI ready, engine in development

## Inspiration

- **GNOME On-Board (Linux)** — Great customization, but limited AI
- **Project-Nimbus** — PySide6+QML architecture pattern
- **iOS/Android keyboards** — Excellent prediction, not accessible enough

Alpha-OSK combines the best of accessibility-first design with modern AI.

---

## Tech Stack

- **Language:** Python 3.9+
- **UI Framework:** PySide6 + QML6 (Qt Quick)
- **Key Synthesis:** xdotool (X11) / ydotool (Wayland)
- **AI/ML (Planned):** 
  - Transformers (Hugging Face) for prediction
  - Whisper (OpenAI) for voice
  - Flower for federated learning
- **Dashboard:** HTML/CSS (served via Python)

---

## Quick Start

### Install System Dependencies
```bash
sudo apt install xdotool  # For X11 key synthesis
```

### Run the Keyboard
```bash
python run.py
```

The launcher automatically:
- Creates a virtual environment
- Installs PySide6 and dependencies
- Launches the on-screen keyboard

### Run the Dashboard
```bash
python run.py --dashboard
```

Dashboard opens at `http://localhost:8080`

---

## Project Structure

```
alpha-osk/
├── README.md              # This file
├── TODO.md                # Task tracking
├── DESIGN.md              # Layout and UX specifications
├── run.py                 # Smart launcher (venv + dependency mgmt)
├── requirements.txt       # Python dependencies
├── src/
│   ├── keyboard_app.py    # QML engine setup and window config
│   ├── keyboard_bridge.py # Python↔QML bridge for key synthesis
│   └── __init__.py
├── qml/
│   ├── Main.qml           # Main keyboard window
│   └── components/
│       └── KeyButton.qml  # Reusable key component
├── templates/
│   └── dashboard.html     # Project dashboard
└── docs/                  # Extended documentation
```

---

## License

MIT License — Free for personal and commercial use.

---

## Constellation

This repo is tracked by [Constellation](https://github.com/owenpkent/constellation) for cross-project visibility.
