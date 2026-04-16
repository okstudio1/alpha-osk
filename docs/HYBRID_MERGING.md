# Hybrid Prediction — How the Predictors Combine

Alpha-OSK's public prediction surface is `HybridPredictor.predict`, but
under the hood four models vote on every suggestion and the final list
is a weighted, filtered, decorated merge.  This doc explains the
scoring rules in `HybridPredictor._merge_predictions` and how the
pieces fit.

Implementation: `src/prediction/hybrid_predictor.py`.

Design philosophy matches Presage and early Gboard/LatinIME: **fast
complementary predictors that each do one thing well, merged by linear
interpolation, with the word-level model dominating and the others
filling gaps**.

## The Four Predictors

| Predictor | File | Answers the question |
|-----------|------|----------------------|
| N-gram | `ngram_predictor.py` | "What word usually follows this word?" — unigram + bigram + trigram word counts. |
| PPM | `ppm_predictor.py` | "Given these characters, what character is likely next?"  Variable-order character model. |
| Fuzzy | `fuzzy_recognizer.py` | "Given the user probably misaimed, what word did they mean?"  Spatial error correction. |
| Transformer | `transformer_predictor.py` | "Re-rank the top candidates with an LLM."  Optional, async, off by default. |

Each runs on every keystroke (except the LLM, which is async and
opt-in).  `predict()` calls them in turn, then hands off to
`_merge_predictions`.

## The Core Merge

`_merge_predictions(ngram, ppm, fuzzy, n)`:

```
# 1. Score by source
is_next_word   = context ends with " "
ngram_weight   = 3.0  if is_next_word else 1.0
ppm_weight     = 0.3  if is_next_word else 0.8
fuzzy_weight   = profile.prediction_weight   # 0.3–0.8 by profile

for i, word in enumerate(ngram):
    scores[word] += ngram_weight / (i + 1)
for i, word in enumerate(ppm):
    scores[word] += ppm_weight   / (i + 1)
for i, word in enumerate(fuzzy):
    scores[word] += fuzzy_weight / (i + 1)

# 2. Penalise dispreferred words
for word in scores:
    dp = ngram.get_dispreference(word)
    if dp > 0:
        scores[word] /= (1 + dp · 0.5)

# 3. Sort, validate, capitalise, return top n
```

### Why those weights?

| Situation | N-gram | PPM | Why |
|-----------|--------|-----|-----|
| **Next-word** (space at end) | 3.0 | 0.3 | N-gram *is* the next-word authority; PPM produces character fragments that look like words but aren't ranked by word frequency.  Trusting PPM here produces noise. |
| **Mid-word** (completion) | 1.0 | 0.8 | N-gram still knows which dictionary words are common, but PPM is genuinely useful for partial prefixes the dictionary hasn't seen yet. |
| Fuzzy | profile | profile | Precise users barely want fuzzy (0.3); severe-tremor users want it almost as loud as n-gram (0.8).  See `docs/FUZZY_RECOGNITION.md`. |

The `/ (i + 1)` is positional decay — rank-1 matters more than rank-5
from the same source.  It's linear, not exponential, so rank-10
still contributes roughly 10% of rank-1.

### Short-word filter

Two-letter words (`it`, `an`, `is`, `of`, …) are excluded from
**next-word** predictions to keep the pill bar populated with
higher-information content.  The literal `"i"` is whitelisted because
it's always grammatically plausible.  Mid-word completions bypass this
filter entirely — users should still be able to complete short words.

## Validation — `_is_valid_word`

Every candidate must:

1. Not be in `ngram.blacklist` (user explicitly suppressed it).
2. Be in `ngram.unigrams` (built-in dictionary + user vocabulary),
   **or** be one of ~30 hardcoded essential short words
   (`{"i","a","an","am","as","at","be",…}`).

This filter runs *during* the scoring loop, so blacklisted or
off-dictionary hallucinations from PPM never make it into `scores`.

## Dispreference Penalty

Users right-click a prediction and mark it "bad".  That increments
`ngram.dispreference[word]`.  At merge time:

```
scores[word] /= (1 + dispreference[word] · 0.5)
```

So one "bad" press halves the score; two presses cut it by 33% more;
it's monotonic and never hits zero.  Words can therefore recover if
the user starts typing them organically again (see auto-rehabilitation
below).

## Capitalisation at Output

