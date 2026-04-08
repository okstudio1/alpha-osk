"""Tests for the PPM (Prediction by Partial Matching) engine."""

from __future__ import annotations

from pathlib import Path

from src.prediction.ppm_predictor import PPMNode, PPMPredictor, PPMWordPredictor


class TestPPMNode:
    """PPMNode data structure."""

    def test_new_node_has_zero_count(self):
        node = PPMNode()
        assert node.count == 0
        assert node.children == {}

    def test_add_child_creates_node(self):
        node = PPMNode()
        child = node.add_child("a")
        assert isinstance(child, PPMNode)
        assert "a" in node.children

    def test_add_child_is_idempotent(self):
        node = PPMNode()
        child1 = node.add_child("a")
        child2 = node.add_child("a")
        assert child1 is child2

    def test_get_child_returns_none_for_missing(self):
        node = PPMNode()
        assert node.get_child("z") is None

    def test_total_children_count(self):
        node = PPMNode()
        node.add_child("a").count = 5
        node.add_child("b").count = 3
        assert node.total_children_count() == 8

    def test_num_children(self):
        node = PPMNode()
        node.add_child("a")
        node.add_child("b")
        node.add_child("c")
        assert node.num_children() == 3


class TestPPMTraining:
    """Training and model building."""

    def test_train_increases_total_chars(self):
        ppm = PPMPredictor()
        ppm.train("hello world")
        assert ppm.total_chars > 0

    def test_train_short_text_is_safe(self):
        ppm = PPMPredictor()
        ppm.train("a")  # len < 2, should be a no-op
        assert ppm.total_chars == 0

    def test_train_builds_trie(self):
        ppm = PPMPredictor()
        ppm.train("abc")
        # Root should have children for a, b, c
        assert ppm.root.num_children() > 0

    def test_normalization_lowercases(self):
        ppm = PPMPredictor()
        result = ppm._normalize("Hello WORLD")
        assert result == "hello world"

    def test_normalization_replaces_unknown_chars(self):
        ppm = PPMPredictor()
        result = ppm._normalize("hello@world")
        # '@' not in default alphabet, replaced with space
        assert "@" not in result


class TestPPMProbabilities:
    """Probability distribution behavior."""

    def test_probabilities_sum_to_one(self):
        ppm = PPMPredictor()
        ppm.train("the quick brown fox jumps over the lazy dog")
        probs = ppm.get_probabilities("the ")
        total = sum(probs.values())
        assert abs(total - 1.0) < 0.01

    def test_probabilities_are_non_negative(self):
        ppm = PPMPredictor()
        ppm.train("hello world")
        probs = ppm.get_probabilities("hel")
        assert all(p >= 0 for p in probs.values())

    def test_probabilities_cover_alphabet(self):
        ppm = PPMPredictor()
        ppm.train("some text to train on")
        probs = ppm.get_probabilities("so")
        # Should have probability for every char in alphabet
        assert len(probs) == len(ppm.alphabet)

    def test_trained_chars_have_higher_prob(self, sample_corpus: str):
        ppm = PPMPredictor()
        ppm.train(sample_corpus)
        probs = ppm.get_probabilities("th")
        # After training on English text, 'e' should be likely after "th"
        assert probs.get("e", 0) > probs.get("z", 0)

    def test_empty_context_returns_distribution(self):
        ppm = PPMPredictor()
        probs = ppm.get_probabilities("")
        assert len(probs) > 0
        assert abs(sum(probs.values()) - 1.0) < 0.01


class TestPPMEntropy:
    """Entropy calculations."""

    def test_entropy_is_non_negative(self):
        ppm = PPMPredictor()
        ppm.train("hello hello hello")
        entropy = ppm.get_context_entropy("hel")
        assert entropy >= 0

    def test_trained_context_has_lower_entropy(self, sample_corpus: str):
        ppm = PPMPredictor()
        ppm.train(sample_corpus)
        trained_entropy = ppm.get_context_entropy("th")
        untrained_entropy = ppm.get_context_entropy("zq")
        # Trained context should be more predictable (lower entropy)
        assert trained_entropy < untrained_entropy


