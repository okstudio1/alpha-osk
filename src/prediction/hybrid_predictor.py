"""
Hybrid word prediction engine.

Combines fast n-gram predictions with LLM re-ranking for
the best balance of speed and accuracy.

Architecture:
1. N-gram provides instant predictions (<10ms)
2. Transformer re-ranks in background (~100ms)
3. UI updates with refined predictions when ready
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import List, Optional, Callable

from PySide6.QtCore import QObject, Signal

from .ngram_predictor import NgramPredictor
from .transformer_predictor import TransformerPredictor

_logger = logging.getLogger("HybridPredictor")


class HybridPredictor(QObject):
    """
    Hybrid prediction engine combining n-gram speed with LLM accuracy.
    
    Emits Qt signals for integration with QML UI.
    """

    # Signals for QML integration
    predictionsReady = Signal(list)      # Instant n-gram predictions
    predictionsRefined = Signal(list)    # LLM-refined predictions
    modelLoading = Signal(bool)          # True when LLM is loading
    llmAvailableChanged = Signal(bool)   # LLM availability changed

    def __init__(
        self,
        model_dir: Optional[Path] = None,
        enable_llm: bool = True,
        parent: Optional[QObject] = None
    ):
        """
        Initialize the hybrid predictor.
        
        Args:
            model_dir: Directory for storing model files
            enable_llm: Whether to enable LLM re-ranking (can disable for speed)
            parent: Qt parent object
        """
        super().__init__(parent)
        
        # Set up model directory
        if model_dir is None:
            model_dir = Path.home() / ".config" / "alpha-osk" / "models"
        self._model_dir = model_dir
        self._model_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize n-gram predictor (always available)
        ngram_path = self._model_dir / "ngram_model.json"
        self._ngram = NgramPredictor(ngram_path if ngram_path.exists() else None)
        
        # Load base dictionary for better initial predictions
        self._ngram.load_base_dictionary()
        _logger.info("N-gram predictor initialized")
        
        # Initialize transformer predictor (lazy loaded)
        self._enable_llm = enable_llm
        self._transformer: Optional[TransformerPredictor] = None
        self._llm_available = False
        
        if enable_llm:
            # Load LLM in background
            self._load_llm_async()
        
        # Current context for tracking
        self._current_context = ""
        self._pending_refinement = False

    def _load_llm_async(self) -> None:
        """Load the LLM in a background thread."""
        def loader():
            self.modelLoading.emit(True)
            try:
                self._transformer = TransformerPredictor(lazy_load=False)
                self._llm_available = self._transformer.is_available()
                if self._llm_available:
                    _logger.info("LLM predictor loaded and available")
                else:
                    _logger.warning("LLM predictor not available (missing dependencies?)")
            except Exception as e:
                _logger.error("Failed to load LLM: %s", e)
                self._llm_available = False
            finally:
                self.modelLoading.emit(False)
                # Notify QML of availability change
                self.llmAvailableChanged.emit(self._llm_available)
        
        thread = threading.Thread(target=loader, daemon=True)
        thread.start()

    def predict(self, context: str, n: int = 5) -> List[str]:
        """
        Get instant predictions (n-gram only, synchronous).
        
        Args:
            context: Text typed so far
            n: Number of predictions
            
        Returns:
            List of predicted words
        """
        self._current_context = context
        predictions = self._ngram.predict(context, n)
        return predictions

    def predict_with_refinement(self, context: str, n: int = 5) -> List[str]:
        """
        Get instant predictions and trigger async LLM refinement.
        
        Emits predictionsReady immediately, then predictionsRefined
        when LLM finishes.
        
        Args:
            context: Text typed so far
            n: Number of predictions
            
        Returns:
            Instant n-gram predictions
        """
        self._current_context = context
        
        # Get instant n-gram predictions
        predictions = self._ngram.predict(context, n)
        self.predictionsReady.emit(predictions)
        
        # Trigger async LLM refinement if available
        if self._llm_available and self._transformer and len(context) > 3:
            self._refine_async(context, predictions, n)
        
        return predictions

    def _refine_async(self, context: str, candidates: List[str], n: int) -> None:
        """Trigger async LLM re-ranking."""
        if self._pending_refinement:
            return  # Don't queue multiple refinements
        
        self._pending_refinement = True
        
        def on_refined(refined: List[str]):
            self._pending_refinement = False
            # Only emit if context hasn't changed
            if context == self._current_context and refined:
                self.predictionsRefined.emit(refined)
        
        # Get more candidates for re-ranking
        extended_candidates = self._ngram.predict(context, n * 3)
        self._transformer.rerank_async(context, extended_candidates, on_refined, n)

    def learn(self, text: str) -> None:
        """
        Learn from user's text to improve predictions.
        
        Args:
            text: Text to learn from
        """
        self._ngram.learn(text)

    def learn_word(self, word: str) -> None:
        """Learn a single word (e.g., when user types it)."""
        self._ngram.learn_word(word)

    def learn_from_selection(self, context: str, selected_word: str) -> None:
        """
        Learn when user selects a prediction.
        
        This helps the model understand which predictions are useful.
        
        Args:
            context: The context when prediction was made
            selected_word: The word the user selected
        """
        # Boost the selected word
        self._ngram.learn_word(selected_word)
        
        # Learn the context -> word association
        full_text = f"{context} {selected_word}"
        self._ngram.learn(full_text)

    def save(self) -> None:
        """Save the model to disk."""
        ngram_path = self._model_dir / "ngram_model.json"
        self._ngram.save(ngram_path)
        _logger.info("Model saved")

    def load_corpus(self, corpus_path: Path) -> None:
        """
        Load a text corpus for initial training.
        
        Args:
            corpus_path: Path to text file
        """
        if not corpus_path.exists():
            _logger.warning("Corpus not found: %s", corpus_path)
            return
        
        text = corpus_path.read_text(encoding="utf-8", errors="ignore")
        self._ngram.load_corpus(text)
        self.save()

    @property
    def llm_available(self) -> bool:
        """Check if LLM is available for refinement."""
        return self._llm_available

    @property
    def enable_llm(self) -> bool:
        """Check if LLM is enabled."""
        return self._enable_llm

    @enable_llm.setter
    def enable_llm(self, value: bool) -> None:
        """Enable/disable LLM refinement."""
        self._enable_llm = value
        if value and self._transformer is None:
            self._load_llm_async()

    def get_stats(self) -> dict:
        """Get prediction engine statistics."""
        stats = self._ngram.get_stats()
        stats["llm_enabled"] = self._enable_llm
        stats["llm_available"] = self._llm_available
        return stats

    def clear_user_data(self) -> None:
        """Clear user-learned vocabulary."""
        self._ngram.clear_user_data()
        # Reload base dictionary
        self._ngram.load_base_dictionary()

    def reload_dictionary(self) -> bool:
        """Reload the base dictionary."""
        return self._ngram.load_base_dictionary()
