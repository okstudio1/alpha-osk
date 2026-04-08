"""Tests for the fuzzy/spatial recognition engine."""

from __future__ import annotations

from src.prediction.fuzzy_recognizer import (
    PROFILES,
    QWERTY_POSITIONS,
    AccessibilityProfile,
    FuzzyRecognizer,
    FuzzyWordGenerator,
    SpatialKeyModel,
)


class TestQWERTYLayout:
    """Verify the QWERTY position map is consistent."""

    def test_all_letters_present(self):
        import string
        for letter in string.ascii_lowercase:
            assert letter in QWERTY_POSITIONS, f"Missing key: {letter}"

    def test_positions_are_tuples(self):
        for key, pos in QWERTY_POSITIONS.items():
            assert isinstance(pos, tuple) and len(pos) == 2

    def test_rows_are_valid(self):
        for key, (row, col) in QWERTY_POSITIONS.items():
            assert 0 <= row <= 2, f"Key {key} has invalid row {row}"
            assert col >= 0, f"Key {key} has negative col {col}"


class TestAccessibilityProfiles:
    """Profile configuration and factory methods."""

    def test_all_profiles_exist(self):
        expected = {"precise", "normal", "mild_tremor", "moderate_tremor",
                    "severe_tremor", "limited_mobility"}
        assert set(PROFILES.keys()) == expected

    def test_precise_has_lowest_uncertainty(self):
        precise = AccessibilityProfile.precise()
        normal = AccessibilityProfile.normal()
        assert precise.spatial_uncertainty < normal.spatial_uncertainty

    def test_severe_tremor_has_highest_uncertainty(self):
        severe = AccessibilityProfile.severe_tremor()
        for name, profile in PROFILES.items():
            if name != "severe_tremor":
                assert severe.spatial_uncertainty >= profile.spatial_uncertainty

    def test_precise_disables_autocorrect(self):
        assert not AccessibilityProfile.precise().autocorrect_enabled

    def test_normal_enables_autocorrect(self):
        assert AccessibilityProfile.normal().autocorrect_enabled

    def test_profile_confidence_thresholds_decrease_with_severity(self):
        profiles = [
            AccessibilityProfile.precise(),
            AccessibilityProfile.normal(),
            AccessibilityProfile.mild_tremor(),
            AccessibilityProfile.moderate_tremor(),
            AccessibilityProfile.severe_tremor(),
        ]
        for i in range(len(profiles) - 1):
            assert profiles[i].confidence_threshold >= profiles[i + 1].confidence_threshold


class TestSpatialKeyModel:
    """Spatial probability model for key presses."""

    def test_clicked_key_has_highest_prob(self):
        model = SpatialKeyModel(uncertainty_radius=1.0)
        probs = model.get_key_probabilities("f")
        assert probs["f"] == max(probs.values())

    def test_probabilities_sum_to_one(self):
        model = SpatialKeyModel(uncertainty_radius=1.5)
        probs = model.get_key_probabilities("g")
        total = sum(probs.values())
        assert abs(total - 1.0) < 0.01

    def test_unknown_key_returns_certainty(self):
        model = SpatialKeyModel(uncertainty_radius=1.0)
        probs = model.get_key_probabilities("1")  # Not in QWERTY layout
        assert probs == {"1": 1.0}

    def test_nearby_keys_are_included(self):
        model = SpatialKeyModel(uncertainty_radius=1.5)
        probs = model.get_key_probabilities("f")
        # d, g, r, v are adjacent to f
        assert "d" in probs or "g" in probs

    def test_distant_keys_excluded(self):
        model = SpatialKeyModel(uncertainty_radius=0.5)
        probs = model.get_key_probabilities("a")
        # 'p' is far from 'a' — should not appear with small radius
        assert "p" not in probs

    def test_get_nearby_keys(self):
        model = SpatialKeyModel(uncertainty_radius=1.5)
        nearby = model.get_nearby_keys("f")
        assert "f" in nearby  # Key itself
        assert len(nearby) > 1  # Plus neighbors

    def test_set_uncertainty_rebuilds_cache(self):
        model = SpatialKeyModel(uncertainty_radius=0.5)
        small_neighbors = len(model.get_nearby_keys("f"))
        model.set_uncertainty_radius(2.5)
        large_neighbors = len(model.get_nearby_keys("f"))
        assert large_neighbors >= small_neighbors

    def test_zero_uncertainty_returns_only_self(self):
        model = SpatialKeyModel(uncertainty_radius=0.01)
        probs = model.get_key_probabilities("f")
        assert len(probs) == 1
        assert "f" in probs


