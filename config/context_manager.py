"""
context_manager.py — Context Window Management

This module provides token-aware context management with window tracking,
pruning strategies, and threshold warnings.

Architecture:
- ContextManager: Main context management class
- PruningStrategy: Enum of available pruning strategies
- ContextWindow: Dataclass for window state tracking

Usage:
    manager = ContextManager(max_tokens=100000)
    manager.track_tokens(45000)
    if manager.should_prune():
        manager.prune()
"""

from __future__ import annotations

import time
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
)
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import deque


class PruningStrategy(Enum):
    """Strategies for pruning context when threshold is exceeded."""
    RECENT_PRIORITY = "recent_priority"  # Keep most recent items
    IMPORTANCE_SCORE = "importance_score"  # Keep high-importance items
    CUSTOM = "custom"  # Use custom scoring function
    ROUND_ROBIN = "round_robin"  # Distribute pruning across categories


@dataclass
class ContextEntry:
    """A single entry in the context window."""
    content: str
    tokens: int
    timestamp: datetime = field(default_factory=datetime.now)
    importance: float = 0.5  # 0-1 score
    category: str = "general"
    entry_id: Optional[str] = None


@dataclass
class ContextWindow:
    """State of the context window."""
    max_tokens: int = 100000
    current_tokens: int = 0
    entries: List[ContextEntry] = field(default_factory=list)
    last_pruned: Optional[datetime] = None
    prune_count: int = 0

    # Thresholds (as fractions of max_tokens)
    warning_threshold: float = 0.85
    critical_threshold: float = 0.95


