"""
hooks.py — Lifecycle Hooks System

This module provides a comprehensive hooks system for managing the lifecycle
of skill execution. Hooks can be registered to execute at specific points
during skill execution, enabling cross-cutting concerns like logging,
monitoring, validation, and state synchronization.

Architecture:
- HookType: Enum of hook execution points
- HookPriority: Priority levels for hook ordering
- Hook: Callable with metadata
- HookRegistry: Central registry for hook management
- HookContext: Context passed to hook callbacks

Usage:
    registry = HookRegistry()
    registry.register(HookType.PRE_EXECUTION, my_hook, priority=HookPriority.HIGH)
    registry.execute_hooks(HookType.PRE_EXECUTION, context)
"""

from __future__ import annotations

import time
import functools
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Union,
)
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from datetime import datetime
import threading


class HookType(Enum):
    """Types of hooks based on execution point."""

    # Skill lifecycle hooks
    PRE_SKILL_EXECUTION = "pre_skill_execution"
    POST_SKILL_EXECUTION = "post_skill_execution"
    ON_SKILL_ERROR = "on_skill_error"

    # Tool lifecycle hooks
    PRE_TOOL_CALL = "pre_tool_call"
    POST_TOOL_CALL = "post_tool_call"
    ON_TOOL_ERROR = "on_tool_error"

    # State management hooks
    ON_STATE_CHANGE = "on_state_change"
    ON_SESSION_START = "on_session_start"
    ON_SESSION_END = "on_session_end"

    # Context management hooks
    ON_TOKEN_THRESHOLD = "on_token_threshold"
    ON_CONTEXT_PRUNE = "on_context_prune"

    # Monitoring hooks
    ON_METRICS_COLLECTED = "on_metrics_collected"
    ON_VALIDATION_COMPLETE = "on_validation_complete"


class HookPriority(IntEnum):
    """Priority levels for hook execution order (higher executes first)."""

    CRITICAL = 100
    HIGH = 75
    NORMAL = 50
    LOW = 25
    BACKGROUND = 0


@dataclass
class HookContext:
    """
    Context passed to hook callbacks.

    Contains information about the event that triggered the hook
    and relevant state for the hook to use.
    """
    hook_type: HookType
    event_timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Skill execution context (if applicable)
    skill_name: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    error: Optional[Exception] = None

    # Tool execution context (if applicable)
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Optional[Any] = None

    # State management (if applicable)
    old_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None

    # Performance metrics
    duration_ms: int = 0
    tokens_used: int = 0

    # Session information
    session_id: Optional[str] = None
    user_id: Optional[str] = None


HookCallback = Callable[[HookContext], None]
"""Type alias for hook callback functions."""


@dataclass
class Hook:
    """
    Registered hook with metadata.

    Attributes:
        name: Unique identifier for the hook
        hook_type: Type of hook (when it executes)
        callback: Function to call when hook is triggered
        priority: Execution priority (higher executes first)
        enabled: Whether the hook is currently enabled
        tags: Tags for filtering and management
        metadata: Additional metadata
    """
    name: str
    hook_type: HookType
    callback: HookCallback
    priority: HookPriority = HookPriority.NORMAL
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def execute(self, context: HookContext) -> None:
        """Execute the hook callback with the given context."""
        if not self.enabled:
            return

        try:
            self.callback(context)
        except Exception as e:
            # Log but don't raise - hooks shouldn't break execution
            print(f"Hook '{self.name}' failed: {e}")


