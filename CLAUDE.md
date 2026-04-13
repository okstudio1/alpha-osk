# CLAUDE.md — Alpha-OSK AI Onboarding

## About the Owner

Owen is a wheelchair user with muscular dystrophy. Typing is hard — be proactive, make decisions, don't ask for confirmation on small things. Offer A/B/C choices so he can type one letter instead of explaining. This is an accessibility tool he actually needs.

## What This Is

Alpha-OSK is an AI-powered on-screen keyboard for Windows and Linux. Users click keys in the UI to type into other applications. It uses a hybrid prediction engine (n-gram + PPM + fuzzy recognition) — no LLM/GPU required.

## How to Run

```bash
python run.py          # Creates venv, installs deps, launches keyboard
python -m pytest       # Run tests (266+ tests)
```

## Architecture Overview

```
User clicks key (QML)
  → KeyButton.qml sends signal
  → Main.qml calls keyboard.pressKey() / keyboard.pressSpecialKey()
  → keyboard_bridge.py (Python↔QML bridge)
    → platform/*.py synthesizes keystroke (xdotool on Linux, SendInput on Windows)
    → prediction engine updates suggestions
  → predictions emitted back to QML via Signal
```

## Key Directories

| Path | What |
|------|------|
| `src/keyboard_bridge.py` | Central bridge: key handling, modifiers, context tracking, predictions |
| `src/keyboard_app.py` | App launcher: QML engine, window flags, auto-save on exit |
| `src/platform/` | OS abstraction — `linux.py` (xdotool/ydotool), `windows.py` (SendInput), `password_detect.py` |
| `src/platform/__init__.py` | Platform detection, `get_config_dir()`, `get_model_dir()` |
| `src/prediction/` | Prediction engines (see below) |
| `qml/Main.qml` | Root UI — title bar, keyboard rows, prediction bar, resize handles |
| `qml/components/` | Reusable QML components (KeyButton, settings panels, etc.) |
| `data/` | Static data: dictionaries, training corpus, keyboard layouts, vocab packs |
| `build/` | Windows build: PyInstaller spec, UIAccess manifest, signing |
| `tests/` | pytest suite |

## Prediction Engine

All in `src/prediction/`. Orchestrated by `hybrid_predictor.py`:

| File | Role |
|------|------|
| `ngram_predictor.py` | Word-frequency model: unigrams, bigrams, trigrams. Learns from typing. |
| `ppm_predictor.py` | Character-level PPM (Dasher algorithm). Predicts next characters. |
| `fuzzy_recognizer.py` | Spatial error correction. Considers nearby keys as candidates. Has 6 accessibility profiles. |
| `hybrid_predictor.py` | Merges all predictors. Manages model save/load. Emits Qt signals. |
| `vocabulary_pack.py` | Domain vocab packs (medical, programming, etc.) + custom pack import |
| `transformer_predictor.py` | Optional LLM re-ranking (disabled by default) |

## Auto-Capitalization & Proper Nouns

Predictions automatically capitalize known proper nouns (names, places, brands, days/months).

- **Built-in**: `data/proper_nouns.txt` (~8,000 entries from US Census + community datasets) loaded into `ngram_predictor.capitalization` on startup.
- **Learned**: When a user types a word with non-trivial capitalization (e.g., "iPhone", "Owen") and completes it with space, the preferred form is saved via `learn_capitalization()`.
- **User edits**: Right-click a prediction → Edit to correct capitalization. This calls `editPrediction()` which inserts the corrected word and saves the capitalization permanently.
- **Applied at output**: `hybrid_predictor._merge_predictions()` calls `ngram.get_capitalized()` on each result before returning to QML.
- **Persisted**: The `capitalization` dict is saved in `ngram_model.json`. User overrides merge with built-in proper nouns on load (user wins).

## Where User Data Lives

- **Settings** (layout, theme, toggles): Managed by Qt `Settings` in QML. Auto-saved on change. Stored in OS registry/config automatically by Qt.
- **Prediction model** (learned words/phrases): Saved to disk explicitly or via auto-save on exit.
  - Windows: `%APPDATA%/alpha-osk/models/`
  - Linux: `~/.config/alpha-osk/models/`
  - Files: `ngram_model.json`, `ppm_model.json`
