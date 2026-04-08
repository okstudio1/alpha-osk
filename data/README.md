# Training Data

This directory contains the data files that bootstrap Alpha-OSK's prediction engine.

## Files

| File | Purpose | Format |
|------|---------|--------|
| `google-10000-english-usa-no-swears.txt` | Frequency-ranked vocabulary (10K words) | One word per line, ranked by frequency |
| `base_dictionary.txt` | Additional vocabulary for unigram boosting | One word per line. **Never** put multiple words on one line — that creates fake bigrams. |
| `common_bigrams.txt` | Two-word sequences for next-word prediction | `word1 word2` per line, space-separated |
| `common_trigrams.txt` | Three-word sequences for next-word prediction | `word1 word2 word3` per line, space-separated |
| `training_corpus.txt` | Natural sentences for PPM and n-gram training | One sentence per line. Covers greetings, work, tech, accessibility, casual texting, etc. |

## How they're loaded

1. **`NgramPredictor.__init__`** loads `google-10000-english-usa-no-swears.txt` for base unigram frequencies
2. **`HybridPredictor.__init__`** calls:
   - `load_base_dictionary()` — boosts unigrams from `base_dictionary.txt`
   - `load_common_bigrams()` — loads `common_bigrams.txt` with weight 50
   - `load_common_trigrams()` — loads `common_trigrams.txt` with weight 50 (also reinforces contained bigrams with weight 10)
   - `_load_training_corpus()` — trains both n-gram and PPM on `training_corpus.txt`

## Adding training data

- **New words**: Add to `base_dictionary.txt`, one per line
- **New word pairs**: Add to `common_bigrams.txt` as `word1 word2`
- **New word triples**: Add to `common_trigrams.txt` as `word1 word2 word3`
- **New sentences**: Add to `training_corpus.txt`, one sentence per line
- Lines starting with `#` are comments and are skipped

## Vocabulary Packs

Domain-specific vocabulary packs live in `packs/<name>/`. Users can enable/disable them at runtime without restarting.

### Built-in packs

| Pack | Words | Description |
|------|-------|-------------|
| `medical` | ~300 | Conditions, medications, therapy, assistive equipment |
| `programming` | ~350 | Languages, frameworks, CLI, development workflow |
| `academic` | ~300 | Research terms, scientific vocabulary, writing phrases |
| `gaming` | ~200 | Game genres, multiplayer chat, streaming |
| `business` | ~150 | Corporate, finance, management vocabulary |

### Pack format

```
packs/<name>/
├── pack.json          # {"name": "...", "description": "...", "version": 1}
├── dictionary.txt     # One word per line (unigrams only!)
├── bigrams.txt        # word1 word2 per line (optional)
└── trigrams.txt       # word1 word2 word3 per line (optional)
```

### Creating a custom pack

1. Create a directory under `data/packs/` (e.g., `data/packs/chemistry/`)
2. Add `pack.json` with name and description
3. Add `dictionary.txt` with one word per line (**no multi-word entries**)
4. Optionally add `bigrams.txt` and `trigrams.txt`
5. Enable it via the keyboard bridge: `keyboard.enableVocabularyPack("chemistry")`
