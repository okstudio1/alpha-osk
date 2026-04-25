"""
Fuzzy / spatial recognition for typo-tolerant prediction.

Models spatial uncertainty around each key so a press near a key
boundary still surfaces the correct word, the way Gboard does.  No
configurable profiles — there's one default that's tuned to be
generous, because picking among six profiles was confusing and the
extra dials never carried their weight.
"""

from __future__ import annotations

import logging
import math
from typing import Dict, List, Optional, Set, Tuple

_logger = logging.getLogger("FuzzyRecognizer")


# QWERTY layout in (row, col) units.  Rows are offset by the standard
# staggered amount so diagonal distances reflect the physical keyboard.
QWERTY_POSITIONS: Dict[str, Tuple[float, float]] = {
    'q': (0, 0),    'w': (0, 1),    'e': (0, 2),    'r': (0, 3),    't': (0, 4),
    'y': (0, 5),    'u': (0, 6),    'i': (0, 7),    'o': (0, 8),    'p': (0, 9),
    'a': (1, 0.25), 's': (1, 1.25), 'd': (1, 2.25), 'f': (1, 3.25), 'g': (1, 4.25),
    'h': (1, 5.25), 'j': (1, 6.25), 'k': (1, 7.25), 'l': (1, 8.25),
    'z': (2, 0.75), 'x': (2, 1.75), 'c': (2, 2.75), 'v': (2, 3.75), 'b': (2, 4.75),
    'n': (2, 5.75), 'm': (2, 6.75),
}


# Tuned so a press one key off-center still has its true neighbours
# (cardinal + diagonal) in the candidate set.  Larger than the original
# "Normal" profile (1.0) but smaller than the "Mild Tremor" profile
# (1.5) — picks up the diagonals without dragging in second-row noise.
DEFAULT_SPATIAL_UNCERTAINTY = 1.4

# Minimum confidence for ``should_autocorrect`` to fire.
DEFAULT_CONFIDENCE_THRESHOLD = 0.65

# Weight the merger applies to fuzzy candidates against n-gram scores.
DEFAULT_PREDICTION_WEIGHT = 0.6

# Pruning threshold inside the candidate-sequence search.  Lower than
# the original 0.01 so a single-substitution path can survive across a
# 5+ character word — at 0.01 a substituted letter (~0.4 prob) dies
# after about 4 multiplications.
DEFAULT_MIN_PROB = 0.001


class SpatialKeyModel:
    """Probability distribution over intended keys for a given press."""

    def __init__(
        self,
        positions: Optional[Dict[str, Tuple[float, float]]] = None,
        uncertainty_radius: float = DEFAULT_SPATIAL_UNCERTAINTY,
    ):
        self.positions = positions or QWERTY_POSITIONS
        self.uncertainty_radius = uncertainty_radius

        self._neighbors: Dict[str, List[Tuple[str, float]]] = {}
        self._build_neighbor_cache()

    def _build_neighbor_cache(self) -> None:
        for key, pos in self.positions.items():
            neighbors = []
            for other_key, other_pos in self.positions.items():
                dist = self._distance(pos, other_pos)
                # Cache slightly more than the radius so we can change
                # the radius later without re-walking every key pair.
                if dist <= self.uncertainty_radius * 1.5:
                    neighbors.append((other_key, dist))
            neighbors.sort(key=lambda x: x[1])
            self._neighbors[key] = neighbors

    @staticmethod
    def _distance(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)

    def get_key_probabilities(self, clicked_key: str) -> Dict[str, float]:
        """Probability distribution over keys the user might have meant."""
        clicked_key = clicked_key.lower()
        if clicked_key not in self.positions:
            return {clicked_key: 1.0}

        probabilities: Dict[str, float] = {}
        sigma = self.uncertainty_radius / 2  # ≈ 95 % within radius
        for key, distance in self._neighbors.get(clicked_key, [(clicked_key, 0.0)]):
            if distance <= self.uncertainty_radius:
                probabilities[key] = math.exp(-distance ** 2 / (2 * sigma ** 2))

        total = sum(probabilities.values())
        if total > 0:
            probabilities = {k: v / total for k, v in probabilities.items()}
        return probabilities

    def get_nearby_keys(self, key: str) -> List[str]:
        key = key.lower()
        if key not in self._neighbors:
            return [key]
        return [k for k, d in self._neighbors[key] if d <= self.uncertainty_radius]

    def set_uncertainty_radius(self, radius: float) -> None:
        self.uncertainty_radius = radius
        self._build_neighbor_cache()


