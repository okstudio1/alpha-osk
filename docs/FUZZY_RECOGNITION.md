# Fuzzy / Spatial Recognition — Design

Fuzzy recognition is Alpha-OSK's **accessibility-first spelling / typing
error corrector**.  The idea is simple: when someone with tremor or
limited precision aims for `h`, they might land on `g`, `j`, or `y`
instead.  The recognizer models this spatial uncertainty and proposes
the word the user most likely *meant* to type.

Implementation: `src/prediction/fuzzy_recognizer.py`.

## Three Collaborating Classes

| Class | Responsibility |
|-------|----------------|
| `SpatialKeyModel` | Given a clicked key, returns P(intended = k) for nearby keys. |
| `FuzzyWordGenerator` | Expands a typed string into candidate strings using the spatial distribution, intersects with the dictionary. |
| `FuzzyRecognizer` | Public entry point. Wires the above together and decides whether to *auto*-correct. |

## Spatial Model — `SpatialKeyModel`

### Key layout

`QWERTY_POSITIONS` assigns each letter a `(row, col)` with the standard
stagger (home row offset +0.25, bottom row +0.75).  Units are
key-widths.

### P(intended | clicked)

For a clicked key, the neighbour cache stores every key within
`1.5 × uncertainty_radius`.  The probability another key was *intended*
is a Gaussian on Euclidean key-distance:

```
sigma   = uncertainty_radius / 2
P(key)  = exp( − distance² / (2 · sigma²) )     if distance ≤ radius
P(key)  = 0                                      otherwise
```

Divide-and-normalize so probabilities sum to 1.  The clicked key always
has distance 0 → highest probability, and probability falls off
smoothly with distance.  Sigma is half the radius so ~95% of the
Gaussian mass sits inside the configured uncertainty radius.

### Neighbour cache

Built once in `_build_neighbor_cache`: O(K²) in the number of keys
(~676 pair checks for 26 letters — cheap).  Rebuilt only if
`set_uncertainty_radius` is called at runtime; otherwise the cache
is permanent.

## Candidate Generation — `FuzzyWordGenerator`

Expands a typed string into weighted candidate strings, then
intersects with the dictionary.

```
_generate_fuzzy_sequences("hel"):
  for each char c in typed:
    multiply every (prefix, p) in beam by every (c', p(c'|c))
    prune: drop any combined probability < min_prob (default 0.001)
    keep top 2 · max_candidates (100) by probability
```

This is a **beam search over possible typing interpretations**, one
character per step.  For a 5-letter word with an average of 6 neighbours
per key, the unpruned search would be 7,776 paths; pruning keeps it at
a few hundred.

`generate_candidates` then filters the surviving sequences to those
that are in `self.dictionary`, returning `(word, probability)` sorted
by probability.

### `get_correction(typed_word, context)`

Returns the top candidate **only if the typed word is not itself in the
dictionary**.  (If the user typed a valid word, we don't "correct" it.)

## Tunable Parameters

There used to be six pre-built "accessibility profiles" (Precise,
Normal, Mild/Moderate/Severe Tremor, Limited Mobility) that swapped
parameter sets at runtime.  They were confusing — most users picked
"Normal" and never looked at the others, and the parameters that
actually mattered (`spatial_uncertainty`, `confidence_threshold`,
`prediction_weight`) are different shades of the same dial.  Now the
recognizer uses one set of generous, Gboard-leaning constants:

| Constant | Value | What it controls |
|----------|-------|------------------|
| `DEFAULT_SPATIAL_UNCERTAINTY` | 1.4 | Radius (in key-widths) the Gaussian covers.  Larger than the old "Normal" 1.0 — picks up diagonal neighbours so a near-miss still surfaces the right word. |
| `DEFAULT_CONFIDENCE_THRESHOLD` | 0.65 | Auto-correct only if the top candidate's probability clears this.  Lower than the old "Normal" 0.8 — more willing to fix obvious typos. |
| `DEFAULT_PREDICTION_WEIGHT` | 0.6 | How heavily `HybridPredictor._merge_predictions` trusts fuzzy candidates vs. n-gram. |
| `DEFAULT_MIN_PROB` | 0.001 | Beam-search pruning threshold inside `_generate_fuzzy_sequences`.  Lower than the old 0.01 so a single-substitution path can survive across a 5+ character word. |

If you need to tune behaviour for a specific user, override these on
the `FuzzyRecognizer` instance — they're class attributes, so a
subclass or instance assignment is enough.  The profile UI in settings
is gone.

## How it Plugs into the Hybrid Engine

`HybridPredictor.predict` pulls fuzzy predictions for the current
partial word via `get_fuzzy_predictions`.  Those candidates are merged
with n-gram and PPM suggestions using `FuzzyRecognizer.prediction_weight`
as the fuzzy score multiplier — see `docs/HYBRID_MERGING.md`.

`HybridPredictor.check_autocorrect` calls `should_autocorrect`, which
returns a corrected word only if the top candidate's probability ≥
`confidence_threshold`.

## Known Gaps / Future Work

The list matches `CLAUDE.md`'s "Prediction & Autocorrect — Architecture
Notes" section:

1. **Edit-distance generation is O(branches · length)** — a five-letter
   word with six-neighbour keys is fine, but longer words and bigger
   alphabets get expensive fast.  Replacing the beam search with
   **SymSpell** (Garbe 2012 — precomputed deletion variants, O(1)
   hash lookup) would be ~1000× faster on a 20K dictionary.
2. **No direct edit-distance scoring** — we handle spatial *substitution*
   but not insertion, deletion, or transposition.  Real autocorrectors
   (LatinIME, Hunspell) use Damerau–Levenshtein with key-distance
   weights on substitution.  Alpha-OSK effectively caps at
   substitutions-only with Gaussian weighting.
3. **Autocorrect doesn't compete with the literal word** — commercial
   keyboards only auto-replace when the correction scores **1.5–2×
   higher** than what the user actually typed.  We use a flat
   confidence threshold, which over-corrects near the boundary.
4. **No n-gram prior in fuzzy ranking** — context (`the ___` is almost
   certainly "is/was/one/…") doesn't influence which fuzzy candidate
   wins.  Passing `context` through to `FuzzyWordGenerator` and
   re-scoring with `NgramPredictor.bigrams` would help.

## References

- Goodman, J., Venolia, G., Steury, K., & Parker, C. (2002).
  *Language modeling for soft keyboards.*  IUI.  (Key-distance weighted
  edit distance for soft keyboards — the LatinIME ancestor.)
- Kernighan, M. D., Church, K. W., & Gale, W. A. (1990).
  *A spelling correction program based on a noisy channel model.*
  COLING.  (Classical substitution/insertion/deletion/transposition
  model — still the textbook reference for edit-distance scoring.)
- Garbe, W. (2012).  *1000× faster spelling correction algorithm.*
  (SymSpell — precomputed-deletions approach.)
- Damerau, F. J. (1964).  *A technique for computer detection and
  correction of spelling errors.*  CACM.
