"""
skill_registry.py — Dynamic Skill Registry System

This module provides a dynamic skill loading and resolution system for the
in-game-photography-cinematography skill. Skills can be registered, resolved,
and executed with proper validation and error handling.

Architecture:
- SkillDefinition: Schema for skill metadata and contracts
- SkillRegistry: Central registry for all skills
- SkillExecutionContext: Execution context with state tracking
- SkillExecutionResult: Structured result with metadata

Usage:
    registry = SkillRegistry()
    registry.register_from_directory("skills/")
    skill = registry.resolve("sub-core-analysis")
    result = registry.execute(skill, context)
"""

from __future__ import annotations

import sys
import time
import hashlib
import json
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Union,
    runtime_checkable,
)
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re


class SkillExecutionStatus(Enum):
    """Status of a skill execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class RetryPolicy:
    """Retry policy for skill execution."""
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay,
        )
        if self.jitter:
            import random
            delay *= (0.5 + random.random())
        return delay


@dataclass
class SkillDefinition:
    """
    Definition of a skill with schema and execution metadata.

    Attributes:
        name: Unique identifier for the skill
        description: Human-readable description (also used for triggering)
        version: Skill version
        input_schema: JSON schema for input validation
        output_schema: JSON schema for output validation
        tool_dependencies: List of tools this skill requires
        file_path: Path to the skill's markdown file
        execution_timeout: Maximum execution time in seconds
        retry_policy: Retry policy for failures
        requires_auth: Whether this skill requires authentication
        tags: Tags for categorization and filtering
    """
    name: str
    description: str
    version: str = "1.0.0"
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    tool_dependencies: List[str] = field(default_factory=list)
    file_path: Optional[Path] = None
    execution_timeout: int = 300
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    requires_auth: bool = False
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate skill definition after initialization."""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Skill name must be a non-empty string")
        if not self.description or not isinstance(self.description, str):
            raise ValueError("Skill description must be a non-empty string")


@dataclass
class SkillExecutionContext:
    """
    Execution context for a skill invocation.

    Tracks state, inputs, outputs, and metadata during execution.
    """
    skill_name: str
    inputs: Dict[str, Any]
    language: str = "en"  # vi, en, or other
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    parent_context: Optional[SkillExecutionContext] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    # Execution tracking (populated during execution)
    status: SkillExecutionStatus = SkillExecutionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    outputs: Optional[Dict[str, Any]] = None
    error: Optional[Exception] = None

    # Token and performance tracking
    tokens_used: int = 0
    duration_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            "skill_name": self.skill_name,
            "inputs": self.inputs,
            "language": self.language,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "outputs": self.outputs,
            "error": str(self.error) if self.error else None,
            "tokens_used": self.tokens_used,
            "duration_ms": self.duration_ms,
        }


@dataclass
class SkillExecutionResult:
    """
    Result of a skill execution with metadata and metrics.
    """
    success: bool
    outputs: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    context: Optional[SkillExecutionContext] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Performance metrics
    duration_ms: int = 0
    tokens_used: int = 0

    # Validation results
    input_valid: bool = True
    output_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)


class SkillValidator:
    """Validator for skill inputs and outputs."""

    @staticmethod
    def validate_schema(
        data: Dict[str, Any],
        schema: Dict[str, Any],
    ) -> tuple[bool, List[str]]:
        """
        Validate data against a JSON schema.

        Returns:
            (is_valid, list_of_error_messages)
        """
        # Basic schema validation (extend with jsonschema for full validation)
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
                if expected_type and not SkillValidator._check_type(
                    data[field], expected_type
                ):
                    errors.append(
                        f"Field '{field}' has wrong type: "
                        f"expected {expected_type}, got {type(data[field]).__name__}"
                    )

        return len(errors) == 0, errors

    @staticmethod
    def _check_type(value: Any, expected_type: str) -> bool:
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