class FuzzyWordGenerator:
    """Expands a typed sequence into spatial-neighbour interpretations."""

    def __init__(
        self,
        spatial_model: Optional[SpatialKeyModel] = None,
        dictionary: Optional[Set[str]] = None,
        max_candidates: int = 50,
    ):
        self.spatial_model = spatial_model or SpatialKeyModel()
        self.dictionary = dictionary or set()
        self.max_candidates = max_candidates

    def generate_candidates(
        self,
        typed_sequence: str,
        min_prob: float = DEFAULT_MIN_PROB,
    ) -> List[Tuple[str, float]]:
        typed_sequence = typed_sequence.lower()
        if not typed_sequence:
            return []

        fuzzy_sequences = self._generate_fuzzy_sequences(typed_sequence, min_prob)
        candidates = [
            (seq, prob) for seq, prob in fuzzy_sequences if seq in self.dictionary
        ]
        candidates.sort(key=lambda x: -x[1])
        return candidates[:self.max_candidates]

    def _generate_fuzzy_sequences(
        self,
        typed: str,
        min_prob: float,
    ) -> List[Tuple[str, float]]:
        current: List[Tuple[str, float]] = [("", 1.0)]
        for char in typed:
            char_probs = self.spatial_model.get_key_probabilities(char)
            new_sequences: List[Tuple[str, float]] = []
            for prefix, prefix_prob in current:
                for possible_char, char_prob in char_probs.items():
                    combined_prob = prefix_prob * char_prob
                    if combined_prob >= min_prob:
                        new_sequences.append((prefix + possible_char, combined_prob))
            new_sequences.sort(key=lambda x: -x[1])
            current = new_sequences[:self.max_candidates * 2]
        return current

    def get_correction(
        self,
        typed_word: str,
        context: str = "",
    ) -> Optional[Tuple[str, float]]:
        if typed_word.lower() in self.dictionary:
            return None
        candidates = self.generate_candidates(typed_word)
        return candidates[0] if candidates else None

    def load_dictionary(self, path) -> bool:
        from pathlib import Path

        path = Path(path)
        if not path.exists():
            return False
        try:
            with open(path) as f:
                for line in f:
                    word = line.strip().lower()
                    if word and not word.startswith("#"):
                        # Frequency format: ``word count`` — keep the word.
                        self.dictionary.add(word.split()[0])
            _logger.info("Fuzzy dictionary loaded: %d words", len(self.dictionary))
            return True
        except OSError as e:
            _logger.error("Failed to load dictionary: %s", e)
            return False


class FuzzyRecognizer:
    """Top-level interface used by the hybrid predictor."""

    spatial_uncertainty: float = DEFAULT_SPATIAL_UNCERTAINTY
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    prediction_weight: float = DEFAULT_PREDICTION_WEIGHT

    def __init__(self, dictionary: Optional[Set[str]] = None):
        self.spatial_model = SpatialKeyModel(
            uncertainty_radius=self.spatial_uncertainty,
        )
        self.word_generator = FuzzyWordGenerator(
            spatial_model=self.spatial_model,
            dictionary=dictionary or set(),
        )

    def get_fuzzy_predictions(
        self,
        typed_text: str,
        n: int = 5,
    ) -> List[Tuple[str, float]]:
        words = typed_text.split()
        current_word = words[-1] if words and not typed_text.endswith(" ") else ""
        if not current_word:
            return []
        return self.word_generator.generate_candidates(current_word)[:n]

    def should_autocorrect(
        self,
        typed_word: str,
        context: str = "",
    ) -> Optional[str]:
        correction = self.word_generator.get_correction(typed_word, context)
        if correction is None:
            return None
        word, confidence = correction
        return word if confidence >= self.confidence_threshold else None

    def get_key_alternatives(self, key: str) -> Dict[str, float]:
        return self.spatial_model.get_key_probabilities(key)

    def load_dictionary(self, path) -> bool:
        return self.word_generator.load_dictionary(path)

    def get_stats(self) -> dict:
        return {
            "spatial_uncertainty": self.spatial_uncertainty,
            "confidence_threshold": self.confidence_threshold,
            "prediction_weight": self.prediction_weight,
            "dictionary_size": len(self.word_generator.dictionary),
        }
