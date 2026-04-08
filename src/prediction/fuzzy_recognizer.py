"""
Fuzzy/Spatial Recognition for motor challenges.

Corrects typos based on key proximity, inspired by Gboard.
Configurable for different motor abilities (tremor, limited mobility).

Key features:
- Models spatial uncertainty around each key
- Generates candidate interpretations
- Ranks by language model probability
- Configurable profiles for different motor abilities
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

_logger = logging.getLogger("FuzzyRecognizer")


# QWERTY keyboard layout with relative positions
# Each key maps to (row, col) coordinates
QWERTY_POSITIONS: Dict[str, Tuple[float, float]] = {
    # Row 0 (top)
    'q': (0, 0), 'w': (0, 1), 'e': (0, 2), 'r': (0, 3), 't': (0, 4),
    'y': (0, 5), 'u': (0, 6), 'i': (0, 7), 'o': (0, 8), 'p': (0, 9),
    # Row 1 (home row) - offset by 0.25
    'a': (1, 0.25), 's': (1, 1.25), 'd': (1, 2.25), 'f': (1, 3.25), 'g': (1, 4.25),
    'h': (1, 5.25), 'j': (1, 6.25), 'k': (1, 7.25), 'l': (1, 8.25),
    # Row 2 (bottom) - offset by 0.75
    'z': (2, 0.75), 'x': (2, 1.75), 'c': (2, 2.75), 'v': (2, 3.75), 'b': (2, 4.75),
    'n': (2, 5.75), 'm': (2, 6.75),
}


@dataclass
class AccessibilityProfile:
    """
    Configuration profile for different motor abilities.

    Attributes:
        name: Profile name for display
        spatial_uncertainty: Radius of spatial uncertainty (in key widths)
        confidence_threshold: Minimum confidence for autocorrect
        prediction_weight: How much to trust predictions vs literal input
        key_hold_delay: Milliseconds to ignore repeated presses
        autocorrect_enabled: Whether to autocorrect automatically
    """
    name: str
    spatial_uncertainty: float
    confidence_threshold: float
    prediction_weight: float
    key_hold_delay: int = 0
    autocorrect_enabled: bool = True

    @classmethod
    def precise(cls) -> "AccessibilityProfile":
        """Profile for precise motor control."""
        return cls(
            name="Precise",
            spatial_uncertainty=0.5,
            confidence_threshold=0.9,
            prediction_weight=0.3,
            key_hold_delay=0,
            autocorrect_enabled=False,
        )

    @classmethod
    def normal(cls) -> "AccessibilityProfile":
        """Profile for normal motor control."""
        return cls(
            name="Normal",
            spatial_uncertainty=1.0,
            confidence_threshold=0.8,
            prediction_weight=0.5,
            key_hold_delay=0,
            autocorrect_enabled=True,
        )

    @classmethod
    def mild_tremor(cls) -> "AccessibilityProfile":
        """Profile for mild tremor or reduced precision."""
        return cls(
            name="Mild Tremor",
            spatial_uncertainty=1.5,
            confidence_threshold=0.7,
            prediction_weight=0.6,
            key_hold_delay=100,
            autocorrect_enabled=True,
        )

    @classmethod
    def moderate_tremor(cls) -> "AccessibilityProfile":
        """Profile for moderate tremor."""
        return cls(
            name="Moderate Tremor",
            spatial_uncertainty=2.0,
            confidence_threshold=0.6,
            prediction_weight=0.7,
            key_hold_delay=200,
            autocorrect_enabled=True,
        )

    @classmethod
    def severe_tremor(cls) -> "AccessibilityProfile":
        """Profile for severe tremor or very limited control."""
        return cls(
            name="Severe Tremor",
            spatial_uncertainty=2.5,
            confidence_threshold=0.5,
            prediction_weight=0.8,
            key_hold_delay=300,
            autocorrect_enabled=True,
        )

    @classmethod
    def limited_mobility(cls) -> "AccessibilityProfile":
        """Profile for limited range of motion."""
        return cls(
            name="Limited Mobility",
            spatial_uncertainty=2.0,
            confidence_threshold=0.6,
            prediction_weight=0.75,
            key_hold_delay=150,
            autocorrect_enabled=True,
        )


# Pre-built profiles
PROFILES: Dict[str, AccessibilityProfile] = {
    "precise": AccessibilityProfile.precise(),
    "normal": AccessibilityProfile.normal(),
    "mild_tremor": AccessibilityProfile.mild_tremor(),
    "moderate_tremor": AccessibilityProfile.moderate_tremor(),
    "severe_tremor": AccessibilityProfile.severe_tremor(),
    "limited_mobility": AccessibilityProfile.limited_mobility(),
}


class SpatialKeyModel:
    """
    Models spatial uncertainty for key presses.

    Given a clicked key, provides probability distribution over
    what the user might have intended based on key proximity.
    """

    def __init__(
        self,
        positions: Optional[Dict[str, Tuple[float, float]]] = None,
        uncertainty_radius: float = 1.0
    ):
        """
        Initialize spatial model.

        Args:
            positions: Key position mapping (uses QWERTY if not provided)
            uncertainty_radius: Spatial uncertainty in key widths
        """
        self.positions = positions or QWERTY_POSITIONS
        self.uncertainty_radius = uncertainty_radius

        # Precompute neighbor lists for efficiency
        self._neighbors: Dict[str, List[Tuple[str, float]]] = {}
        self._build_neighbor_cache()

    def _build_neighbor_cache(self) -> None:
        """Precompute neighbors for each key."""
        for key, pos in self.positions.items():
            neighbors = []
            for other_key, other_pos in self.positions.items():
                dist = self._distance(pos, other_pos)
                if dist <= self.uncertainty_radius * 1.5:  # Include slightly beyond radius
                    neighbors.append((other_key, dist))

            # Sort by distance
            neighbors.sort(key=lambda x: x[1])
            self._neighbors[key] = neighbors

    def _distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """Euclidean distance between positions."""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

    def get_key_probabilities(self, clicked_key: str) -> Dict[str, float]:
        """
        Get probability distribution over intended keys.

        Given a clicked key, returns probability of what user intended
        based on spatial proximity.

        Args:
            clicked_key: Key that was clicked

        Returns:
            Dict mapping key -> probability
        """
        clicked_key = clicked_key.lower()

        if clicked_key not in self.positions:
            # Unknown key, return just the clicked key
            return {clicked_key: 1.0}

        probabilities = {}

        # Get neighbors from cache
        neighbors = self._neighbors.get(clicked_key, [(clicked_key, 0.0)])

        for key, distance in neighbors:
            if distance <= self.uncertainty_radius:
                # Gaussian probability based on distance
                # sigma = uncertainty_radius / 2 (so 95% within radius)
                sigma = self.uncertainty_radius / 2
                prob = math.exp(-distance**2 / (2 * sigma**2))
                probabilities[key] = prob

        # Normalize
        total = sum(probabilities.values())
        if total > 0:
            probabilities = {k: v / total for k, v in probabilities.items()}

        return probabilities

    def get_nearby_keys(self, key: str) -> List[str]:
        """Get list of keys near the given key."""
        key = key.lower()
        if key not in self._neighbors:
            return [key]

        return [k for k, d in self._neighbors[key] if d <= self.uncertainty_radius]

    def set_uncertainty_radius(self, radius: float) -> None:
        """Update uncertainty radius and rebuild cache."""
        self.uncertainty_radius = radius
        self._build_neighbor_cache()


class FuzzyWordGenerator:
    """
    Generates fuzzy word candidates based on spatial uncertainty.

    Given a typed sequence, generates all plausible interpretations
    considering that each key might be a nearby key.
    """

    def __init__(
        self,
        spatial_model: Optional[SpatialKeyModel] = None,
        dictionary: Optional[Set[str]] = None,
        max_candidates: int = 50
    ):
        """
        Initialize fuzzy generator.

        Args:
            spatial_model: Spatial key model
            dictionary: Set of valid words
            max_candidates: Maximum candidates to generate
        """
        self.spatial_model = spatial_model or SpatialKeyModel()
        self.dictionary = dictionary or set()
        self.max_candidates = max_candidates

    def generate_candidates(
        self,
        typed_sequence: str,
        min_prob: float = 0.01
    ) -> List[Tuple[str, float]]:
        """
        Generate word candidates considering spatial uncertainty.

        Args:
            typed_sequence: What the user typed
            min_prob: Minimum probability threshold

        Returns:
            List of (word, probability) tuples
        """
        typed_sequence = typed_sequence.lower()

        if not typed_sequence:
            return []

        # Generate fuzzy sequences
        fuzzy_sequences = self._generate_fuzzy_sequences(typed_sequence, min_prob)

        # Filter to dictionary words
        candidates = []
        for sequence, prob in fuzzy_sequences:
            if sequence in self.dictionary:
                candidates.append((sequence, prob))

        # Sort by probability
        candidates.sort(key=lambda x: -x[1])

        return candidates[:self.max_candidates]

    def _generate_fuzzy_sequences(
        self,
        typed: str,
        min_prob: float
    ) -> List[Tuple[str, float]]:
        """
        Generate all possible sequences considering spatial uncertainty.

        Uses iterative approach with pruning for efficiency.
        """
        # Start with empty prefix
        current = [("", 1.0)]

        for char in typed:
            # Get probabilities for this character
            char_probs = self.spatial_model.get_key_probabilities(char)

            # Extend each current sequence with each possible character
            new_sequences = []
            for prefix, prefix_prob in current:
                for possible_char, char_prob in char_probs.items():
                    combined_prob = prefix_prob * char_prob

                    # Prune low probability sequences
                    if combined_prob >= min_prob:
                        new_sequences.append((prefix + possible_char, combined_prob))

            # Keep top candidates to limit growth
            new_sequences.sort(key=lambda x: -x[1])
            current = new_sequences[:self.max_candidates * 2]

        return current

    def get_correction(
        self,
        typed_word: str,
        context: str = ""
    ) -> Optional[Tuple[str, float]]:
        """
        Get best correction for a typed word.

        Args:
            typed_word: Word as typed
            context: Previous context (unused for now)

        Returns:
            (corrected_word, confidence) or None if no correction
        """
        # If typed word is in dictionary, no correction needed
        if typed_word.lower() in self.dictionary:
            return None

        # Get candidates
        candidates = self.generate_candidates(typed_word)

        if not candidates:
            return None

        # Return best candidate
        return candidates[0]

    def load_dictionary(self, path) -> bool:
        """Load dictionary from file."""
        from pathlib import Path
        path = Path(path)

        if not path.exists():
            return False

        try:
            with open(path) as f:
                for line in f:
                    word = line.strip().lower()
                    if word and not word.startswith("#"):
                        # Handle frequency format: word count
                        parts = word.split()
                        self.dictionary.add(parts[0])

            _logger.info("Fuzzy dictionary loaded: %d words", len(self.dictionary))
            return True
        except Exception as e:
            _logger.error("Failed to load dictionary: %s", e)
            return False


class FuzzyRecognizer:
    """
    Main fuzzy recognition interface.

    Combines spatial model, word generation, and language model
    for intelligent error correction.
    """

    def __init__(
        self,
        profile: Optional[AccessibilityProfile] = None,
        dictionary: Optional[Set[str]] = None
    ):
        """
        Initialize fuzzy recognizer.

        Args:
            profile: Accessibility profile to use
            dictionary: Word dictionary
        """
        self.profile = profile or AccessibilityProfile.normal()

        # Initialize spatial model with profile's uncertainty
        self.spatial_model = SpatialKeyModel(
            uncertainty_radius=self.profile.spatial_uncertainty
        )

        # Initialize word generator
        self.word_generator = FuzzyWordGenerator(
            spatial_model=self.spatial_model,
            dictionary=dictionary or set()
        )

        # Language model integration (to be connected)
        self._language_model = None

    def set_profile(self, profile_name: str) -> bool:
        """
        Set accessibility profile by name.

        Args:
            profile_name: Name of profile (e.g., "normal", "mild_tremor")

        Returns:
            True if profile found and set
        """
        if profile_name not in PROFILES:
            _logger.warning("Unknown profile: %s", profile_name)
            return False

        self.profile = PROFILES[profile_name]
        self.spatial_model.set_uncertainty_radius(self.profile.spatial_uncertainty)

        _logger.info("Set accessibility profile: %s", self.profile.name)
        return True

    def set_custom_profile(self, profile: AccessibilityProfile) -> None:
        """Set a custom accessibility profile."""
        self.profile = profile
        self.spatial_model.set_uncertainty_radius(profile.spatial_uncertainty)

    def get_fuzzy_predictions(
        self,
        typed_text: str,
        n: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Get word predictions considering spatial uncertainty.

        Args:
            typed_text: Text typed so far
            n: Number of predictions

        Returns:
            List of (word, probability) tuples
        """
        # Extract current word
        words = typed_text.split()
        current_word = words[-1] if words and not typed_text.endswith(" ") else ""

        if not current_word:
            return []

        # Get fuzzy candidates
        candidates = self.word_generator.generate_candidates(current_word)

        return candidates[:n]

    def should_autocorrect(
        self,
        typed_word: str,
        context: str = ""
    ) -> Optional[str]:
        """
        Check if word should be autocorrected.

        Args:
            typed_word: Word as typed
            context: Previous context

        Returns:
            Corrected word if should autocorrect, None otherwise
        """
        if not self.profile.autocorrect_enabled:
            return None

        correction = self.word_generator.get_correction(typed_word, context)

        if correction is None:
            return None

        word, confidence = correction

        if confidence >= self.profile.confidence_threshold:
            return word

        return None

    def get_key_alternatives(self, key: str) -> Dict[str, float]:
        """
        Get probability distribution over intended keys.

        Args:
            key: Pressed key

        Returns:
            Dict mapping key -> probability
        """
        return self.spatial_model.get_key_probabilities(key)

    def load_dictionary(self, path) -> bool:
        """Load dictionary for fuzzy matching."""
        return self.word_generator.load_dictionary(path)

    def get_profile_names(self) -> List[str]:
        """Get list of available profile names."""
        return list(PROFILES.keys())

    def get_current_profile(self) -> AccessibilityProfile:
        """Get current accessibility profile."""
        return self.profile

    def get_stats(self) -> dict:
        """Get recognizer statistics."""
        return {
            "profile": self.profile.name,
            "spatial_uncertainty": self.profile.spatial_uncertainty,
            "dictionary_size": len(self.word_generator.dictionary),
            "autocorrect_enabled": self.profile.autocorrect_enabled,
        }
