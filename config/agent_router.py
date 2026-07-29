"""
agent_router.py — Chain-of-Thought Agent Router

This module provides intelligent routing between specialized agents using
chain-of-thought reasoning. The router analyzes the input context and
selects the most appropriate skill or agent for handling the task.

Architecture:
- AgentRoute: Definition of a routing rule
- AgentRouter: Central router with chain-of-thought logic
- RoutingContext: Context for routing decisions
- RoutingDecision: Result of routing with justification

Usage:
    router = AgentRouter()
    router.add_route(AgentRoute(...))
    decision = router.route(RoutingContext(...))
    result = decision.execute()
"""

from __future__ import annotations

import re
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


class RoutingStrategy(Enum):
    """Strategy for routing decisions."""
    EXCLUSIVE = "exclusive"  # First match wins
    WEIGHTED = "weighted"    # Highest priority score wins
    CONSENSUS = "consensus"  # Multiple skills with aggregation
    FALLBACK = "fallback"    # Try primary, then fallbacks


@dataclass
class AgentRoute:
    """
    Definition of a routing rule for agent selection.

    Attributes:
        name: Unique identifier for this route
        condition: Expression or callable that determines if route matches
        target_skill: Name of the skill to route to
        priority: Higher values take precedence (0-100)
        fallback_skill: Optional fallback skill if target fails
        tags: Tags for categorization
        metadata: Additional metadata
        requires_auth: Whether this route requires authentication
        rate_limit: Optional rate limit per minute
    """
    name: str
    condition: Union[str, Callable[[Dict[str, Any]], bool]]
    target_skill: str
    priority: int = 50
    fallback_skill: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    requires_auth: bool = False
    rate_limit: Optional[int] = None

    def matches(self, context: RoutingContext) -> bool:
        """
        Determine if this route matches the given context.

        Args:
            context: Routing context with inputs and metadata

        Returns:
            True if route matches, False otherwise
        """
        if isinstance(self.condition, str):
            # String condition: check for keyword matches
            condition_lower = self.condition.lower()
            inputs_str = str(context.inputs).lower()
            query_str = str(context.query).lower()
            return condition_lower in inputs_str or condition_lower in query_str
        elif callable(self.condition):
            # Callable condition: invoke with inputs
            try:
                return self.condition(context.inputs)
            except Exception:
                return False
        else:
            return False

    def calculate_score(self, context: RoutingContext) -> float:
        """
        Calculate a routing score for this route.

        Higher scores indicate better matches. Score is based on:
        - Priority (0-100)
        - Match quality (0-1)
        - Context fit (0-1)

        Args:
            context: Routing context

        Returns:
            Score between 0 and 100
        """
        base_score = float(self.priority)

        # Match quality bonus
        if self.matches(context):
            match_quality = 1.0
        else:
            match_quality = 0.0

        # Context fit bonus (could be extended with ML model)
        context_fit = self._calculate_context_fit(context)

        # Combine scores
        final_score = base_score * (0.5 + 0.3 * match_quality + 0.2 * context_fit)
        return min(final_score, 100.0)

    def _calculate_context_fit(self, context: RoutingContext) -> float:
        """Calculate how well this route fits the context (0-1)."""
        # Simple implementation: check tag overlap
        if not self.tags or not context.tags:
            return 0.5

        route_tags = set(self.tags)
        context_tags = set(context.tags)
        overlap = route_tags & context_tags

        if not route_tags:
            return 0.5

        return len(overlap) / len(route_tags)


@dataclass
class RoutingContext:
    """
    Context for making routing decisions.

    Contains the input query, metadata, and state information needed
    to determine the appropriate route.
    """
    query: str
    inputs: Dict[str, Any]
    language: str = "en"
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    # History and state
    previous_routes: List[str] = field(default_factory=list)
    failed_routes: List[str] = field(default_factory=list)

    def add_route_attempt(self, route_name: str, success: bool) -> None:
        """Record a route attempt."""
        self.previous_routes.append(route_name)
        if not success:
            self.failed_routes.append(route_name)


@dataclass
class RoutingDecision:
    """
    Result of a routing decision with execution capability.

    Attributes:
        route: Selected AgentRoute
        score: Routing score for this decision
        confidence: Confidence level (0-1)
        reasoning: Chain-of-thought reasoning for the decision
        alternatives: List of alternative routes considered
        context: Original routing context
        created_at: When the decision was made
    """
    route: AgentRoute
    score: float
    confidence: float
    reasoning: str
    alternatives: List[tuple[AgentRoute, float]] = field(default_factory=list)
    context: Optional[RoutingContext] = None
    created_at: datetime = field(default_factory=datetime.now)

    def execute(self, registry) -> Any:
        """
        Execute the routed skill.

        Args:
            registry: SkillRegistry to use for execution

        Returns:
            Execution result
        """
        from .skill_registry import get_global_registry

        registry = registry or get_global_registry()

        # Record attempt
        if self.context:
            self.context.add_route_attempt(self.route.name, success=True)

        # Execute the target skill
        result = registry.execute(
            self.route.target_skill,
            self.context.inputs if self.context else {},
        )

        return result