class HookRegistry:
    """
    Central registry for managing lifecycle hooks.

    Hooks are organized by type and executed in priority order when
    triggered. Thread-safe for concurrent access.
    """

    def __init__(self):
        """Initialize an empty hook registry."""
        self._hooks: Dict[HookType, List[Hook]] = {}
        self._lock = threading.RLock()

    def register(
        self,
        hook_type: HookType,
        callback: HookCallback,
        name: Optional[str] = None,
        priority: HookPriority = HookPriority.NORMAL,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Hook:
        """
        Register a new hook.

        Args:
            hook_type: Type of hook to register
            callback: Function to call when hook is triggered
            name: Optional name (auto-generated if not provided)
            priority: Execution priority
            tags: Optional tags for categorization
            metadata: Optional metadata

        Returns:
            The registered Hook object
        """
        if name is None:
            # Auto-generate name from callback
            name = f"{hook_type.value}_{callback.__name__}"

        hook = Hook(
            name=name,
            hook_type=hook_type,
            callback=callback,
            priority=priority,
            tags=tags or [],
            metadata=metadata or {},
        )

        with self._lock:
            if hook_type not in self._hooks:
                self._hooks[hook_type] = []

            self._hooks[hook_type].append(hook)
            # Sort by priority descending (higher priority first)
            self._hooks[hook_type].sort(key=lambda h: h.priority, reverse=True)

        return hook

    def unregister(self, hook_name: str) -> bool:
        """
        Unregister a hook by name.

        Args:
            hook_name: Name of hook to unregister

        Returns:
            True if hook was found and removed, False otherwise
        """
        with self._lock:
            for hook_list in self._hooks.values():
                for i, hook in enumerate(hook_list):
                    if hook.name == hook_name:
                        hook_list.pop(i)
                        return True
        return False

    def enable(self, hook_name: str) -> bool:
        """Enable a hook by name."""
        with self._lock:
            for hook_list in self._hooks.values():
                for hook in hook_list:
                    if hook.name == hook_name:
                        hook.enabled = True
                        return True
        return False

    def disable(self, hook_name: str) -> bool:
        """Disable a hook by name."""
        with self._lock:
            for hook_list in self._hooks.values():
                for hook in hook_list:
                    if hook.name == hook_name:
                        hook.enabled = False
                        return True
        return False

    def execute_hooks(
        self,
        hook_type: HookType,
        context: HookContext,
    ) -> None:
        """
        Execute all registered hooks of a given type.

        Hooks are executed in priority order (highest to lowest).
        Errors in individual hooks are logged but don't stop execution.

        Args:
            hook_type: Type of hooks to execute
            context: Context to pass to hook callbacks
        """
        with self._lock:
            hooks = self._hooks.get(hook_type, []).copy()

        # Execute outside lock to avoid deadlocks
        for hook in hooks:
            hook.execute(context)

    def get_hooks(
        self,
        hook_type: Optional[HookType] = None,
        tag: Optional[str] = None,
        enabled_only: bool = False,
    ) -> List[Hook]:
        """
        Get registered hooks, optionally filtered.

        Args:
            hook_type: Filter by hook type (None = all types)
            tag: Filter by tag (None = no tag filter)
            enabled_only: Only return enabled hooks

        Returns:
            List of matching hooks
        """
        with self._lock:
            if hook_type:
                hooks = self._hooks.get(hook_type, []).copy()
            else:
                hooks = []
                for hook_list in self._hooks.values():
                    hooks.extend(hook_list)

            # Apply filters
            if tag:
                hooks = [h for h in hooks if tag in h.tags]

            if enabled_only:
                hooks = [h for h in hooks if h.enabled]

        return hooks

    @property
    def hook_count(self) -> int:
        """Total number of registered hooks."""
        with self._lock:
            return sum(len(hooks) for hooks in self._hooks.values())


# Standard hooks provided by the system

class StandardHooks:
    """Collection of standard hook implementations."""

    @staticmethod
    def logging_hook(context: HookContext) -> None:
        """Log hook execution for monitoring."""
        timestamp = context.event_timestamp.isoformat()
        print(f"[{timestamp}] Hook: {context.hook_type.value}")
        if context.skill_name:
            print(f"  Skill: {context.skill_name}")
        if context.duration_ms > 0:
            print(f"  Duration: {context.duration_ms}ms")
        if context.tokens_used > 0:
            print(f"  Tokens: {context.tokens_used}")

    @staticmethod
    def metrics_hook(context: HookContext) -> None:
        """Collect metrics from hook execution."""
        # In production, this would send to a metrics system
        metrics = {
            "hook_type": context.hook_type.value,
            "timestamp": context.event_timestamp.isoformat(),
            "duration_ms": context.duration_ms,
            "tokens_used": context.tokens_used,
        }
        if context.skill_name:
            metrics["skill_name"] = context.skill_name
        # Store/send metrics
        print(f"Metrics: {metrics}")

    @staticmethod
    def token_threshold_hook(threshold: float = 0.85) -> HookCallback:
        """
        Create a hook that warns when token threshold is exceeded.

        Args:
            threshold: Token threshold (0-1) as fraction of context window

        Returns:
            Hook callback function
        """
        def _hook(context: HookContext) -> None:
            # In production, this would check actual token usage
            # For now, it's a placeholder
            if context.tokens_used > 0:
                # Assume 100K token context window for example
                context_window = 100000
                usage = context.tokens_used / context_window
                if usage >= threshold:
                    print(
                        f"⚠️ Token threshold exceeded: "
                        f"{usage:.1%} used (threshold: {threshold:.1%})"
                    )

        return _hook

    @staticmethod
    def error_recovery_hook(context: HookContext) -> None:
        """Handle errors with logging and potential recovery."""
        if context.error:
            print(
                f"❌ Error in {context.hook_type.value}: "
                f"{type(context.error).__name__}: {context.error}"
            )
            # In production, could trigger recovery logic here


def setup_standard_hooks(registry: HookRegistry) -> None:
    """
    Register standard hooks with the given registry.

    Args:
        registry: HookRegistry to populate with standard hooks
    """
    # Logging hooks
    registry.register(
        HookType.PRE_SKILL_EXECUTION,
        StandardHooks.logging_hook,
        name="log_pre_execution",
        priority=HookPriority.LOW,
    )
    registry.register(
        HookType.POST_SKILL_EXECUTION,
        StandardHooks.logging_hook,
        name="log_post_execution",
        priority=HookPriority.LOW,
    )

    # Metrics hooks
    registry.register(
        HookType.POST_SKILL_EXECUTION,
        StandardHooks.metrics_hook,
        name="collect_metrics",
        priority=HookPriority.LOW,
    )

    # Token threshold hook
    registry.register(
        HookType.ON_TOKEN_THRESHOLD,
        StandardHooks.token_threshold_hook(0.85),
        name="token_warning",
        priority=HookPriority.HIGH,
    )

    # Error recovery hook
    registry.register(
        HookType.ON_SKILL_ERROR,
        StandardHooks.error_recovery_hook,
        name="error_recovery",
        priority=HookPriority.CRITICAL,
    )


# Singleton hook registry
_global_hook_registry: Optional[HookRegistry] = None


def get_global_hook_registry() -> HookRegistry:
    """Get the global hook registry instance."""
    global _global_hook_registry
    if _global_hook_registry is None:
        _global_hook_registry = HookRegistry()
        setup_standard_hooks(_global_hook_registry)
    return _global_hook_registry


def reset_global_hook_registry() -> None:
    """Reset the global hook registry (useful for testing)."""
    global _global_hook_registry
    _global_hook_registry = None


# Decorator for hook registration
def hook(
    hook_type: HookType,
    name: Optional[str] = None,
    priority: HookPriority = HookPriority.NORMAL,
    tags: Optional[List[str]] = None,
):
    """
    Decorator for registering a function as a hook.

    Usage:
        @hook(HookType.PRE_SKILL_EXECUTION, priority=HookPriority.HIGH)
        def my_hook(context):
            print("Skill execution starting")

    Args:
        hook_type: Type of hook to register
        name: Optional name (auto-generated if not provided)
        priority: Execution priority
        tags: Optional tags for categorization
    """
    def decorator(func: HookCallback) -> HookCallback:
        registry = get_global_hook_registry()
        registry.register(
            hook_type=hook_type,
            callback=func,
            name=name or func.__name__,
            priority=priority,
            tags=tags,
        )
        return func
    return decorator


# Context manager for hook execution
class HookExecution:
    """Context manager for automatic hook execution."""

    def __init__(
        self,
        hook_type: HookType,
        registry: Optional[HookRegistry] = None,
    ):
        """
        Initialize the context manager.

        Args:
            hook_type: Type of hooks to execute
            registry: Optional registry (uses global if not provided)
        """
        self.hook_type = hook_type
        self.registry = registry or get_global_hook_registry()
        self.context: Optional[HookContext] = None

    def __enter__(self) -> HookContext:
        """Enter context and execute pre-hooks."""
        self.context = HookContext(hook_type=self.hook_type)
        self.registry.execute_hooks(self.hook_type, self.context)
        return self.context

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and execute post-hooks."""
        if self.context:
            if exc_type is not None:
                self.context.error = exc_val
            self.registry.execute_hooks(self.hook_type, self.context)
