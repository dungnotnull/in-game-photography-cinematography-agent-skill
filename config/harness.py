"""
harness.py — Complete Integration Harness

This module provides the complete integration harness that ties together
all the v2.0.0 infrastructure components into a cohesive system.

Components integrated:
- Skill registry and router
- Tool handlers and executor
- Hooks system
- Context manager
- Logging and metrics

Usage:
    harness = SkillHarness()
    result = harness.execute("in-game-photography-cinematography", user_query)
"""

from __future__ import annotations

import time
from typing import (
    Any,
    Dict,
    List,
    Optional,
)
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

from .skill_registry import (
    get_global_registry,
    SkillExecutionContext,
    SkillExecutionResult,
)
from .agent_router import (
    get_global_router,
    RoutingContext,
    RoutingDecision,
)
from .hooks import (
    get_global_hook_registry,
    HookContext,
    HookType,
)
from .tool_schemas import (
    get_global_tool_registry,
)
from .tool_handlers import (
    initialize_tool_registry,
)
from .context_manager import (
    get_global_context_manager,
)
from .logging_config import (
    get_logger,
    log_execution,
    log_error,
)


@dataclass
class HarnessConfig:
    """Configuration for the skill harness."""
    enable_hooks: bool = True
    enable_routing: bool = True
    enable_metrics: bool = True
    enable_context_management: bool = True
    log_execution: bool = True
    max_execution_time: int = 300  # seconds


