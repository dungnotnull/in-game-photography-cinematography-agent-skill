"""
tool_schemas.py — Schema-Defined Tool Execution

This module provides tool definitions with proper schemas, execution handlers,
validation, and timeout management. Tools are the building blocks that skills
use to perform their work (WebSearch, Read, Write, etc.).

Architecture:
- ToolDefinition: Schema for tool metadata and contracts
- ToolExecutor: Safe tool execution with timeout and fallback
- ToolRegistry: Central registry for all tools
- ToolResult: Structured result from tool execution

Usage:
    registry = ToolRegistry()
    registry.register(ToolDefinition(...))
    result = registry.execute("WebSearch", {"query": "composition techniques"})
"""

from __future__ import annotations

import sys
import time
import signal
import json
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Union,
)
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import functools


class ToolExecutionStatus(Enum):
    """Status of a tool execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ToolDefinition:
    """
    Definition of a tool with schema and execution metadata.

    Attributes:
        name: Unique identifier for the tool
        description: Human-readable description of what the tool does
        input_schema: JSON schema for input validation
        output_schema: JSON schema for output validation
        handler: Callable that executes the tool
        timeout: Maximum execution time in seconds
        requires_auth: Whether this tool requires authentication
        rate_limit: Optional rate limit per minute
        fallback_handler: Optional fallback handler if primary fails
        tags: Tags for categorization and filtering
        metadata: Additional metadata
    """
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    handler: Optional[Callable] = None
    timeout: int = 30
    requires_auth: bool = False
    rate_limit: Optional[int] = None
    fallback_handler: Optional[Callable] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate tool definition after initialization."""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Tool name must be a non-empty string")
        if not self.description or not isinstance(self.description, str):
            raise ValueError("Tool description must be a non-empty string")

        # If neither handler nor fallback is provided, set a default
        if self.handler is None and self.fallback_handler is None:
            # Default handler that returns a placeholder
            self.handler = lambda **kwargs: {
                "status": "placeholder",
                "message": f"Tool '{self.name}' not implemented",
            }


@dataclass
class ToolResult:
    """
    Result of a tool execution with metadata.

    Attributes:
        success: Whether execution was successful
        data: Output data from the tool
        error: Error message if execution failed
        status: Execution status
        duration_ms: Execution duration in milliseconds
        metadata: Additional metadata
        tool_name: Name of the tool that was executed
    """
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    status: ToolExecutionStatus = ToolExecutionStatus.COMPLETED
    duration_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    tool_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
            "tool_name": self.tool_name,
        }


class ToolTimeoutError(Exception):
    """Raised when tool execution times out."""
    pass


def execute_with_timeout(
    func: Callable,
    timeout: int,
    *args,
    **kwargs,
) -> Any:
    """
    Execute a function with a timeout.

    Args:
        func: Function to execute
        timeout: Timeout in seconds
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Result from func

    Raises:
        ToolTimeoutError: If execution times out
    """
    def timeout_handler(signum, frame):
        raise ToolTimeoutError(f"Function timed out after {timeout} seconds")

    # Set signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)

    try:
        result = func(*args, **kwargs)
        signal.alarm(0)  # Cancel alarm
        return result
    except ToolTimeoutError:
        signal.alarm(0)  # Cancel alarm
        raise
    finally:
        signal.signal(signal.SIGALRM, old_handler)  # Restore old handler


