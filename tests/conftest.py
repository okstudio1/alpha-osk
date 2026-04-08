"""Shared fixtures for Alpha-OSK tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_model_dir(tmp_path: Path) -> Path:
    """Temporary directory for model files."""
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    return model_dir


@pytest.fixture
def sample_corpus() -> str:
    """Small text corpus for training predictors."""
    return (
        "the quick brown fox jumps over the lazy dog. "
        "the cat sat on the mat. "
        "I want to go to the store. "
        "how are you doing today. "
        "please help me with this. "
        "thank you very much for your help. "
        "hello how are you. "
        "the weather is nice today. "
        "I need to finish this work. "
        "can you help me please. "
    )


@pytest.fixture
def small_dictionary() -> set[str]:
    """Small word dictionary for testing fuzzy recognition."""
    return {
        "the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog",
        "cat", "sat", "mat", "hello", "help", "please", "thank", "thanks",
        "want", "need", "going", "today", "weather", "nice", "work",
        "store", "finish", "doing", "much", "your", "very", "with",
        "this", "that", "have", "from", "they", "will", "would",
        "there", "their", "what", "about", "which", "could", "should",
    }