Right before returning, each winning word goes through
`ngram.get_capitalized(word, sentence_start)` — the three-tier model
described in `CLAUDE.md`:

1. **Always capitalise**: `I`, `I'm`, `I'll`, `I've`, `I'd`.
2. **Sentence-start only**: ambiguous proper nouns that are also
   common English words (`will`, `jack`, `may`, `mark`) — capitalised
   only after `.!?` or at input start.
3. **Unambiguous proper nouns**: `Monday`, `Paris`, `iPhone`, `Owen`,
   plus user-taught casings.

`sentence_start` is computed by checking whether the trimmed context
ends with `.`, `!`, `?`, `\n`, or is empty.

## The LLM Refinement Layer

If `enable_llm=True` and `TransformerPredictor` loaded successfully,
`predict_with_refinement` runs in two phases:

1. **Instant** — `predict()` returns the hybrid top-N right away.
   `predictionsReady` is emitted.  UI renders.
2. **Async** — `_refine_async` sends the top `n · 3` candidates plus
   context to the transformer in a background thread.  When it
   returns, `predictionsRefined` fires, but only if the user hasn't
   typed anything since (context match).

So the hybrid merge is always the primary experience; the LLM is a
*rerankier* that can quietly improve the order, never block, and
never produce hallucinations (it can only reorder the candidates
we already know are valid).

## Auto-Rehabilitation

If the user types a previously-blacklisted word 3 times in a row
(detected in `ngram.record_typed_word`), the word is automatically
un-blacklisted.  Applies to manual typing only, not prediction
selection — we assume if you keep typing it, you want it back.

## Learning Paths

User actions feed back into the models:

| Trigger | What gets learned |
|---------|-------------------|
| Word completed with space | n-gram unigrams/bigrams/trigrams, PPM trie, capitalisation |
| Sentence ended (`.!?`) | Full sentence re-trains n-grams + PPM |
| Prediction selected | Word boosted (`learn_from_selection`), context→word association recorded |
| Prediction edited via right-click → "Edit" | Capitalisation recorded permanently (`set_capitalization`) |
| Word right-click → "Remove" | Blacklist entry added |
| Word right-click → "Bad suggestion" | Dispreference incremented |

All persisted to `ngram_model.json` + `ppm_model.json` on explicit
save or auto-save-on-exit.

## Personal vs. Base Vocabulary (split-table scoring)

The n-gram unigram score inside `NgramPredictor.predict` blends two
separate tables in probability space:

| Table | Source | Updated by |
|-------|--------|-----------|
| `_base_unigrams` | Google 10K + 20K supplement + `data/base_dictionary.txt` + fallback common words | Loaded at startup / `_learn_base`.  Does not change during use. |
| `user_vocab` | The user's actual typing | `learn()` / `learn_word()`.  Recency-decayed. |

Scoring for a partial-prefix candidate:

```
alpha   = personal_weight   (default 0.7)
P_user  = user_vocab[w]    / _user_total
P_base  = _base_unigrams[w] / _base_total
score   = SCALE · [ alpha · P_user + (1 − alpha) · P_base ]
```

`SCALE = 100,000` brings the interpolated probability into the same
magnitude as the bigram/trigram scores added earlier in `predict`, so
context bonuses still move the needle.

**`_user_total` is tracked incrementally** — `learn`, `learn_word`,
`_apply_decay`, `clear_user_data`, and `load` all keep it equal to
`sum(user_vocab.values())`.  Don't recompute the sum in `predict()`;
the invariant is covered by
`tests/test_ngram_predictor.py::TestUserTotalIncremental`.

### Why the split matters

The old merged scheme stored base-dictionary frequencies and personal
typing counts in the **same** `unigrams` dict.  The Google 10K seeds
top words at ~10,000 while a personal word typed 10 times sat at 10.
The multiplicative user boost `(1 + count · 0.1)` couldn't close that
gap — a word like "Claude" typed 10 times scored ~10, while "can"
scored ~5,000.  Personal vocabulary effectively never surfaced.

Under split-table scoring, `P_user(claude) = 10 / user_total` is
~0.01 after a few hundred words of typing; at alpha = 0.7 that gives
7 "units" of score, which beats the top dictionary word's
`0.3 · 0.002 · 100000 = 60` by an order of magnitude once enough
personal use accumulates.  The knob to tune this balance is
`NgramPredictor.personal_weight`.

### Known limits

