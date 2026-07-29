"""
logging_config.py — Structured Logging Configuration

This module provides production-grade structured logging with JSON output,
error classification, and performance metrics collection.

Architecture:
- LogFormatter: Structured JSON formatter
- LogClassifier: Error classification system
- MetricsCollector: Performance metrics collection
- configure_logging: Main logging setup function

Usage:
    configure_logging()
    logger = get_logger(__name__)
    logger.info("Skill executed", extra={"skill": "sub-core-analysis", "duration_ms": 1234})
"""

from __future__ import annotations

import sys
import logging
import json
import time
import traceback
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
)
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from pathlib import Path
import threading


class ErrorSeverity(Enum):
    """Severity classification for errors."""
    CRITICAL = "critical"  # System-level failure, requires immediate attention
    HIGH = "high"  # Major failure affecting core functionality
    MEDIUM = "medium"  # Partial failure with workarounds available
    LOW = "low"  # Minor issue with minimal impact
    INFO = "info"  # Informational, not an error


class ErrorCategory(Enum):
    """Category classification for errors."""
    RECOVERABLE = "recoverable"  # Can be retried or worked around
    FATAL = "fatal"  # Cannot continue execution
    TRANSIENT = "transient"  # Temporary failure (network, timeout)
    VALIDATION = "validation"  # Input validation failure
    AUTHENTICATION = "authentication"  # Auth-related failure
    RATE_LIMIT = "rate_limit"  # Rate limit exceeded
    TIMEOUT = "timeout"  # Operation timed out
    UNKNOWN = "unknown"  # Uncategorized error


@dataclass
class ErrorClassification:
    """Classification information for an error."""
    severity: ErrorSeverity
    category: ErrorCategory
    recoverable: bool
    requires_retry: bool
    user_message: Optional[str] = None
    internal_note: Optional[str] = None


class ErrorClassifier:
    """Classifies errors into severity and category."""

    # Error type mapping
    CLASSIFICATION_MAP: Dict[type, ErrorClassification] = {
        # Timeout errors
        TimeoutError: ErrorClassification(
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.TIMEOUT,
            recoverable=True,
            requires_retry=True,
            user_message="Operation timed out. Please try again.",
            internal_note="Timeout occurred during execution",
        ),

        # Network/transient errors
        ConnectionError: ErrorClassification(
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.TRANSIENT,
            recoverable=True,
            requires_retry=True,
            user_message="Network connection failed. Please check your connection.",
        ),

        # Validation errors
        ValueError: ErrorClassification(
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.VALIDATION,
            recoverable=False,
            requires_retry=False,
            user_message="Invalid input provided. Please check your request.",
        ),

        # Authentication errors
        PermissionError: ErrorClassification(
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.AUTHENTICATION,
            recoverable=False,
            requires_retry=False,
            user_message="Permission denied. Please check your credentials.",
        ),
    }

    @classmethod
    def classify(cls, error: Exception) -> ErrorClassification:
        """
        Classify an error into severity and category.

        Args:
            error: Exception to classify

        Returns:
            ErrorClassification with severity, category, and guidance
        """
        # Check for specific type match
        for error_type, classification in cls.CLASSIFICATION_MAP.items():
            if isinstance(error, error_type):
                return classification

        # Check for common patterns in error message
        error_msg = str(error).lower()

        if "timeout" in error_msg:
            return ErrorClassification(
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.TIMEOUT,
                recoverable=True,
                requires_retry=True,
                user_message="Operation timed out. Please try again.",
            )

        if "rate limit" in error_msg or "too many requests" in error_msg:
            return ErrorClassification(
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.RATE_LIMIT,
                recoverable=True,
                requires_retry=False,
                user_message="Rate limit exceeded. Please wait before trying again.",
            )

        if "auth" in error_msg or "credential" in error_msg or "unauthorized" in error_msg:
            return ErrorClassification(
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.AUTHENTICATION,
                recoverable=False,
                requires_retry=False,
                user_message="Authentication failed. Please check your credentials.",
            )

        if "not found" in error_msg or "404" in error_msg:
            return ErrorClassification(
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.TRANSIENT,
                recoverable=True,
                requires_retry=True,
                user_message="Resource not found. It may have been moved or deleted.",
            )

        # Default classification
        return ErrorClassification(
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.UNKNOWN,
            recoverable=True,
            requires_retry=False,
            user_message="An error occurred. Please try again.",
            internal_note=f"Unclassified error: {type(error).__name__}",
        )


