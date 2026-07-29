"""
settings.py — Type-Safe Configuration Management

This module provides type-safe configuration management for the skill system.
Settings are loaded from environment variables, config files, and defaults,
with validation and schema enforcement.

Usage:
    settings = get_settings()
    print(settings.skill_version)
    print(settings.max_execution_time)
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
)
from dataclasses import dataclass, field, asdict
from enum import Enum
import functools


T = TypeVar("T")


class ConfigLoadError(Exception):
    """Error loading configuration."""
    pass


class ConfigValidationError(Exception):
    """Error validating configuration."""
    pass


def get_env(
    key: str,
    default: Optional[str] = None,
    required: bool = False,
) -> Optional[str]:
    """
    Get environment variable with optional default and requirement check.

    Args:
        key: Environment variable name
        default: Default value if not found
        required: Whether the variable is required

    Returns:
        Environment variable value or default

    Raises:
        ConfigLoadError: If required variable is not found
    """
    value = os.environ.get(key, default)

    if required and value is None:
        raise ConfigLoadError(f"Required environment variable '{key}' not set")

    return value


def parse_bool(value: Optional[str]) -> bool:
    """Parse a string value to boolean."""
    if value is None:
        return False
    return value.lower() in ("true", "1", "yes", "on")


def parse_list(value: Optional[str], delimiter: str = ",") -> List[str]:
    """Parse a string value to list."""
    if value is None:
        return []
    return [item.strip() for item in value.split(delimiter) if item.strip()]


def parse_int(value: Optional[str], default: int = 0) -> int:
    """Parse a string value to integer."""
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def parse_float(value: Optional[str], default: float = 0.0) -> float:
    """Parse a string value to float."""
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class LoggingSettings:
    """Logging configuration settings."""

    level: str = "INFO"
    format: str = "json"
    output_file: Optional[str] = None
    max_size_mb: int = 10
    backup_count: int = 3
    enable_console: bool = True
    enable_structured: bool = True

    @classmethod
    def from_env(cls) -> LoggingSettings:
        """Create settings from environment variables."""
        return cls(
            level=get_env("SKILL_LOG_LEVEL", "INFO"),
            format=get_env("SKILL_LOG_FORMAT", "json"),
            output_file=get_env("SKILL_LOG_FILE"),
            max_size_mb=parse_int(get_env("SKILL_LOG_MAX_SIZE_MB"), 10),
            backup_count=parse_int(get_env("SKILL_LOG_BACKUP_COUNT"), 3),
            enable_console=parse_bool(get_env("SKILL_LOG_CONSOLE", "true")),
            enable_structured=parse_bool(get_env("SKILL_LOG_STRUCTURED", "true")),
        )


@dataclass(frozen=True)
class ExecutionSettings:
    """Skill execution configuration settings."""

    max_execution_time: int = 300  # seconds
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    timeout_grace_period: float = 5.0  # seconds
    enable_fallback: bool = True
    parallel_execution: bool = False

    @classmethod
    def from_env(cls) -> ExecutionSettings:
        """Create settings from environment variables."""
        return cls(
            max_execution_time=parse_int(get_env("SKILL_MAX_EXECUTION_TIME"), 300),
            max_retries=parse_int(get_env("SKILL_MAX_RETRIES"), 3),
            retry_delay=parse_float(get_env("SKILL_RETRY_DELAY"), 1.0),
            timeout_grace_period=parse_float(get_env("SKILL_TIMEOUT_GRACE"), 5.0),
            enable_fallback=parse_bool(get_env("SKILL_ENABLE_FALLBACK", "true")),
            parallel_execution=parse_bool(get_env("SKILL_PARALLEL_EXECUTION", "false")),
        )


@dataclass(frozen=True)
class ContextSettings:
    """Context window management settings."""

    max_tokens: int = 100000
    warning_threshold: float = 0.85  # 85% of max
    critical_threshold: float = 0.95  # 95% of max
    enable_auto_prune: bool = True
    prune_strategy: str = "recent_priority"  # recent_priority, importance, custom

    @classmethod
    def from_env(cls) -> ContextSettings:
        """Create settings from environment variables."""
        return cls(
            max_tokens=parse_int(get_env("SKILL_MAX_TOKENS"), 100000),
            warning_threshold=parse_float(get_env("SKILL_WARNING_THRESHOLD"), 0.85),
            critical_threshold=parse_float(get_env("SKILL_CRITICAL_THRESHOLD"), 0.95),
            enable_auto_prune=parse_bool(get_env("SKILL_AUTO_PRUNE", "true")),
            prune_strategy=get_env("SKILL_PRUNE_STRATEGY", "recent_priority"),
        )


@dataclass(frozen=True)
class KnowledgeSettings:
    """Knowledge base and crawl settings."""

    update_interval_hours: int = 168  # 1 week
    news_update_interval_hours: int = 24  # 1 day
    max_entries: int = 1000
    dedup_enabled: bool = True
    score_threshold: float = 5.0  # minimum relevance score

    @classmethod
    def from_env(cls) -> KnowledgeSettings:
        """Create settings from environment variables."""
        return cls(
            update_interval_hours=parse_int(get_env("SKILL_KNOWLEDGE_UPDATE_INTERVAL"), 168),
            news_update_interval_hours=parse_int(get_env("SKILL_NEWS_UPDATE_INTERVAL"), 24),
            max_entries=parse_int(get_env("SKILL_MAX_KNOWLEDGE_ENTRIES"), 1000),
            dedup_enabled=parse_bool(get_env("SKILL_DEDUP_ENABLED", "true")),
            score_threshold=parse_float(get_env("SKILL_SCORE_THRESHOLD"), 5.0),
        )


@dataclass(frozen=True)
class APISettings:
    """External API configuration settings."""

    anthropic_api_key: Optional[str] = None
    semantic_scholar_api_key: Optional[str] = None
    request_timeout: int = 30  # seconds
    max_concurrent_requests: int = 5

    @classmethod
    def from_env(cls) -> APISettings:
        """Create settings from environment variables."""
        return cls(
            anthropic_api_key=get_env("ANTHROPIC_API_KEY"),
            semantic_scholar_api_key=get_env("SEMANTIC_SCHOLAR_API_KEY"),
            request_timeout=parse_int(get_env("SKILL_API_TIMEOUT"), 30),
            max_concurrent_requests=parse_int(get_env("SKILL_MAX_CONCURRENT_REQUESTS"), 5),
        )


@dataclass(frozen=True)
class SkillSettings:
    """
    Main settings container for the skill system.

    All configuration is centralized here with type-safe access and
    validation. Settings are loaded from environment variables and
    optional config file.
    """

    # Skill metadata
    skill_name: str = "in-game-photography-cinematography"
    skill_version: str = "2.0.0"
    skill_description: str = "Virtual Photography & Game Cinematography analysis harness"

    # Environment
    environment: str = "development"  # development, staging, production
    debug: bool = False

    # Sub-settings
    logging: LoggingSettings = field(default_factory=LoggingSettings.from_env)
    execution: ExecutionSettings = field(default_factory=ExecutionSettings.from_env)
    context: ContextSettings = field(default_factory=ContextSettings.from_env)
    knowledge: KnowledgeSettings = field(default_factory=KnowledgeSettings.from_env)
    api: APISettings = field(default_factory=APISettings.from_env)

    # Feature flags
    enable_hooks: bool = True
    enable_routing: bool = True
    enable_caching: bool = True
    enable_metrics: bool = True

    @classmethod
    def from_env(cls) -> SkillSettings:
        """Create settings from environment variables."""
        return cls(
            skill_name=get_env("SKILL_NAME", "in-game-photography-cinematography"),
            skill_version=get_env("SKILL_VERSION", "2.0.0"),
            skill_description=get_env(
                "SKILL_DESCRIPTION",
                "Virtual Photography & Game Cinematography analysis harness"
            ),
            environment=get_env("SKILL_ENVIRONMENT", "development"),
            debug=parse_bool(get_env("SKILL_DEBUG", "false")),
            logging=LoggingSettings.from_env(),
            execution=ExecutionSettings.from_env(),
            context=ContextSettings.from_env(),
            knowledge=KnowledgeSettings.from_env(),
            api=APISettings.from_env(),
            enable_hooks=parse_bool(get_env("SKILL_ENABLE_HOOKS", "true")),
            enable_routing=parse_bool(get_env("SKILL_ENABLE_ROUTING", "true")),
            enable_caching=parse_bool(get_env("SKILL_ENABLE_CACHING", "true")),
            enable_metrics=parse_bool(get_env("SKILL_ENABLE_METRICS", "true")),
        )

    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> SkillSettings:
        """
        Load settings from a JSON config file.

        Args:
            config_path: Path to config file

        Returns:
            SkillSettings instance

        Raises:
            ConfigLoadError: If file cannot be loaded
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise ConfigLoadError(f"Config file not found: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigLoadError(f"Invalid JSON in config file: {e}")

        # Recursively build settings from dict
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> SkillSettings:
        """Build settings from nested dictionary."""
        # Extract sub-settings
        logging_data = data.get("logging", {})
        execution_data = data.get("execution", {})
        context_data = data.get("context", {})
        knowledge_data = data.get("knowledge", {})
        api_data = data.get("api", {})

        return cls(
            skill_name=data.get("skill_name", "in-game-photography-cinematography"),
            skill_version=data.get("skill_version", "2.0.0"),
            skill_description=data.get(
                "skill_description",
                "Virtual Photography & Game Cinematography analysis harness"
            ),
            environment=data.get("environment", "development"),
            debug=data.get("debug", False),
            logging=LoggingSettings(**logging_data) if logging_data else LoggingSettings.from_env(),
            execution=ExecutionSettings(**execution_data) if execution_data else ExecutionSettings.from_env(),
            context=ContextSettings(**context_data) if context_data else ContextSettings.from_env(),
            knowledge=KnowledgeSettings(**knowledge_data) if knowledge_data else KnowledgeSettings.from_env(),
            api=APISettings(**api_data) if api_data else APISettings.from_env(),
            enable_hooks=data.get("enable_hooks", True),
            enable_routing=data.get("enable_routing", True),
            enable_caching=data.get("enable_caching", True),
            enable_metrics=data.get("enable_metrics", True),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for serialization."""
        return {
            "skill_name": self.skill_name,
            "skill_version": self.skill_version,
            "skill_description": self.skill_description,
            "environment": self.environment,
            "debug": self.debug,
            "logging": asdict(self.logging),
            "execution": asdict(self.execution),
            "context": asdict(self.context),
            "knowledge": asdict(self.knowledge),
            "api": asdict(self.api),
            "enable_hooks": self.enable_hooks,
            "enable_routing": self.enable_routing,
            "enable_caching": self.enable_caching,
            "enable_metrics": self.enable_metrics,
        }

    def validate(self) -> List[str]:
        """
        Validate settings and return list of errors (empty if valid).

        Returns:
            List of validation error messages
        """
        errors = []

        # Validate environment
        if self.environment not in ("development", "staging", "production"):
            errors.append(f"Invalid environment: {self.environment}")

        # Validate execution time
        if self.execution.max_execution_time <= 0:
            errors.append("max_execution_time must be positive")

        # Validate context thresholds
        if not 0 < self.context.warning_threshold < 1:
            errors.append("warning_threshold must be between 0 and 1")

        if not 0 < self.context.critical_threshold < 1:
            errors.append("critical_threshold must be between 0 and 1")

        if self.context.critical_threshold <= self.context.warning_threshold:
            errors.append("critical_threshold must be greater than warning_threshold")

        # Validate context window
        if self.context.max_tokens <= 0:
            errors.append("max_tokens must be positive")

        # Validate knowledge settings
        if self.knowledge.max_entries <= 0:
            errors.append("max_entries must be positive")

        if not 0 <= self.knowledge.score_threshold <= 10:
            errors.append("score_threshold must be between 0 and 10")

        return errors

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


# Global settings instance
_global_settings: Optional[SkillSettings] = None


def get_settings(
    reload: bool = False,
    config_path: Optional[Union[str, Path]] = None,
) -> SkillSettings:
    """
    Get the global settings instance.

    Args:
        reload: Force reload of settings
        config_path: Optional path to config file

    Returns:
        SkillSettings instance

    Raises:
        ConfigLoadError: If config file is specified but cannot be loaded
        ConfigValidationError: If settings fail validation
    """
    global _global_settings

    if _global_settings is None or reload:
        if config_path:
            _global_settings = SkillSettings.from_file(config_path)
        else:
            _global_settings = SkillSettings.from_env()

        # Validate settings
        errors = _global_settings.validate()
        if errors:
            raise ConfigValidationError(
                f"Settings validation failed: {'; '.join(errors)}"
            )

    return _global_settings


def reset_settings() -> None:
    """Reset global settings (useful for testing)."""
    global _global_settings
    _global_settings = None


def save_settings(settings: SkillSettings, config_path: Union[str, Path]) -> None:
    """
    Save settings to a JSON config file.

    Args:
        settings: Settings to save
        config_path: Path to save config file
    """
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(settings.to_dict(), f, indent=2, ensure_ascii=False)
