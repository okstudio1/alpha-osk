"""
N-gram based word prediction engine.

Fast, lightweight prediction using word frequency and context.
This is the "instant" layer of the hybrid approach.
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Optional

_logger = logging.getLogger("NgramPredictor")


class NgramPredictor:
    """
    N-gram based predictor for instant word suggestions.
    
    Uses unigram (word frequency) and bigram (word pairs) models
    to predict the next word based on context.
    """

    def __init__(self, model_path: Optional[Path] = None):
        """
        Initialize the predictor.
        
        Args:
            model_path: Path to saved model file. If None, starts with empty model.
        """
        # Unigram: word -> frequency
        self.unigrams: Dict[str, int] = defaultdict(int)
        # Bigram: (prev_word, word) -> frequency
        self.bigrams: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        # Trigram: (prev2, prev1, word) -> frequency (optional, more context)
        self.trigrams: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Total word count for probability calculation
        self.total_words = 0
        
        # User-specific vocabulary boost
        self.user_vocab: Dict[str, int] = defaultdict(int)
        
        # Common words to always include
        self._common_words = [
            "the", "be", "to", "of", "and", "a", "in", "that", "have", "I",
            "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
            "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
            "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
            "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
            "is", "are", "was", "were", "been", "being", "am", "can", "could", "may",
            "might", "must", "shall", "should", "will", "would", "need", "want", "like",
            "hello", "hi", "thanks", "thank", "please", "yes", "no", "okay", "ok",
        ]
        
        # Initialize with common words
        for word in self._common_words:
            self.unigrams[word] = 100  # Base frequency
        self.total_words = len(self._common_words) * 100
        
        # Load saved model if provided
        if model_path and model_path.exists():
            self.load(model_path)

    def predict(self, context: str, n: int = 5) -> List[str]:
        """
        Predict next words based on context.
        
        Args:
            context: The text typed so far (full or partial word at end)
            n: Number of predictions to return
            
        Returns:
            List of predicted words, most likely first
        """
        # IMPORTANT: Check for trailing space BEFORE stripping
        # Trailing space = user finished word, predict NEXT word
        # No trailing space = user typing, complete CURRENT word
        ends_with_space = context.endswith(" ")
        
        context_clean = context.lower().strip()
        if not context_clean:
            return self._top_unigrams(n)
        
        # Split into words
        words = self._tokenize(context_clean)
        
        # Check if user is mid-word (no trailing space in original)
        partial_word = ""
        if not ends_with_space and words:
            # User is typing a partial word - complete it
            partial_word = words[-1]
            words = words[:-1]
        # else: User finished word (space at end) - predict next word
        
        # Get candidates
        candidates: Dict[str, float] = {}
        
        # Trigram predictions (if we have 2+ previous words)
        if len(words) >= 2:
            key = f"{words[-2]} {words[-1]}"
            if key in self.trigrams:
                for word, freq in self.trigrams[key].items():
                    if self._matches_partial(word, partial_word):
                        candidates[word] = candidates.get(word, 0) + freq * 3  # Weight trigrams highest
        
        # Bigram predictions (if we have 1+ previous words)
        if len(words) >= 1:
            prev_word = words[-1]
            if prev_word in self.bigrams:
                for word, freq in self.bigrams[prev_word].items():
                    if self._matches_partial(word, partial_word):
                        candidates[word] = candidates.get(word, 0) + freq * 2  # Weight bigrams
        
        # Unigram fallback + partial matching
        for word, freq in self.unigrams.items():
            if self._matches_partial(word, partial_word):
                candidates[word] = candidates.get(word, 0) + freq * 0.5
        
        # Boost user vocabulary
        for word, boost in self.user_vocab.items():
            if word in candidates:
                candidates[word] *= (1 + boost * 0.1)
        
        # Sort by score and return top n
        sorted_candidates = sorted(candidates.items(), key=lambda x: -x[1])
        return [word for word, _ in sorted_candidates[:n]]

    def _matches_partial(self, word: str, partial: str) -> bool:
        """Check if word matches partial input."""
        if not partial:
            return True
        return word.startswith(partial)

    def _top_unigrams(self, n: int) -> List[str]:
        """Get top n words by frequency."""
        sorted_words = sorted(self.unigrams.items(), key=lambda x: -x[1])
        return [word for word, _ in sorted_words[:n]]

    def _tokenize(self, text: str) -> List[str]:
        """Split text into words."""
        # Simple tokenization: split on non-alphanumeric
        words = re.findall(r"[a-zA-Z']+", text.lower())
        return words

    def learn(self, text: str) -> None:
        """
        Learn from new text, updating n-gram frequencies.
        
        Args:
            text: Text to learn from
        """
        words = self._tokenize(text)
        if not words:
            return
        
        # Update unigrams
        for word in words:
            self.unigrams[word] += 1
            self.user_vocab[word] += 1
            self.total_words += 1
        
        # Update bigrams
        for i in range(1, len(words)):
            prev_word = words[i - 1]
            curr_word = words[i]
            self.bigrams[prev_word][curr_word] += 1
        
        # Update trigrams
        for i in range(2, len(words)):
            key = f"{words[i-2]} {words[i-1]}"
            curr_word = words[i]
            self.trigrams[key][curr_word] += 1

    def learn_word(self, word: str) -> None:
        """Learn a single word (boost its frequency)."""
        word = word.lower().strip()
        if word:
            self.unigrams[word] += 5
            self.user_vocab[word] += 5
            self.total_words += 5

    def save(self, path: Path) -> None:
        """Save model to JSON file."""
        data = {
            "unigrams": dict(self.unigrams),
            "bigrams": {k: dict(v) for k, v in self.bigrams.items()},
            "trigrams": {k: dict(v) for k, v in self.trigrams.items()},
            "user_vocab": dict(self.user_vocab),
            "total_words": self.total_words,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f)
        _logger.info("Model saved to %s", path)

    def load(self, path: Path) -> None:
        """Load model from JSON file."""
        try:
            with open(path) as f:
                data = json.load(f)
            
            self.unigrams = defaultdict(int, data.get("unigrams", {}))
            self.bigrams = defaultdict(
                lambda: defaultdict(int),
                {k: defaultdict(int, v) for k, v in data.get("bigrams", {}).items()}
            )
            self.trigrams = defaultdict(
                lambda: defaultdict(int),
                {k: defaultdict(int, v) for k, v in data.get("trigrams", {}).items()}
            )
            self.user_vocab = defaultdict(int, data.get("user_vocab", {}))
            self.total_words = data.get("total_words", 0)
            _logger.info("Model loaded from %s", path)
        except Exception as e:
            _logger.warning("Failed to load model from %s: %s", path, e)

    def load_corpus(self, text: str) -> None:
        """Load a large corpus for initial training."""
        _logger.info("Loading corpus (%d chars)...", len(text))
        self.learn(text)
        _logger.info("Corpus loaded. Total words: %d", self.total_words)

    def load_base_dictionary(self, dict_path: Optional[Path] = None) -> bool:
        """
        Load base dictionary file to bootstrap predictions.
        
        Args:
            dict_path: Path to dictionary file. If None, uses default location.
            
        Returns:
            True if loaded successfully
        """
        if dict_path is None:
            # Default location relative to this file
            dict_path = Path(__file__).parent.parent.parent / "data" / "base_dictionary.txt"
        
        if not dict_path.exists():
            _logger.warning("Base dictionary not found: %s", dict_path)
            return False
        
        try:
            with open(dict_path, "r") as f:
                content = f.read()
            
            # Process each line
            for line in content.split("\n"):
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                # Learn the words/phrases on this line
                self.learn(line)
            
            _logger.info("Base dictionary loaded: %d total words", self.total_words)
            return True
        except Exception as e:
            _logger.error("Failed to load base dictionary: %s", e)
            return False

    def clear_user_data(self) -> None:
        """Clear user-learned vocabulary while keeping base dictionary."""
        self.user_vocab.clear()
        _logger.info("User vocabulary cleared")

    def get_stats(self) -> dict:
        """Get prediction engine statistics."""
        return {
            "total_words": self.total_words,
            "unique_words": len(self.unigrams),
            "bigrams": sum(len(v) for v in self.bigrams.values()),
            "trigrams": sum(len(v) for v in self.trigrams.values()),
            "user_words": len(self.user_vocab),
        }
