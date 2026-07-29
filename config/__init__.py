"""
Configuration module for in-game-photography-cinematography skill.

This module provides:
- Dynamic skill registry and resolution
- Agent routing with chain-of-thought logic
- Lifecycle hooks for execution management
- Type-safe configuration settings
"""

__version__ = "2.0.0"

from .skill_registry import (
    SkillDefinition,
    SkillRegistry,
    SkillExecutionContext,
    SkillExecutionResult,
)

from .agent_router import (
    AgentRoute,
    AgentRouter,
    RoutingContext,
    RoutingDecision,
)

from .hooks import (
    Hook,
    HookRegistry,
    HookContext,
    HookPriority,
    HookType,
)

from .settings import (
    SkillSettings,
    get_settings,
)

__all__ = [
    # Skill registry
    "SkillDefinition",
    "SkillRegistry",
    "SkillExecutionContext",
    "SkillExecutionResult",
    # Agent router
    "AgentRoute",
    "AgentRouter",
    "RoutingContext",
    "RoutingDecision",
    # Hooks
    "Hook",
    "HookRegistry",
    "HookContext",
    "HookPriority",
    "HookType",
    # Settings
    "SkillSettings",
    "get_settings",
]
