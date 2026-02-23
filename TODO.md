# TODO

## Phase 1: Foundation ✅

- [x] **Set up project structure** — Create src directories
- [x] **Basic keyboard window** — PySide6 + QML6 floating window
- [x] **Key input simulation** — Send keystrokes to focused app via xdotool
- [x] **Simple QWERTY layout** — Standard keyboard arrangement

## Phase 2: Accessibility Core

- [ ] **Dwell-click support** — Trigger keys by hovering
- [ ] **Scanning mode** — Row/column scanning for switch users
- [x] **Adjustable key sizes** — Compact mode toggle in settings
- [ ] **High-contrast themes** — WCAG-compliant color schemes
- [x] **Sticky/latch keys** — Shift, Caps, Ctrl, Alt, Win/Super (auto-release)
- [x] **Modular layout** — Toggleable Function Row, Nav Panel, Numpad

## Phase 3: AI Prediction ✅

- [x] **Word prediction engine** — Hybrid n-gram + DistilGPT-2 LLM
- [x] **Prediction integration** — Connected to QML UI with real-time updates
- [x] **Personal vocabulary** — Learns from typed words and selections
- [ ] **Abbreviation expansion** — Custom shortcuts (e.g., "omw" → "on my way")
- [ ] **Medical/AT dictionary** — Specialized terms

## Phase 4: Voice Dictation

- [ ] **Whisper integration** — Local speech-to-text
- [ ] **Real-time transcription** — Streaming audio input
- [ ] **Voice commands** — "Delete word", "New line", etc.
- [ ] **Hybrid mode** — Switch between voice and keyboard

## Phase 5: Federated Learning

- [ ] **Local model training** — On-device personalization
- [ ] **Flower client setup** — Federated learning framework
- [ ] **Privacy controls** — User consent and data visibility
- [ ] **Model aggregation** — Contribute to shared improvements

## Phase 6: Collaboration

- [ ] **Shared word lists** — Import/export vocabularies
- [ ] **Community profiles** — Pre-built accessibility configs
- [ ] **Cloud sync** — Settings across devices (optional)
- [ ] **Accessibility presets** — One-click configurations

## Backlog

- [ ] Multi-language support
- [ ] Emoji and symbol panels
- [ ] Macro recording
- [ ] Integration with AAC software
- [ ] Eye-tracking support
- [ ] Game controller input

---

## Completed

- [x] Project planning
- [x] Initial documentation
- [x] Dashboard setup
- [x] PySide6 + QML6 architecture
- [x] Python↔QML bridge (keyboard_bridge.py)
- [x] Full QWERTY layout with all symbols (`, [], {}, \|, etc.)
- [x] Sticky modifiers (Shift, Caps, Ctrl, Alt, Win/Super)
- [x] Key synthesis via xdotool/ydotool
- [x] Dark theme with press animations
- [x] Draggable window (stays on top, no focus steal)
- [x] Hybrid prediction engine (n-gram + LLM)
- [x] Function row (F1-F12, Esc, PrtSc, etc.)
- [x] Navigation panel (Ins, Del, Home, End, PgUp, PgDn, Arrows)
- [x] Number pad with NumLock
- [x] Settings panel with layout toggles
- [x] Compact mode option
- [x] LLM_ONBOARDING.md updated for AI assistants
- [x] Key hold/repeat functionality
- [x] Next-word prediction after word selection