class SkillHarness:
    """
    Complete integration harness for skill execution.

    Ties together all v2.0.0 infrastructure components:
    - Skill registry and dynamic loading
    - Agent router with chain-of-thought
    - Tool handlers and execution
    - Lifecycle hooks
    - Context window management
    - Structured logging and metrics
    """

    def __init__(self, config: Optional[HarnessConfig] = None):
        """
        Initialize the skill harness.

        Args:
            config: Optional harness configuration
        """
        self.config = config or HarnessConfig()

        # Initialize logger first
        self._logger = get_logger(__name__)

        # Initialize components
        self._skill_registry = get_global_registry()
        self._agent_router = get_global_router()
        self._hook_registry = get_global_hook_registry()
        self._tool_registry = None  # Lazy initialize
        self._context_manager = get_global_context_manager()

        # Load skills from directory
        self._load_skills()

        # Setup routes
        self._setup_routes()

    def _load_skills(self) -> None:
        """Load all skills from the skills directory."""
        skills_dir = Path(__file__).parent.parent / "skills"
        if skills_dir.exists():
            count = self._skill_registry.register_from_directory(skills_dir)
            self._logger.info(f"Loaded {count} skills from {skills_dir}")

    def _setup_routes(self) -> None:
        """Setup agent routing rules."""
        from .agent_router import AgentRoute

        # Core analysis route
        self._agent_router.add_route(AgentRoute(
            name="analysis_route",
            condition="composition" or "camera" or "lighting" or "angle" or "focal" or "photo mode",
            target_skill="sub-core-analysis",
            priority=75,
            fallback_skill="sub-advisor",
            tags=["analysis", "core"],
        ))

        # Requirements gathering route
        self._agent_router.add_route(AgentRoute(
            name="requirements_route",
            condition="clarify" or "requirements" or "scope" or "inputs",
            target_skill="sub-gather-requirements",
            priority=90,
            tags=["intake", "requirements"],
        ))

        # Evidence collection route
        self._agent_router.add_route(AgentRoute(
            name="evidence_route",
            condition="search" or "fetch" or "find" or "data" or "docs",
            target_skill="sub-evidence-collector",
            priority=70,
            tags=["data", "collection"],
        ))

        # Knowledge query route
        self._agent_router.add_route(AgentRoute(
            name="knowledge_route",
            condition="academic" or "research" or "citation" or "evidence",
            target_skill="sub-knowledge-updater",
            priority=65,
            tags=["knowledge", "research"],
        ))

        # Advisor route
        self._agent_router.add_route(AgentRoute(
            name="advisor_route",
            condition="recommend" or "advise" or "conclusion" or "verdict",
            target_skill="sub-advisor",
            priority=60,
            tags=["advisory", "synthesis"],
        ))

    def execute(
        self,
        skill_name: str,
        query: str,
        inputs: Optional[Dict[str, Any]] = None,
        language: str = "en",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> SkillExecutionResult:
        """
        Execute a skill with full harness integration.

        Args:
            skill_name: Name of skill to execute
            query: User query or task description
            inputs: Optional additional inputs
            language: Language code (en, vi, other)
            user_id: Optional user identifier
            session_id: Optional session identifier

        Returns:
            SkillExecutionResult with outputs and metadata
        """
        start_time = time.time()

        # Initialize tool registry if needed
        if self._tool_registry is None:
            self._tool_registry = initialize_tool_registry()

        # Prepare inputs
        if inputs is None:
            inputs = {}
        inputs["query"] = query

        # Create execution context
        execution_context = SkillExecutionContext(
            skill_name=skill_name,
            inputs=inputs,
            language=language,
            user_id=user_id,
            session_id=session_id,
        )

        # Pre-execution hooks
        if self.config.enable_hooks:
            self._execute_pre_hooks(execution_context)

        # Track context if enabled
        if self.config.enable_context_management:
            estimated_tokens = len(query) // 4  # Rough estimate
            self._context_manager.track_tokens(estimated_tokens)

        try:
            # Execute the skill
            result = self._skill_registry.execute(
                skill_name,
                inputs,
                execution_context,
            )

            # Update context with actual usage
            execution_context.duration_ms = result.duration_ms
            execution_context.tokens_used = result.tokens_used

        except Exception as e:
            # Handle execution error
            log_error(self._logger, e, skill_name)

            result = SkillExecutionResult(
                success=False,
                error=str(e),
                context=execution_context,
            )

            # Error hooks
            if self.config.enable_hooks:
                self._execute_error_hooks(execution_context, e)

        # Post-execution hooks
        if self.config.enable_hooks:
            self._execute_post_hooks(execution_context, result)

        # Log execution if enabled
        if self.config.log_execution:
            log_execution(
                self._logger,
                skill_name,
                result.duration_ms,
                result.tokens_used,
                result.success,
            )

        # Check context usage
        if self.config.enable_context_management:
            if self._context_manager.should_warn():
                self._logger.warning(
                    f"Context usage at {self._context_manager.get_usage_percentage():.1f}%"
                )

            if self._context_manager.is_critical():
                self._logger.critical(
                    f"Context usage critical at {self._context_manager.get_usage_percentage():.1f}%"
                )

        return result

    def route_and_execute(
        self,
        query: str,
        inputs: Optional[Dict[str, Any]] = None,
        language: str = "en",
    ) -> SkillExecutionResult:
        """
        Use agent router to determine and execute appropriate skill.

        Args:
            query: User query
            inputs: Optional additional inputs
            language: Language code

        Returns:
            SkillExecutionResult with outputs and metadata
        """
        # Prepare inputs
        if inputs is None:
            inputs = {}
        inputs["query"] = query

        # Create routing context
        routing_context = RoutingContext(
            query=query,
            inputs=inputs,
            language=language,
        )

        # Get routing decision
        try:
            decision = self._agent_router.route(routing_context)

            # Execute routed skill
            return self.execute(
                decision.route.target_skill,
                query,
                inputs,
                language,
            )

        except Exception as e:
            # Routing failed, try direct execution
            self._logger.warning(f"Routing failed: {e}, attempting direct execution")

            # Try to execute as main skill
            return self.execute(
                "in-game-photography-cinematography",
                query,
                inputs,
                language,
            )

    def _execute_pre_hooks(self, context: SkillExecutionContext) -> None:
        """Execute pre-execution hooks."""
        hook_context = HookContext(
            hook_type=HookType.PRE_SKILL_EXECUTION,
            skill_name=context.skill_name,
            inputs=context.inputs,
            session_id=context.session_id,
            user_id=context.user_id,
        )

        self._hook_registry.execute_hooks(
            HookType.PRE_SKILL_EXECUTION,
            hook_context,
        )

    def _execute_post_hooks(
        self,
        context: SkillExecutionContext,
        result: SkillExecutionResult,
    ) -> None:
        """Execute post-execution hooks."""
        hook_context = HookContext(
            hook_type=HookType.POST_SKILL_EXECUTION,
            skill_name=context.skill_name,
            inputs=context.inputs,
            outputs=result.outputs,
            duration_ms=result.duration_ms,
            tokens_used=result.tokens_used,
            session_id=context.session_id,
            user_id=context.user_id,
        )

        if not result.success and result.error:
            hook_context.error = Exception(result.error)

        self._hook_registry.execute_hooks(
            HookType.POST_SKILL_EXECUTION,
            hook_context,
        )

    def _execute_error_hooks(
        self,
        context: SkillExecutionContext,
        error: Exception,
    ) -> None:
        """Execute error hooks."""
        hook_context = HookContext(
            hook_type=HookType.ON_SKILL_ERROR,
            skill_name=context.skill_name,
            inputs=context.inputs,
            error=error,
            session_id=context.session_id,
            user_id=context.user_id,
        )

        self._hook_registry.execute_hooks(
            HookType.ON_SKILL_ERROR,
            hook_context,
        )

    def get_status(self) -> Dict[str, Any]:
        """Get current harness status."""
        return {
            "skills_loaded": self._skill_registry.skill_count,
            "routes_configured": self._agent_router.route_count,
            "hooks_registered": self._hook_registry.hook_count,
            "tools_registered": self._tool_registry.tool_count if self._tool_registry else 0,
            "context_usage": self._context_manager.get_status(),
            "config": {
                "hooks_enabled": self.config.enable_hooks,
                "routing_enabled": self.config.enable_routing,
                "metrics_enabled": self.config.enable_metrics,
                "context_management": self.config.enable_context_management,
            },
        }


# Global harness instance
_global_harness: Optional[SkillHarness] = None


def get_global_harness() -> SkillHarness:
    """Get the global skill harness instance."""
    global _global_harness
    if _global_harness is None:
        _global_harness = SkillHarness()
    return _global_harness


def reset_global_harness() -> None:
    """Reset the global harness (useful for testing)."""
    global _global_harness
    _global_harness = None


# Convenience function for simple skill execution
def execute_skill(
    skill_name: str,
    query: str,
    **kwargs,
) -> SkillExecutionResult:
    """
    Execute a skill using the global harness.

    Args:
        skill_name: Name of skill to execute
        query: User query or task
        **kwargs: Additional arguments (language, inputs, etc.)

    Returns:
        SkillExecutionResult with outputs and metadata
    """
    harness = get_global_harness()
    return harness.execute(skill_name, query, **kwargs)


# Convenience function for routed execution
def route_and_execute(query: str, **kwargs) -> SkillExecutionResult:
    """
    Use agent router to determine and execute appropriate skill.

    Args:
        query: User query
        **kwargs: Additional arguments (language, inputs, etc.)

    Returns:
        SkillExecutionResult with outputs and metadata
    """
    harness = get_global_harness()
    return harness.route_and_execute(query, **kwargs)