- **Custom vocabulary packs**: Imported by user, stored separately from built-in packs.
  - Built-in: `data/packs/` (in repo — medical, programming, academic, gaming, business)
  - User-imported: `%APPDATA%/alpha-osk/packs/` (Windows) or `~/.config/alpha-osk/packs/` (Linux)
  - Pack format: folder with `dictionary.txt` (required), optional `bigrams.txt`, `trigrams.txt`, `pack.json`

## QML ↔ Python Bridge Pattern

QML calls Python via `@Slot` methods on `KeyboardBridge`. Python emits `Signal`s back to QML. Example flow:

1. QML: `keyboard.pressKey("a")` → calls `KeyboardBridge.pressKey()`
2. Python: synthesizes keystroke, updates context, runs prediction
3. Python: `self.predictionsChanged.emit(predictions)` → Signal
4. QML: binds to `keyboard.predictions` property, updates UI

## Sticky Modifiers (Ctrl, Alt, Win)

Modifier keys are **sticky** — tap once to activate, tap again to deactivate. While active, the modifier is held at the OS level via `hold_modifier()` / `release_modifier()` on the platform synthesizer. This means:

- **Modifier+click works**: e.g., Ctrl+click to open hyperlinks in terminals/browsers.
- **Modifier+key combos work**: e.g., tap Ctrl, then tap C → sends Ctrl+C.
- **Auto-release**: After any key press (character or special), active modifiers are released at the OS level and deactivated.

### Implementation
- `keyboard_bridge.py`: `toggleCtrl()` / `toggleAlt()` / `toggleWin()` call `_synth.hold_modifier()` on activate and `_synth.release_modifier()` on deactivate. All auto-release paths in `pressKey()` and `pressSpecialKey()` also call `release_modifier()`.
- `platform/base.py`: `hold_modifier()` and `release_modifier()` — default no-op.
- `platform/windows.py`: Sends `VK_CONTROL` / `VK_MENU` / `VK_LWIN` key-down or key-up via `SendInput`.
- `platform/linux.py`: Uses `xdotool keydown/keyup` or `ydotool key --key-down/--key-up`.

## Adding a New Setting

1. Add `property bool savedFoo: defaultValue` to `Settings {}` in `Main.qml`
2. Add `property bool foo: appSettings.savedFoo` to root in `Main.qml`
3. Add `property bool foo: defaultValue` to `UnifiedSettingsPanel.qml`
4. Add `SettingsToggle` in the appropriate section of `UnifiedSettingsPanel.qml`
5. Pass property through: `foo: root.foo` in the `Comp.UnifiedSettingsPanel {}` block
6. Handle in `onSettingChanged`: update root, save to appSettings, call bridge if needed
7. If Python needs it: add `@Slot(bool) def setFoo()` to `keyboard_bridge.py`
8. Load on startup in `Component.onCompleted` if it needs to be sent to the bridge

## Adding a New QML Component

1. Create `qml/components/MyComponent.qml`
2. It's auto-discovered — the `components/` directory is imported as `"components" as Comp` in Main.qml
3. Use as `Comp.MyComponent {}` in Main.qml

## Accessibility Profiles

Defined in `src/prediction/fuzzy_recognizer.py`. Six profiles adjust:
- **spatial_uncertainty**: How far off-center a keypress can be (in key-widths)
- **confidence_threshold**: Minimum score to autocorrect
- **prediction_weight**: How much fuzzy candidates influence ranking
- **key_hold_delay**: Milliseconds to ignore jitter/tremor double-taps
- **autocorrect_enabled**: Whether to auto-correct at all

## Testing

```bash
python -m pytest                    # All tests
python -m pytest tests/test_keyboard_bridge.py  # Bridge tests
python -m pytest -k "fuzzy"         # Fuzzy recognizer tests
```

Linting: `ruff check src/`, type checking: `mypy src/`

## Word Suppression

Users can right-click prediction pills to:
- **Remove from vocabulary** — adds to `ngram_predictor.blacklist` (word never appears again)
- **Bad suggestion** — increments `ngram_predictor.dispreference` (word is downweighted by `1 / (1 + count * 0.5)`)

Both are persisted in `ngram_model.json` and applied in `hybrid_predictor._merge_predictions()`.

### Restoring Suppressed Words
In the Model Visualization dashboard (Settings → Tools → Language Model Visualization → Dashboard tab → Suppressed Words), blacklisted and dispreferred words display as clickable tags. Click a tag to restore it.

Bridge slots: `keyboard.unblacklistWord(word)`, `keyboard.undisprefer(word)`.