class TestPPMWordPrediction:
    """Word-level prediction via beam search."""

    def test_predict_word_returns_tuples(self, sample_corpus: str):
        ppm = PPMPredictor()
        ppm.train(sample_corpus)
        results = ppm.predict_word("th", partial="th", n=3)
        assert all(isinstance(r, tuple) and len(r) == 2 for r in results)

    def test_predict_word_completions_start_with_partial(self, sample_corpus: str):
        ppm = PPMPredictor()
        ppm.train(sample_corpus)
        results = ppm.predict_word("", partial="he", n=5)
        for word, _ in results:
            assert word.startswith("he")

    def test_predict_next_chars(self, sample_corpus: str):
        ppm = PPMPredictor()
        ppm.train(sample_corpus)
        results = ppm.predict_next_chars("th", n=3)
        assert len(results) <= 3
        assert all(isinstance(r, tuple) for r in results)


class TestPPMPersistence:
    """Save and load round-trips."""

    def test_save_and_load_preserves_stats(self, tmp_model_dir: Path, sample_corpus: str):
        path = tmp_model_dir / "ppm.json"
        ppm = PPMPredictor()
        ppm.train(sample_corpus)
        original_stats = ppm.get_stats()
        ppm.save(path)

        loaded = PPMPredictor()
        loaded.load(path)
        loaded_stats = loaded.get_stats()
        assert loaded_stats["total_chars"] == original_stats["total_chars"]
        assert loaded_stats["max_order"] == original_stats["max_order"]

    def test_save_and_load_preserves_predictions(self, tmp_model_dir: Path, sample_corpus: str):
        path = tmp_model_dir / "ppm.json"
        ppm = PPMPredictor()
        ppm.train(sample_corpus)
        original_probs = ppm.get_probabilities("th")
        ppm.save(path)

        loaded = PPMPredictor()
        loaded.load(path)
        loaded_probs = loaded.get_probabilities("th")
        # Probabilities should be very close
        for char in ppm.alphabet:
            assert abs(original_probs.get(char, 0) - loaded_probs.get(char, 0)) < 0.01

    def test_load_corrupt_file_is_safe(self, tmp_model_dir: Path):
        path = tmp_model_dir / "corrupt.json"
        path.write_text("{bad json")
        ppm = PPMPredictor()
        ppm.load(path)
        # Should not crash, still usable
        probs = ppm.get_probabilities("a")
        assert len(probs) > 0


class TestPPMWordPredictor:
    """Word-level wrapper around PPM."""

    def test_predict_returns_strings(self, sample_corpus: str):
        ppm = PPMPredictor()
        ppm.train(sample_corpus)
        wp = PPMWordPredictor(ppm=ppm, dictionary={"the", "quick", "brown", "help", "hello"})
        results = wp.predict("hel", n=3)
        assert all(isinstance(w, str) for w in results)

    def test_predict_next_word_after_space(self, sample_corpus: str):
        ppm = PPMPredictor()
        ppm.train(sample_corpus)
        wp = PPMWordPredictor(ppm=ppm, dictionary={"the", "quick", "to", "go"})
        results = wp.predict("I want ", n=3)
        # Should predict next word, not complete "want"
        assert all(not w.startswith("want") for w in results)

    def test_learn_adds_to_dictionary(self):
        wp = PPMWordPredictor()
        wp.learn("supercalifragilistic is great")
        assert "supercalifragilistic" in wp.dictionary

    def test_cache_is_populated(self, sample_corpus: str):
        ppm = PPMPredictor()
        ppm.train(sample_corpus)
        wp = PPMWordPredictor(ppm=ppm, dictionary={"the", "help"})
        wp.predict("hel", n=3)
        assert len(wp._completion_cache) > 0

    def test_cache_eviction(self):
        wp = PPMWordPredictor()
        wp._cache_max_size = 5
        # Fill cache beyond max
        for i in range(10):
            wp._completion_cache[f"key{i}"] = [f"word{i}"]
        wp.predict("test", n=1)
        assert len(wp._completion_cache) <= 10  # eviction happens on next predict

    def test_get_stats(self):
        wp = PPMWordPredictor(dictionary={"hello", "world"})
        stats = wp.get_stats()
        assert stats["dictionary_size"] == 2
        assert "cache_size" in stats
