"""
Integration tests for context window management.

Tests token tracking, pruning strategies, and threshold warnings.
"""

import pytest
import sys
from pathlib import Path

# Add config to path
config_path = Path(__file__).parent.parent.parent / "config"
sys.path.insert(0, str(config_path))

from context_manager import (
    ContextManager,
    PruningStrategy,
    ContextEntry,
)


class TestContextManager:
    """Test suite for ContextManager."""

    def test_manager_initialization(self):
        """Test manager initialization with defaults."""
        manager = ContextManager()

        assert manager.window.max_tokens == 100000
        assert manager.window.current_tokens == 0
        assert len(manager.window.entries) == 0

    def test_custom_initialization(self):
        """Test manager with custom settings."""
        manager = ContextManager(
            max_tokens=50000,
            warning_threshold=0.80,
            critical_threshold=0.90,
        )

        assert manager.window.max_tokens == 50000
        assert manager.window.warning_threshold == 0.80
        assert manager.window.critical_threshold == 0.90

    def test_add_entry(self):
        """Test adding entries to context."""
        manager = ContextManager()

        success = manager.add_entry(
            content="test content",
            tokens=100,
            category="test",
        )

        assert success is True
        assert manager.window.current_tokens == 100
        assert len(manager.window.entries) == 1

    def test_add_entry_exceeds_max(self):
        """Test adding entry that exceeds max tokens."""
        manager = ContextManager(max_tokens=1000)

        success = manager.add_entry(
            content="large content",
            tokens=1500,  # Exceeds max
        )

        assert success is False
        assert manager.window.current_tokens == 0

    def test_token_tracking(self):
        """Test simple token tracking."""
        manager = ContextManager()

        manager.track_tokens(500)
        manager.track_tokens(300)

        assert manager.window.current_tokens == 800
        assert len(manager.window.entries) == 2

    def test_usage_fraction(self):
        """Test usage fraction calculation."""
        manager = ContextManager(max_tokens=10000)

        manager.track_tokens(5000)

        assert manager.get_usage_fraction() == 0.5
        assert manager.get_usage_percentage() == 50.0

    def test_warning_threshold(self):
        """Test warning threshold detection."""
        manager = ContextManager(
            max_tokens=10000,
            warning_threshold=0.85,
        )

        manager.track_tokens(8000)  # 80% - should not warn
        assert manager.should_warn() is False

        manager.track_tokens(1000)  # 90% - should warn
        assert manager.should_warn() is True

    def test_critical_threshold(self):
        """Test critical threshold detection."""
        manager = ContextManager(
            max_tokens=10000,
            critical_threshold=0.95,
        )

        manager.track_tokens(9000)  # 90% - not critical
        assert manager.is_critical() is False

        manager.track_tokens(1000)  # 100% - critical
        assert manager.is_critical() is True

    def test_should_prune(self):
        """Test pruning recommendation."""
        manager = ContextManager(
            max_tokens=10000,
            warning_threshold=0.85,
        )

        manager.track_tokens(8000)  # 80% - don't prune
        assert manager.should_prune() is False

        manager.track_tokens(1000)  # 90% - should prune
        assert manager.should_prune() is True

    def test_recent_priority_pruning(self):
        """Test pruning with recent priority strategy."""
        manager = ContextManager(
            max_tokens=1000,
            warning_threshold=0.5,
        )

        # Add multiple entries
        for i in range(10):
            manager.add_entry(
                content=f"entry_{i}",
                tokens=100,
                importance=0.5,
            )

        # Current: 1000 tokens, target: 75% = 750
        removed = manager.prune(target_fraction=0.75)

        assert len(removed) > 0
        assert manager.window.current_tokens <= 750
        # Should remove oldest entries
        assert all(e.content.startswith("entry_") for e in removed)

    def test_importance_score_pruning(self):
        """Test pruning with importance score strategy."""
        manager = ContextManager(max_tokens=1000)

        # Add entries with varying importance
        for i in range(5):
            manager.add_entry(
                content=f"entry_{i}",
                tokens=200,
                importance=0.2 + (i * 0.15),  # 0.2, 0.35, 0.5, 0.65, 0.8
            )

        # Prune to 600 tokens (should keep high importance)
        removed = manager.prune(
            target_fraction=0.6,
            strategy=PruningStrategy.IMPORTANCE_SCORE,
        )

        # Should have removed low importance entries
        assert len(removed) > 0
        assert manager.window.current_tokens <= 600

    def test_round_robin_pruning(self):
        """Test pruning with round robin strategy."""
        manager = ContextManager(max_tokens=1000)

        # Add entries from different categories
        categories = ["a", "b", "c"]
        for category in categories:
            for i in range(3):
                manager.add_entry(
                    content=f"{category}_entry_{i}",
                    tokens=100,
                    category=category,
                )

        # Prune to 600 tokens (should distribute across categories)
        removed = manager.prune(
            target_fraction=0.6,
            strategy=PruningStrategy.ROUND_ROBIN,
        )

        assert len(removed) > 0
        assert manager.window.current_tokens <= 600

    def test_get_status(self):
        """Test getting status information."""
        manager = ContextManager(max_tokens=10000)

        manager.track_tokens(5000)

        status = manager.get_status()

        assert status["current_tokens"] == 5000
        assert status["max_tokens"] == 10000
        assert status["usage_fraction"] == 0.5
        assert status["usage_percentage"] == 50.0
        assert status["should_warn"] is False
        assert status["is_critical"] is False

    def test_category_tracking(self):
        """Test tracking entries by category."""
        manager = ContextManager()

        manager.add_entry("entry1", tokens=100, category="analysis")
        manager.add_entry("entry2", tokens=200, category="analysis")
        manager.add_entry("entry3", tokens=150, category="advisory")

        analysis_entries = manager.get_entries_by_category("analysis")
        assert len(analysis_entries) == 2

        category_usage = manager.get_category_token_usage()
        assert category_usage["analysis"] == 300
        assert category_usage["advisory"] == 150

    def test_clear_context(self):
        """Test clearing all context."""
        manager = ContextManager()

        manager.track_tokens(5000)
        manager.clear()

        assert manager.window.current_tokens == 0
        assert len(manager.window.entries) == 0

    def test_token_estimation(self):
        """Test token estimation."""
        manager = ContextManager()

        # Rough estimation: ~4 characters per token
        estimated = manager.estimate_tokens("Hello, world!")
        assert estimated > 0
        assert estimated < 100  # Should be reasonable


class TestPruningPerformance:
    """Test pruning performance with larger contexts."""

    def test_large_context_pruning(self):
        """Test pruning performance with large context."""
        import time

        manager = ContextManager(max_tokens=100000)

        # Add 1000 entries
        start = time.time()
        for i in range(1000):
            manager.add_entry(
                content=f"entry_{i}",
                tokens=100,
                importance=0.5,
            )
        add_time = time.time() - start

        # Prune
        start = time.time()
        removed = manager.prune(target_fraction=0.7)
        prune_time = time.time() - start

        # Should complete in reasonable time
        assert add_time < 1.0
        assert prune_time < 1.0

        # Verify pruning worked
        assert manager.window.current_tokens <= 70000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