class StructuredFormatter(logging.Formatter):
    """
    Structured JSON formatter for logging.

    Outputs log entries as JSON with consistent schema for parsing
    and analysis.
    """

    def __init__(self, timezone: str = "UTC"):
        """Initialize the formatter."""
        super().__init__()
        self.timezone = timezone

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as structured JSON."""
        # Base log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(
                record.created,
            ).astimezone().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add thread/process info
        log_entry.update({
            "thread_id": record.thread,
            "process_id": record.process,
        })

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields
        if hasattr(record, "skill_name"):
            log_entry["component"] = f"skill:{record.skill_name}"
        if hasattr(record, "event_type"):
            log_entry["event_type"] = record.event_type
        if hasattr(record, "duration_ms"):
            log_entry["metrics"] = {
                "duration_ms": record.duration_ms,
            }
        if hasattr(record, "tokens_used"):
            if "metrics" not in log_entry:
                log_entry["metrics"] = {}
            log_entry["metrics"]["tokens_used"] = record.tokens_used

        # Add any additional context
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "asctime", "skill_name", "event_type", "duration_ms", "tokens_used",
            }:
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


class MetricsCollector:
    """
    Collects and aggregates performance metrics.

    Thread-safe collection of timing data, token usage, and execution
    statistics for monitoring and analysis.
    """

    def __init__(self):
        """Initialize the metrics collector."""
        self._metrics: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.RLock()
        self._enabled = True

    def record(
        self,
        component: str,
        duration_ms: int,
        tokens_used: int = 0,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a metric entry.

        Args:
            component: Component name (e.g., skill name)
            duration_ms: Execution duration in milliseconds
            tokens_used: Number of tokens used
            success: Whether execution was successful
            metadata: Optional additional metadata
        """
        if not self._enabled:
            return

        with self._lock:
            if component not in self._metrics:
                self._metrics[component] = []

            self._metrics[component].append({
                "timestamp": datetime.now().isoformat(),
                "duration_ms": duration_ms,
                "tokens_used": tokens_used,
                "success": success,
                "metadata": metadata or {},
            })

    def get_stats(
        self,
        component: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get aggregated statistics.

        Args:
            component: Optional component to filter by

        Returns:
            Aggregated statistics dictionary
        """
        with self._lock:
            if component:
                entries = self._metrics.get(component, [])
                return self._aggregate_entries(entries, component)

            # Aggregate all components
            stats = {}
            for comp_name, entries in self._metrics.items():
                stats[comp_name] = self._aggregate_entries(entries, comp_name)
            return stats

    def _aggregate_entries(
        self,
        entries: List[Dict[str, Any]],
        component: str,
    ) -> Dict[str, Any]:
        """Aggregate entries into statistics."""
        if not entries:
            return {
                "component": component,
                "count": 0,
            }

        durations = [e["duration_ms"] for e in entries]
        tokens = [e["tokens_used"] for e in entries]
        success_count = sum(1 for e in entries if e["success"])

        return {
            "component": component,
            "count": len(entries),
            "success_rate": success_count / len(entries),
            "duration_ms": {
                "min": min(durations),
                "max": max(durations),
                "mean": sum(durations) / len(durations),
                "median": sorted(durations)[len(durations) // 2],
            },
            "tokens_used": {
                "min": min(tokens),
                "max": max(tokens),
                "mean": sum(tokens) / len(tokens),
                "total": sum(tokens),
            },
        }

    def clear(self, component: Optional[str] = None) -> None:
        """Clear metrics for component or all."""
        with self._lock:
            if component:
                self._metrics.pop(component, None)
            else:
                self._metrics.clear()

    def enable(self) -> None:
        """Enable metrics collection."""
        self._enabled = True

    def disable(self) -> None:
        """Disable metrics collection."""
        self._enabled = False


# Singleton metrics collector
_global_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = MetricsCollector()
    return _global_metrics_collector


def configure_logging(
    level: str = "INFO",
    format_type: str = "json",
    output_file: Optional[str] = None,
    max_size_mb: int = 10,
    backup_count: int = 3,
    enable_console: bool = True,
    enable_structured: bool = True,
) -> logging.Logger:
    """
    Configure structured logging for the skill system.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type (json, text)
        output_file: Optional file path for log output
        max_size_mb: Max size per log file in MB
        backup_count: Number of backup files to keep
        enable_console: Whether to enable console output
        enable_structured: Whether to use structured JSON format

    Returns:
        Configured root logger
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatter
    if enable_structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Add console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, level.upper()))
        root_logger.addHandler(console_handler)

    # Add file handler if specified
    if output_file:
        from logging.handlers import RotatingFileHandler

        log_path = Path(output_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count,
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, level.upper()))
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_execution(
    logger: logging.Logger,
    component: str,
    duration_ms: int,
    tokens_used: int = 0,
    success: bool = True,
    level: str = "INFO",
) -> None:
    """
    Log execution metrics.

    Args:
        logger: Logger instance
        component: Component name (skill, tool, etc.)
        duration_ms: Execution duration in milliseconds
        tokens_used: Number of tokens used
        success: Whether execution was successful
        level: Log level (INFO, DEBUG, etc.)
    """
    # Record metrics
    collector = get_metrics_collector()
    collector.record(component, duration_ms, tokens_used, success)

    # Log
    log_level = getattr(logging, level.upper())
    logger.log(
        log_level,
        f"{'Success' if success else 'Failure'}: {component} executed in {duration_ms}ms",
        extra={
            "skill_name": component,
            "duration_ms": duration_ms,
            "tokens_used": tokens_used,
            "event_type": "skill_execution",
        },
    )


def log_error(
    logger: logging.Logger,
    error: Exception,
    component: str,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an error with classification.

    Args:
        logger: Logger instance
        error: Exception that occurred
        component: Component where error occurred
        context: Optional additional context
    """
    # Classify error
    classification = ErrorClassifier.classify(error)

    # Build error info
    error_info = {
        "component": component,
        "severity": classification.severity.value,
        "category": classification.category.value,
        "recoverable": classification.recoverable,
        "requires_retry": classification.requires_retry,
        "error_type": type(error).__name__,
        "error_message": str(error),
    }

    if context:
        error_info.update(context)

    # Log with appropriate level
    if classification.severity == ErrorSeverity.CRITICAL:
        logger.critical(
            f"Critical error in {component}: {error}",
            extra=error_info,
            exc_info=True,
        )
    elif classification.severity in (ErrorSeverity.HIGH, ErrorSeverity.MEDIUM):
        logger.error(
            f"Error in {component}: {error}",
            extra=error_info,
            exc_info=True,
        )
    else:
        logger.warning(
            f"Issue in {component}: {error}",
            extra=error_info,
        )