class AgentRouter:
    """
    Central router for intelligent agent selection.

    Uses chain-of-thought reasoning to select the most appropriate
    skill or agent for a given task based on context, priorities,
    and historical performance.
    """

    def __init__(self, strategy: RoutingStrategy = RoutingStrategy.WEIGHTED):
        """
        Initialize the router.

        Args:
            strategy: Routing strategy to use
        """
        self._routes: Dict[str, AgentRoute] = {}
        self._strategy = strategy
        self._decision_history: List[RoutingDecision] = []

    def add_route(self, route: AgentRoute) -> None:
        """
        Add a routing rule.

        Args:
            route: AgentRoute to add

        Raises:
            ValueError: If a route with the same name exists
        """
        if route.name in self._routes:
            raise ValueError(f"Route '{route.name}' already exists")

        self._routes[route.name] = route

    def remove_route(self, route_name: str) -> None:
        """Remove a route by name."""
        if route_name in self._routes:
            del self._routes[route_name]

    def route(self, context: RoutingContext) -> RoutingDecision:
        """
        Make a routing decision based on context.

        Args:
            context: Routing context with query and inputs

        Returns:
            RoutingDecision with selected route and reasoning

        Raises:
            ValueError: If no matching route is found
        """
        # Calculate scores for all routes
        scored_routes = []
        for route in self._routes.values():
            score = route.calculate_score(context)
            if score > 0:  # Only consider matching routes
                scored_routes.append((route, score))

        if not scored_routes:
            raise ValueError("No matching route found for context")

        # Sort by score descending
        scored_routes.sort(key=lambda x: x[1], reverse=True)

        # Select based on strategy
        if self._strategy == RoutingStrategy.EXCLUSIVE:
            selected_route, score = scored_routes[0]
        elif self._strategy == RoutingStrategy.WEIGHTED:
            # Highest score wins
            selected_route, score = scored_routes[0]
        elif self._strategy == RoutingStrategy.CONSENSUS:
            # Average top 3
            top_routes = scored_routes[:3]
            score = sum(s for _, s in top_routes) / len(top_routes)
            selected_route = top_routes[0][0]
        else:  # FALLBACK
            selected_route, score = scored_routes[0]

        # Calculate confidence based on score gap
        confidence = self._calculate_confidence(score, scored_routes)

        # Generate reasoning
        reasoning = self._generate_reasoning(
            selected_route,
            score,
            scored_routes[:5],  # Top 5 alternatives
            context,
        )

        # Create decision
        decision = RoutingDecision(
            route=selected_route,
            score=score,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=scored_routes[1:6],  # Top 5 alternatives
            context=context,
        )

        # Record decision
        self._decision_history.append(decision)

        return decision

    def _calculate_confidence(
        self,
        selected_score: float,
        all_scores: List[tuple[AgentRoute, float]],
    ) -> float:
        """Calculate confidence based on score gap."""
        if len(all_scores) == 1:
            return 1.0

        # Gap between first and second
        first_score = selected_score
        second_score = all_scores[1][1] if len(all_scores) > 1 else 0

        if second_score == 0:
            return 1.0

        gap = first_score - second_score
        confidence = min(gap / first_score, 1.0)

        return confidence

    def _generate_reasoning(
        self,
        selected_route: AgentRoute,
        score: float,
        alternatives: List[tuple[AgentRoute, float]],
        context: RoutingContext,
    ) -> str:
        """Generate chain-of-thought reasoning for the decision."""
        reasoning_parts = []

        # Analysis of the query
        reasoning_parts.append(f"Query Analysis: '{context.query}'")

        # Route selection
        reasoning_parts.append(
            f"Selected route: {selected_route.name} → {selected_route.target_skill}"
        )

        # Score justification
        reasoning_parts.append(f"Routing score: {score:.2f}/100")

        # Priority consideration
        reasoning_parts.append(f"Route priority: {selected_route.priority}/100")

        # Match explanation
        if selected_route.matches(context):
            reasoning_parts.append("Route condition matched query context")

        # Alternatives considered
        if alternatives:
            alt_names = [f"{route.name} ({score:.1f})" for route, score in alternatives[:3]]
            reasoning_parts.append(f"Alternatives considered: {', '.join(alt_names)}")

        # Context fit
        if selected_route.tags and context.tags:
            common_tags = set(selected_route.tags) & set(context.tags)
            if common_tags:
                reasoning_parts.append(f"Shared context tags: {', '.join(common_tags)}")

        return " | ".join(reasoning_parts)

    def route_with_fallback(
        self,
        context: RoutingContext,
        registry,
    ) -> Any:
        """
        Route with automatic fallback on failure.

        Args:
            context: Routing context
            registry: SkillRegistry for execution

        Returns:
            Execution result from primary or fallback skill
        """
        try:
            decision = self.route(context)

            # Try primary route
            result = decision.execute(registry)
            if result.success:
                return result

            # Try fallback if available
            if decision.route.fallback_skill:
                context.add_route_attempt(decision.route.name, success=False)
                fallback_result = registry.execute(
                    decision.route.fallback_skill,
                    context.inputs,
                )
                return fallback_result

            return result

        except ValueError as e:
            # No matching route
            from .skill_registry import SkillExecutionResult
            return SkillExecutionResult(
                success=False,
                error=f"No route found: {e}",
            )

    @property
    def route_count(self) -> int:
        """Total number of registered routes."""
        return len(self._routes)

    @property
    def route_names(self) -> List[str]:
        """List of all registered route names."""
        return list(self._routes.keys())


# Singleton router instance
_global_router: Optional[AgentRouter] = None


def get_global_router() -> AgentRouter:
    """Get the global agent router instance."""
    global _global_router
    if _global_router is None:
        _global_router = AgentRouter()
    return _global_router


def reset_global_router() -> None:
    """Reset the global agent router (useful for testing)."""
    global _global_router
    _global_router = None