class SkillRegistry:
    """
    Central registry for all skills in the system.

    Manages skill registration, resolution, and execution with proper
    validation and error handling.
    """

    def __init__(self):
        """Initialize an empty skill registry."""
        self._skills: Dict[str, SkillDefinition] = {}
        self._by_tag: Dict[str, List[str]] = {}
        self._execution_history: List[SkillExecutionContext] = []

    def register(self, skill: SkillDefinition) -> None:
        """
        Register a skill definition.

        Args:
            skill: SkillDefinition to register

        Raises:
            ValueError: If a skill with the same name is already registered
        """
        if skill.name in self._skills:
            raise ValueError(f"Skill '{skill.name}' is already registered")

        self._skills[skill.name] = skill

        # Index by tags
        for tag in skill.tags:
            if tag not in self._by_tag:
                self._by_tag[tag] = []
            self._by_tag[tag].append(skill.name)

    def unregister(self, skill_name: str) -> None:
        """Unregister a skill by name."""
        if skill_name in self._skills:
            skill = self._skills[skill_name]
            # Remove from tag index
            for tag in skill.tags:
                if tag in self._by_tag and skill_name in self._by_tag[tag]:
                    self._by_tag[tag].remove(skill_name)
            # Remove from main registry
            del self._skills[skill_name]

    def resolve(self, skill_name: str) -> Optional[SkillDefinition]:
        """
        Resolve a skill by name.

        Args:
            skill_name: Name of the skill to resolve

        Returns:
            SkillDefinition if found, None otherwise
        """
        return self._skills.get(skill_name)

    def find_by_tag(self, tag: str) -> List[SkillDefinition]:
        """
        Find all skills with a given tag.

        Args:
            tag: Tag to search for

        Returns:
            List of matching SkillDefinitions
        """
        skill_names = self._by_tag.get(tag, [])
        return [self._skills[name] for name in skill_names if name in self._skills]

    def search(self, query: str) -> List[SkillDefinition]:
        """
        Search for skills by name or description.

        Args:
            query: Search query string

        Returns:
            List of matching SkillDefinitions, sorted by relevance
        """
        query_lower = query.lower()
        results = []

        for skill in self._skills.values():
            # Exact name match gets highest priority
            if skill.name.lower() == query_lower:
                results.append((skill, 100))
                continue

            # Partial name match
            if query_lower in skill.name.lower():
                results.append((skill, 80))
                continue

            # Description match
            if query_lower in skill.description.lower():
                results.append((skill, 60))
                continue

        # Sort by relevance score and return
        results.sort(key=lambda x: x[1], reverse=True)
        return [skill for skill, score in results]

    def register_from_directory(self, directory: Union[str, Path]) -> int:
        """
        Register all skills from a directory.

        Assumes markdown files with YAML frontmatter defining skills.

        Args:
            directory: Path to directory containing skill files

        Returns:
            Number of skills registered
        """
        directory = Path(directory)
        count = 0

        for file_path in directory.rglob("*.md"):
            try:
                skill = self._parse_skill_file(file_path)
                if skill:
                    self.register(skill)
                    count += 1
            except Exception as e:
                print(f"Warning: Failed to parse {file_path}: {e}")

        return count

    def _parse_skill_file(self, file_path: Path) -> Optional[SkillDefinition]:
        """Parse a skill markdown file into a SkillDefinition."""
        content = file_path.read_text(encoding="utf-8")

        # Extract YAML frontmatter
        frontmatter_match = re.match(
            r"^---\s*\n(.*?)\n---\s*\n",
            content,
            re.DOTALL,
        )

        if not frontmatter_match:
            return None

        try:
            import yaml
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
        except ImportError:
            # Fallback: simple parsing
            frontmatter = {}
            for line in frontmatter_match.group(1).split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip()

        # Extract skill name and description
        name = frontmatter.get("name")
        description = frontmatter.get("description")

        if not name or not description:
            return None

        # Create skill definition
        skill = SkillDefinition(
            name=name,
            description=description,
            version=frontmatter.get("version", "1.0.0"),
            file_path=file_path,
            tags=frontmatter.get("tags", []),
            metadata={
                "frontmatter": frontmatter,
                "file_size": file_path.stat().st_size,
                "last_modified": datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat(),
            },
        )

        return skill

    def execute(
        self,
        skill_name: str,
        inputs: Dict[str, Any],
        context: Optional[SkillExecutionContext] = None,
    ) -> SkillExecutionResult:
        """
        Execute a skill with given inputs.

        Args:
            skill_name: Name of skill to execute
            inputs: Input data for the skill
            context: Optional execution context

        Returns:
            SkillExecutionResult with outputs or error information
        """
        skill = self.resolve(skill_name)
        if not skill:
            return SkillExecutionResult(
                success=False,
                error=f"Skill '{skill_name}' not found in registry",
            )

        # Create context if not provided
        if context is None:
            context = SkillExecutionContext(skill_name=skill_name, inputs=inputs)

        # Validate inputs
        if skill.input_schema:
            input_valid, validation_errors = SkillValidator.validate_schema(
                inputs, skill.input_schema
            )
            if not input_valid:
                return SkillExecutionResult(
                    success=False,
                    error=f"Input validation failed: {validation_errors}",
                    context=context,
                    input_valid=False,
                    validation_errors=validation_errors,
                )

        # Execute skill (placeholder - actual implementation would invoke the skill)
        start_time = time.time()
        try:
            # TODO: Implement actual skill execution
            # For now, simulate execution
            outputs = {"result": "simulated_output"}

            result = SkillExecutionResult(
                success=True,
                outputs=outputs,
                context=context,
                duration_ms=int((time.time() - start_time) * 1000),
                input_valid=True,
            )

        except Exception as e:
            result = SkillExecutionResult(
                success=False,
                error=str(e),
                context=context,
                duration_ms=int((time.time() - start_time) * 1000),
            )

        # Record execution
        context.status = (
            SkillExecutionStatus.COMPLETED if result.success
            else SkillExecutionStatus.FAILED
        )
        context.completed_at = datetime.now()
        context.outputs = result.outputs
        context.error = result.error
        context.duration_ms = result.duration_ms

        self._execution_history.append(context)

        return result

    def get_execution_history(
        self,
        skill_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[SkillExecutionContext]:
        """
        Get execution history, optionally filtered by skill name.

        Args:
            skill_name: Optional skill name to filter by
            limit: Maximum number of entries to return

        Returns:
            List of execution contexts, most recent first
        """
        history = self._execution_history

        if skill_name:
            history = [ctx for ctx in history if ctx.skill_name == skill_name]

        # Return most recent first
        return list(reversed(history[-limit:]))

    @property
    def skill_count(self) -> int:
        """Total number of registered skills."""
        return len(self._skills)

    @property
    def skill_names(self) -> List[str]:
        """List of all registered skill names."""
        return list(self._skills.keys())


# Singleton registry instance
_global_registry: Optional[SkillRegistry] = None


def get_global_registry() -> SkillRegistry:
    """Get the global skill registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = SkillRegistry()
    return _global_registry


def reset_global_registry() -> None:
    """Reset the global skill registry (useful for testing)."""
    global _global_registry
    _global_registry = None