- **Early-typing dominance.**  With only a handful of user_vocab
  entries, any one word has `P_user ≈ 1` and dominates regardless of
  alpha.  Works itself out after ~100 words of typing; could be
  smoothed with a `max(user_total, N)` floor if it bites.
- **Bigrams/trigrams are still merged.**  `bigrams` and `trigrams`
  hold both base-loaded and user-learned counts together, so the
  same "base drowns personal" problem exists for context predictions
  (`hi ___`).  Worth splitting next if the unigram fix helps.

## Recency Decay

Every `_decay_interval` learn calls, `ngram._apply_decay` multiplies
all user-vocab and user-learned bigram counts by `_decay_factor` (0.95
by default).  This prevents a flurry of typing on one topic from
dominating predictions months later.  PPM does **not** currently decay
— see `docs/PPM.md` "Known Limits".

## Trade-offs Baked into the Weights

- **N-gram >> PPM for next word** — Deliberately harsh.  If you want
  PPM to contribute more to next-word, raise `ppm_weight` in
  `_merge_predictions`; the cost is noisier predictions when the
  context is clear.
- **Fuzzy weight is profile-driven** — More tremor → more aggressive
  spatial correction.  This is the single biggest user-facing knob;
  the Precise profile effectively turns fuzzy off by weight (0.3) *and*
  by disabling autocorrect.
- **Positional decay is linear** — Rank-based, not probability-based.
  Fine for short lists; if `n` grew to 20+, an exponential decay
  would better reflect how users actually scan pill bars.
- **LLM is a rerankier, not a generator** — By design, it can only
  reorder the hybrid candidates, preserving vocabulary/blacklist
  guarantees.

## Known Gaps / Future Work

1. **Unified scoring with the literal typed word.**  Commercial
   keyboards score the literal typed characters as one of the
   candidates, so autocorrect only fires when an alternative scores
   1.5–2× higher.  We don't — autocorrect uses a flat confidence
   threshold.  (Also called out in `docs/FUZZY_RECOGNITION.md`.)
2. **Key-distance weights in the final ranking.**  Fuzzy's spatial
   model feeds candidate generation but not final merge scores.  A
   nearby-key match should count more than a far-key match even
   after dictionary filtering.
3. **Bigram prior on fuzzy candidates.**  When the user types `teh`
   after `to`, `the` is vastly more likely than `ten` or `tea`
   regardless of spatial scores — but we don't currently re-score
   fuzzy candidates against the n-gram bigram table.
4. **LLM could suggest new candidates, not just reorder.**  Current
   implementation is defensive; a more integrated path would let the
   LLM propose words outside the candidate list (with sandboxing).

## Public API for External Callers

Code outside `src/prediction/` should go through `HybridPredictor`, not
reach into `_ngram` / `_ppm` / `_fuzzy`.  The bridge and anything else
that needs raw data should use these forwarders:

| Method | Returns | Used by |
|--------|---------|---------|
| `get_unigram_freqs()` | merged `unigrams` dict (base + user) | `keyboard_bridge.processSwipe` (candidate set for the swipe decoder) |
| `get_capitalized(word, sentence_start)` | `str` | same, to render "iPhone" / "Owen" correctly on decoded swipes |
| `learn`, `learn_word`, `learn_from_selection`, `predict`, `predict_with_refinement` | — | all normal prediction paths |
| `blacklist_word`, `unblacklist_word`, `mark_bad_suggestion`, `remove_dispreference` | — | right-click word suppression |
| `set_accessibility_profile`, `get_accessibility_profiles`, `get_current_profile` | — | accessibility settings UI |
| `enable_vocabulary_pack`, `disable_vocabulary_pack`, `import_vocabulary_pack` | — | vocabulary-pack UI |

If you need data that isn't exposed, add a new forwarder here rather
than reaching through private attributes.  Private access from the
bridge or UI was removed during the security review; don't re-introduce
it.  CLAUDE.md "Things to Watch Out For" calls this out.

## References

- Presage — https://presage.sourceforge.io/ (pluggable predictor
  architecture that inspired the hybrid merge design).
- LatinIME (AOSP) — trie-based dictionary with weighted edit distance
  and n-gram LM scoring.
- Dasher — `docs/PPM.md` for full references.
- Goodman, Venolia, Steury, & Parker (2002).  *Language modeling for
  soft keyboards.*  IUI.  (Unified probabilistic model for soft
  keyboards.)