class ContextManager:
    """
    Manager for token-aware context window operations.

    Tracks token usage, warns when approaching limits, and provides
    pruning strategies to maintain context within window bounds.
    """

    def __init__(
        self,
        max_tokens: int = 100000,
        warning_threshold: float = 0.85,
        critical_threshold: float = 0.95,
        pruning_strategy: PruningStrategy = PruningStrategy.RECENT_PRIORITY,
    ):
        """
        Initialize the context manager.

        Args:
            max_tokens: Maximum context window size in tokens
            warning_threshold: Warning threshold (0-1) as fraction of max
            critical_threshold: Critical threshold (0-1) as fraction of max
            pruning_strategy: Default strategy for pruning
        """
        self.window = ContextWindow(
            max_tokens=max_tokens,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
        )
        self.pruning_strategy = pruning_strategy
        self._custom_score_func: Optional[Callable[[ContextEntry], float]] = None

        # Performance tracking
        self._add_times: deque = deque(maxlen=100)
        self._prune_times: deque = deque(maxlen=100)

    def add_entry(
        self,
        content: str,
        tokens: int,
        importance: float = 0.5,
        category: str = "general",
        entry_id: Optional[str] = None,
    ) -> bool:
        """
        Add an entry to the context window.

        Args:
            content: Text content of the entry
            tokens: Number of tokens in the entry
            importance: Importance score (0-1) for pruning decisions
            category: Category for organization
            entry_id: Optional unique identifier

        Returns:
            True if entry was added, False if would exceed max_tokens
        """
        start_time = time.time()

        # Check if adding would exceed max
        if self.window.current_tokens + tokens > self.window.max_tokens:
            return False

        entry = ContextEntry(
            content=content,
            tokens=tokens,
            importance=importance,
            category=category,
            entry_id=entry_id,
        )

        self.window.entries.append(entry)
        self.window.current_tokens += tokens

        # Track performance
        self._add_times.append(time.time() - start_time)

        return True

    def track_tokens(self, token_count: int) -> None:
        """
        Track token usage (convenience method for simple updates).

        Args:
            token_count: Number of tokens to add
        """
        # Create a generic entry
        self.add_entry(
            content=f"<token_block_{len(self.window.entries)}>",
            tokens=token_count,
            category="tracking",
        )

    def remove_entry(self, entry_id: str) -> bool:
        """
        Remove an entry by ID.

        Args:
            entry_id: ID of entry to remove

        Returns:
            True if entry was found and removed
        """
        for i, entry in enumerate(self.window.entries):
            if entry.entry_id == entry_id:
                self.window.current_tokens -= entry.tokens
                self.window.entries.pop(i)
                return True
        return False

    def get_usage_fraction(self) -> float:
        """Get current token usage as fraction of max_tokens."""
        if self.window.max_tokens == 0:
            return 0.0
        return self.window.current_tokens / self.window.max_tokens

    def get_usage_percentage(self) -> float:
        """Get current token usage as percentage."""
        return self.get_usage_fraction() * 100

    def should_warn(self) -> bool:
        """Check if usage exceeds warning threshold."""
        return self.get_usage_fraction() >= self.window.warning_threshold

    def is_critical(self) -> bool:
        """Check if usage exceeds critical threshold."""
        return self.get_usage_fraction() >= self.window.critical_threshold

    def should_prune(self) -> bool:
        """Check if pruning is recommended."""
        return self.get_usage_fraction() >= (self.window.warning_threshold + 0.05)

    def get_status(self) -> Dict[str, Any]:
        """Get current status information."""
        return {
            "current_tokens": self.window.current_tokens,
            "max_tokens": self.window.max_tokens,
            "usage_fraction": self.get_usage_fraction(),
            "usage_percentage": self.get_usage_percentage(),
            "entry_count": len(self.window.entries),
            "should_warn": self.should_warn(),
            "is_critical": self.is_critical(),
            "should_prune": self.should_prune(),
            "last_pruned": self.window.last_pruned.isoformat() if self.window.last_pruned else None,
            "prune_count": self.window.prune_count,
        }

    def prune(
        self,
        target_fraction: float = 0.75,
        strategy: Optional[PruningStrategy] = None,
    ) -> List[ContextEntry]:
        """
        Prune context window to target fraction using specified strategy.

        Args:
            target_fraction: Target usage fraction after pruning (0-1)
            strategy: Pruning strategy (uses default if not specified)

        Returns:
            List of removed entries
        """
        start_time = time.time()
        strategy = strategy or self.pruning_strategy

        target_tokens = int(self.window.max_tokens * target_fraction)
        removed = []

        if self.window.current_tokens <= target_tokens:
            return removed  # Nothing to prune

        if strategy == PruningStrategy.RECENT_PRIORITY:
            removed = self._prune_recent_priority(target_tokens)
        elif strategy == PruningStrategy.IMPORTANCE_SCORE:
            removed = self._prune_importance_score(target_tokens)
        elif strategy == PruningStrategy.CUSTOM:
            removed = self._prune_custom(target_tokens)
        elif strategy == PruningStrategy.ROUND_ROBIN:
            removed = self._prune_round_robin(target_tokens)
        else:
            removed = self._prune_recent_priority(target_tokens)

        # Update window state
        self.window.last_pruned = datetime.now()
        self.window.prune_count += 1

        # Track performance
        self._prune_times.append(time.time() - start_time)

        return removed

    def _prune_recent_priority(self, target_tokens: int) -> List[ContextEntry]:
        """Prune keeping most recent entries."""
        removed = []
        tokens_to_remove = self.window.current_tokens - target_tokens

        # Remove oldest entries until target is reached
        while self.window.current_tokens > target_tokens and self.window.entries:
            entry = self.window.entries.pop(0)
            self.window.current_tokens -= entry.tokens
            removed.append(entry)

        return removed

    def _prune_importance_score(self, target_tokens: int) -> List[ContextEntry]:
        """Prune keeping high-importance entries."""
        # Sort by importance (lowest first)
        sorted_entries = sorted(
            enumerate(self.window.entries),
            key=lambda x: (x[1].importance, x[1].timestamp),
        )

        removed = []
        tokens_to_remove = self.window.current_tokens - target_tokens
        removed_indices = set()

        for idx, (original_idx, entry) in enumerate(sorted_entries):
            if tokens_to_remove <= 0:
                break

            self.window.current_tokens -= entry.tokens
            tokens_to_remove -= entry.tokens
            removed_indices.add(original_idx)
            removed.append(entry)

        # Rebuild entries list keeping those not removed
        self.window.entries = [
            entry for i, entry in enumerate(self.window.entries)
            if i not in removed_indices
        ]

        return removed

    def _prune_custom(self, target_tokens: int) -> List[ContextEntry]:
        """Prune using custom scoring function."""
        if not self._custom_score_func:
            return self._prune_importance_score(target_tokens)

        # Score all entries
        scored = [
            (self._custom_score_func(entry), i, entry)
            for i, entry in enumerate(self.window.entries)
        ]

        # Sort by score (lowest first)
        scored.sort(key=lambda x: x[0])

        removed = []
        tokens_to_remove = self.window.current_tokens - target_tokens
        removed_indices = set()

        for score, original_idx, entry in scored:
            if tokens_to_remove <= 0:
                break

            self.window.current_tokens -= entry.tokens
            tokens_to_remove -= entry.tokens
            removed_indices.add(original_idx)
            removed.append(entry)

        # Rebuild entries list
        self.window.entries = [
            entry for i, entry in enumerate(self.window.entries)
            if i not in removed_indices
        ]

        return removed

    def _prune_round_robin(self, target_tokens: int) -> List[ContextEntry]:
        """Prune distributing across categories."""
        # Group by category
        by_category: Dict[str, List[ContextEntry]] = {}
        for entry in self.window.entries:
            if entry.category not in by_category:
                by_category[entry.category] = []
            by_category[entry.category].append(entry)

        removed = []
        tokens_to_remove = self.window.current_tokens - target_tokens

        # Prune from each category proportionally
        while tokens_to_remove > 0 and by_category:
            for category in list(by_category.keys()):
                if not by_category[category]:
                    continue

                entry = by_category[category].pop(0)
                self.window.current_tokens -= entry.tokens
                tokens_to_remove -= entry.tokens
                removed.append(entry)

        # Rebuild entries from remaining categories
        self.window.entries = []
        for category_entries in by_category.values():
            self.window.entries.extend(category_entries)

        return removed

    def set_custom_score_function(self, func: Callable[[ContextEntry], float]) -> None:
        """
        Set custom scoring function for pruning.

        Args:
            func: Function that takes ContextEntry and returns score (lower = prune first)
        """
        self._custom_score_func = func

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            "avg_add_time_ms": sum(self._add_times) / len(self._add_times) * 1000 if self._add_times else 0,
            "avg_prune_time_ms": sum(self._prune_times) / len(self._prune_times) * 1000 if self._prune_times else 0,
            "total_adds": len(self._add_times),
            "total_prunes": len(self._prune_times),
        }

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        # Rough approximation: ~4 characters per token
        return len(text) // 4

    def get_entries_by_category(self, category: str) -> List[ContextEntry]:
        """Get all entries of a specific category."""
        return [e for e in self.window.entries if e.category == category]

    def get_category_token_usage(self) -> Dict[str, int]:
        """Get token usage broken down by category."""
        usage = {}
        for entry in self.window.entries:
            usage[entry.category] = usage.get(entry.category, 0) + entry.tokens
        return usage

    def clear(self) -> None:
        """Clear all entries from the context window."""
        self.window.entries.clear()
        self.window.current_tokens = 0
        self.window.last_pruned = None
        self.window.prune_count = 0


# Singleton instance
_global_context_manager: Optional[ContextManager] = None


def get_global_context_manager() -> ContextManager:
    """Get the global context manager instance."""
    global _global_context_manager
    if _global_context_manager is None:
        _global_context_manager = ContextManager()
    return _global_context_manager


def reset_global_context_manager() -> None:
    """Reset the global context manager (useful for testing)."""
    global _global_context_manager
    _global_context_manager = None