class ToolExecutor:
    """
    Executor for tool calls with validation, timeout, and error handling.

    Provides safe execution of tools with proper resource management and
    fallback support.
    """

    def __init__(self):
        """Initialize a new tool executor."""
        self._execution_count: Dict[str, int] = {}
        self._last_execution: Dict[str, datetime] = {}

    def execute(
        self,
        tool: ToolDefinition,
        inputs: Dict[str, Any],
        validate_input: bool = True,
        validate_output: bool = True,
    ) -> ToolResult:
        """
        Execute a tool with given inputs.

        Args:
            tool: ToolDefinition to execute
            inputs: Input data for the tool
            validate_input: Whether to validate inputs against schema
            validate_output: Whether to validate outputs against schema

        Returns:
            ToolResult with data or error information
        """
        start_time = time.time()
        result = ToolResult(tool_name=tool.name, status=ToolExecutionStatus.RUNNING)

        # Update execution tracking
        self._execution_count[tool.name] = self._execution_count.get(tool.name, 0) + 1
        self._last_execution[tool.name] = datetime.now()

        # Validate inputs
        if validate_input and tool.input_schema:
            input_valid, errors = self._validate_schema(inputs, tool.input_schema)
            if not input_valid:
                result.success = False
                result.status = ToolExecutionStatus.FAILED
                result.error = f"Input validation failed: {errors}"
                result.duration_ms = int((time.time() - start_time) * 1000)
                return result

        # Check rate limit
        if tool.rate_limit and not self._check_rate_limit(tool):
            result.success = False
            result.status = ToolExecutionStatus.FAILED
            result.error = f"Rate limit exceeded: {tool.rate_limit} per minute"
            result.duration_ms = int((time.time() - start_time) * 1000)
            return result

        # Execute with timeout
        try:
            if tool.handler:
                output = execute_with_timeout(
                    tool.handler,
                    tool.timeout,
                    **inputs,
                )
                result.data = output
                result.success = True
                result.status = ToolExecutionStatus.COMPLETED
            else:
                raise ValueError(f"Tool '{tool.name}' has no handler")

        except ToolTimeoutError:
            result.success = False
            result.status = ToolExecutionStatus.TIMEOUT
            result.error = f"Execution timed out after {tool.timeout} seconds"

            # Try fallback
            if tool.fallback_handler:
                try:
                    fallback_output = tool.fallback_handler(**inputs)
                    result.data = fallback_output
                    result.success = True
                    result.status = ToolExecutionStatus.COMPLETED
                    result.metadata["fallback_used"] = True
                except Exception as e:
                    result.error += f"; fallback also failed: {e}"

        except Exception as e:
            result.success = False
            result.status = ToolExecutionStatus.FAILED
            result.error = str(e)

            # Try fallback
            if tool.fallback_handler:
                try:
                    fallback_output = tool.fallback_handler(**inputs)
                    result.data = fallback_output
                    result.success = True
                    result.status = ToolExecutionStatus.COMPLETED
                    result.metadata["fallback_used"] = True
                except Exception as fallback_error:
                    result.error += f"; fallback also failed: {fallback_error}"

        # Validate outputs
        if result.success and validate_output and tool.output_schema:
            output_valid, errors = self._validate_schema(result.data, tool.output_schema)
            if not output_valid:
                result.success = False
                result.metadata["output_validation_errors"] = errors

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    def _validate_schema(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any],
    ) -> tuple[bool, List[str]]:
        """Validate data against a JSON schema."""
        errors = []

        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                errors.append(f"Required field '{field}' is missing")

        # Check field types
        properties = schema.get("properties", {})
        for field, prop_schema in properties.items():
            if field in data:
                expected_type = prop_schema.get("type")
                if expected_type and not self._check_type(data[field], expected_type):
                    errors.append(
                        f"Field '{field}' has wrong type: "
                        f"expected {expected_type}, got {type(data[field]).__name__}"
                    )

        return len(errors) == 0, errors

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }

        expected_python_type = type_map.get(expected_type)
        if expected_python_type is None:
            return True  # Unknown type, skip check

        return isinstance(value, expected_python_type)

    def _check_rate_limit(self, tool: ToolDefinition) -> bool:
        """Check if tool execution is within rate limit."""
        if not tool.rate_limit:
            return True

        last_exec = self._last_execution.get(tool.name)
        if not last_exec:
            return True

        # Check if within rate limit window (1 minute)
        time_since = (datetime.now() - last_exec).total_seconds()
        if time_since >= 60:
            return True

        # Check if under limit
        count = self._execution_count.get(tool.name, 0)
        return count < tool.rate_limit

    @property
    def execution_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get execution statistics for all tools."""
        stats = {}
        for tool_name, count in self._execution_count.items():
            last_exec = self._last_execution.get(tool_name)
            stats[tool_name] = {
                "execution_count": count,
                "last_execution": last_exec.isoformat() if last_exec else None,
            }
        return stats


class ToolRegistry:
    """
    Central registry for all tools in the system.

    Manages tool registration, resolution, and execution with proper
    validation and error handling.
    """

    def __init__(self):
        """Initialize an empty tool registry."""
        self._tools: Dict[str, ToolDefinition] = {}
        self._by_tag: Dict[str, List[str]] = {}
        self._executor = ToolExecutor()

    def register(self, tool: ToolDefinition) -> None:
        """
        Register a tool definition.

        Args:
            tool: ToolDefinition to register

        Raises:
            ValueError: If a tool with the same name is already registered
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")

        self._tools[tool.name] = tool

        # Index by tags
        for tag in tool.tags:
            if tag not in self._by_tag:
                self._by_tag[tag] = []
            self._by_tag[tag].append(tool.name)

    def unregister(self, tool_name: str) -> None:
        """Unregister a tool by name."""
        if tool_name in self._tools:
            tool = self._tools[tool_name]
            # Remove from tag index
            for tag in tool.tags:
                if tag in self._by_tag and tool_name in self._by_tag[tag]:
                    self._by_tag[tag].remove(tool_name)
            # Remove from main registry
            del self._tools[tool_name]

    def resolve(self, tool_name: str) -> Optional[ToolDefinition]:
        """
        Resolve a tool by name.

        Args:
            tool_name: Name of the tool to resolve

        Returns:
            ToolDefinition if found, None otherwise
        """
        return self._tools.get(tool_name)

    def execute(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        **kwargs,
    ) -> ToolResult:
        """
        Execute a tool by name with given inputs.

        Args:
            tool_name: Name of tool to execute
            inputs: Input data for the tool
            **kwargs: Additional arguments for executor

        Returns:
            ToolResult with data or error information
        """
        tool = self.resolve(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found in registry",
                tool_name=tool_name,
                status=ToolExecutionStatus.FAILED,
            )

        return self._executor.execute(tool, inputs, **kwargs)

    def find_by_tag(self, tag: str) -> List[ToolDefinition]:
        """
        Find all tools with a given tag.

        Args:
            tag: Tag to search for

        Returns:
            List of matching ToolDefinitions
        """
        tool_names = self._by_tag.get(tag, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    @property
    def tool_count(self) -> int:
        """Total number of registered tools."""
        return len(self._tools)

    @property
    def tool_names(self) -> List[str]:
        """List of all registered tool names."""
        return list(self._tools.keys())


# Singleton registry instance
_global_tool_registry: Optional[ToolRegistry] = None


def get_global_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _global_tool_registry
    if _global_tool_registry is None:
        _global_tool_registry = ToolRegistry()
    return _global_tool_registry


def reset_global_tool_registry() -> None:
    """Reset the global tool registry (useful for testing)."""
    global _global_tool_registry
    _global_tool_registry = None