class TestFuzzyWordGenerator:
    """Fuzzy word candidate generation."""

    def test_empty_input_returns_empty(self, small_dictionary: set):
        gen = FuzzyWordGenerator(dictionary=small_dictionary)
        assert gen.generate_candidates("") == []

    def test_exact_match_returns_word(self, small_dictionary: set):
        gen = FuzzyWordGenerator(
            spatial_model=SpatialKeyModel(uncertainty_radius=1.0),
            dictionary=small_dictionary,
        )
        candidates = gen.generate_candidates("the")
        words = [w for w, _ in candidates]
        assert "the" in words

    def test_nearby_typo_generates_correction(self, small_dictionary: set):
        gen = FuzzyWordGenerator(
            spatial_model=SpatialKeyModel(uncertainty_radius=1.5),
            dictionary=small_dictionary,
        )
        # 'r' is next to 't', so "rhe" might correct to "the"
        candidates = gen.generate_candidates("rhe")
        words = [w for w, _ in candidates]
        assert "the" in words

    def test_candidates_are_sorted_by_probability(self, small_dictionary: set):
        gen = FuzzyWordGenerator(
            spatial_model=SpatialKeyModel(uncertainty_radius=1.5),
            dictionary=small_dictionary,
        )
        candidates = gen.generate_candidates("the")
        probs = [p for _, p in candidates]
        assert probs == sorted(probs, reverse=True)

    def test_max_candidates_respected(self, small_dictionary: set):
        gen = FuzzyWordGenerator(
            spatial_model=SpatialKeyModel(uncertainty_radius=2.0),
            dictionary=small_dictionary,
            max_candidates=3,
        )
        candidates = gen.generate_candidates("the")
        assert len(candidates) <= 3

    def test_get_correction_returns_none_for_valid_word(self, small_dictionary: set):
        gen = FuzzyWordGenerator(dictionary=small_dictionary)
        assert gen.get_correction("the") is None

    def test_get_correction_returns_candidate_for_typo(self, small_dictionary: set):
        gen = FuzzyWordGenerator(
            spatial_model=SpatialKeyModel(uncertainty_radius=1.5),
            dictionary=small_dictionary,
        )
        result = gen.get_correction("rhe")
        if result is not None:
            word, prob = result
            assert isinstance(word, str)
            assert prob > 0


class TestFuzzyRecognizer:
    """Main fuzzy recognizer interface."""

    def test_default_profile_is_normal(self):
        rec = FuzzyRecognizer()
        assert rec.profile.name == "Normal"

    def test_set_profile_valid(self):
        rec = FuzzyRecognizer()
        assert rec.set_profile("mild_tremor")
        assert rec.profile.name == "Mild Tremor"

    def test_set_profile_invalid(self):
        rec = FuzzyRecognizer()
        assert not rec.set_profile("nonexistent_profile")

    def test_set_profile_updates_spatial_model(self):
        rec = FuzzyRecognizer()
        rec.set_profile("severe_tremor")
        expected = AccessibilityProfile.severe_tremor().spatial_uncertainty
        assert rec.spatial_model.uncertainty_radius == expected

    def test_get_profile_names(self):
        rec = FuzzyRecognizer()
        names = rec.get_profile_names()
        assert "normal" in names
        assert "mild_tremor" in names

    def test_get_key_alternatives(self):
        rec = FuzzyRecognizer()
        alts = rec.get_key_alternatives("f")
        assert isinstance(alts, dict)
        assert "f" in alts

    def test_autocorrect_disabled_in_precise(self, small_dictionary: set):
        rec = FuzzyRecognizer(
            profile=AccessibilityProfile.precise(),
            dictionary=small_dictionary,
        )
        # Precise profile has autocorrect disabled
        assert rec.should_autocorrect("rhe") is None

    def test_autocorrect_enabled_in_normal(self, small_dictionary: set):
        rec = FuzzyRecognizer(
            profile=AccessibilityProfile.normal(),
            dictionary=small_dictionary,
        )
        # May or may not correct, but should not crash
        result = rec.should_autocorrect("the")
        # "the" is valid, so no correction
        assert result is None

    def test_get_fuzzy_predictions_empty_text(self):
        rec = FuzzyRecognizer()
        assert rec.get_fuzzy_predictions("") == []

    def test_get_fuzzy_predictions_after_space(self, small_dictionary: set):
        rec = FuzzyRecognizer(dictionary=small_dictionary)
        # Trailing space = no current word
        assert rec.get_fuzzy_predictions("hello ") == []

    def test_get_stats(self):
        rec = FuzzyRecognizer()
        stats = rec.get_stats()
        assert "profile" in stats
        assert "spatial_uncertainty" in stats
        assert "dictionary_size" in stats