### Auto-Rehabilitation
If a user manually types a blacklisted word 3 times (completing it with space), the word is automatically restored to predictions. Tracked via `ngram_predictor._blacklist_type_count`, persisted in `ngram_model.json`.

## Model Visualization

Accessed via Settings → Tools → Language Model Visualization. Three tabs:
- **Word Cloud** — circle-packed bubble chart of top words, sized by frequency
- **Word Flow** — network graph of bigram word→word connections
- **Dashboard** — stats cards, top words bar chart, interactive suppressed words, top word pairs

Data provided by `keyboard_bridge.getVisualizationData()` → `ModelVisualization.qml`.

## Privacy Mode & Password Detection

Protects sensitive input (passwords, PINs) from leaking into the prediction model.

### How it works
- **Auto-detection** (Windows): A `QTimer` polls every 500ms, calling `is_password_field()` from `src/platform/password_detect.py`. Uses Windows UI Automation COM (`IUIAutomation::GetFocusedElement` → `UIA_IsPasswordPropertyId`) to detect password fields in native apps and browsers. Falls back to Win32 `EM_GETPASSWORDCHAR` if UIA fails.
- **Manual toggle**: Play/pause icon in the title bar (Canvas-drawn). Overrides auto-detection.
- **When active**: Keystrokes still reach the OS, but `_current_word`, predictions, and learning are all suppressed. The prediction bar shows "Learning paused".

### Key files
- `src/platform/password_detect.py` — platform-specific detection (UIA COM via ctypes)
- `src/keyboard_bridge.py` — `_privacy_mode` flag, `_check_password_field()` timer, `setPrivacyMode()` slot

### Linux
Auto-detection not yet implemented. Users should use the manual toggle.

## Themes

Defined in `themeData` in `Main.qml`. Each theme has: `name`, `background`, `keyColor`, `keyPressed`, `textColor`, `accent`, `border`, `animation`.

**9 themes**: Dark, Light, Ocean, Forest, Amethyst, Vaporwave, Blackboard, Typewriter, Spaceship.

Theme colors flow to all components: main keyboard keys, prediction pills, nav panel, numpad, title bar icons, and active key states (NumLock, Shift, etc.). `KeyButton.qml` auto-computes text contrast on active/pressed states using luminance.

**Animations** (optional per theme): Canvas overlay at 15% opacity. Vaporwave has gradient shift, Spaceship has twinkling stars.

Theme picker in settings shows labeled color swatches with mini key previews.

## Vocabulary

- **Base**: Google 10K wordlist (`data/google-10000-english-usa-no-swears.txt`) + 10K supplement (`data/google-20000-supplement.txt`, filtered for explicit content). ~20K total regular words.
- **Packs**: Medical, Programming, Academic, Gaming, Business, NSFW. Toggled in Settings → Vocabulary Packs. NSFW is off by default.
- **Numpad**: Toggles between numbers and navigation keys (Home/End/PgUp/PgDn/arrows/Ins/Del) via NumLock. Key 5 is blank in nav mode.

## Analytics & Quality Scoring

`src/analytics.py` tracks session and all-time stats. All-time stats persist to `<config_dir>/analytics.json`.

**Prediction Quality Score** (0-100) is a weighted combination:
- Keystroke savings rate (40%) — how much effort predictions save
- Prediction hit rate (25%) — how often predictions are used
- Rank accuracy (20%) — how often users pick the #1 suggestion
- Low correction rate (15%) — inverse of backspace rate

## Federated Learning

Design doc at `docs/FEDERATED_LEARNING.md`. Not yet implemented — Phase 1 (local delta computation) is the next step.

## Git Conventions

Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`

## Things to Watch Out For

- `Main.qml` is large (~1300 lines). The keyboard rows are data-driven from `keyboard.getLayoutRows()`.
- `keyboard_bridge.py` is the biggest Python file (~1000 lines). It handles everything: keys, modifiers, context, predictions, settings, privacy mode.
- Window flags are critical — the keyboard must never steal focus from the user's app. See `_apply_window_flags()` in `keyboard_app.py`.
- On Windows, `WS_EX_NOACTIVATE` is set via Win32 API (not just Qt flags).
- Key spacing and sizing are calculated dynamically from window width — see `keyW`, `keyH`, `keySpacing`, `layoutFixedPixels` properties in Main.qml.
- The title bar has play/pause (privacy), ⚙ (settings), minimize, and close. Help and visualization are in Settings → Tools.
- Predictions clear automatically when the window loses focus (`onActiveChanged` in Main.qml) so context doesn't go stale.
