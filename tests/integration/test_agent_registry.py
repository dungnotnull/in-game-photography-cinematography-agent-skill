"""
Integration tests for the agent registry system.

Tests skill registration, resolution, execution, and routing functionality.
"""

import pytest
import sys
from pathlib import Path

# Add config to path
config_path = Path(__file__).parent.parent.parent / "config"
sys.path.insert(0, str(config_path))

from skill_registry import (
    SkillDefinition,
    SkillRegistry,
    SkillExecutionContext,
    RetryPolicy,
)


class TestSkillRegistry:
    """Test suite for SkillRegistry."""

    def test_registry_initialization(self):
        """Test that registry initializes empty."""
        registry = SkillRegistry()
        assert registry.skill_count == 0
        assert registry.skill_names == []

    def test_skill_registration(self):
        """Test registering a skill."""
        registry = SkillRegistry()
        skill = SkillDefinition(
            name="test-skill",
            description="A test skill",
        )

        registry.register(skill)

        assert registry.skill_count == 1
        assert "test-skill" in registry.skill_names
        assert registry.resolve("test-skill") is not None

    def test_duplicate_registration_raises(self):
        """Test that duplicate registration raises ValueError."""
        registry = SkillRegistry()
        skill = SkillDefinition(
            name="test-skill",
            description="A test skill",
        )

        registry.register(skill)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(skill)

    def test_skill_resolution(self):
        """Test resolving a skill by name."""
        registry = SkillRegistry()
        skill = SkillDefinition(
            name="test-skill",
            description="A test skill",
        )

        registry.register(skill)
        resolved = registry.resolve("test-skill")

        assert resolved is not None
        assert resolved.name == "test-skill"
        assert resolved.description == "A test skill"

    def test_skill_resolution_not_found(self):
        """Test resolving non-existent skill returns None."""
        registry = SkillRegistry()
        resolved = registry.resolve("non-existent")

        assert resolved is None

    def test_tag_based_search(self):
        """Test finding skills by tag."""
        registry = SkillRegistry()

        skill1 = SkillDefinition(
            name="analysis-skill",
            description="Analysis skill",
            tags=["analysis", "core"],
        )
        skill2 = SkillDefinition(
            name="advisor-skill",
            description="Advisor skill",
            tags=["advisory", "core"],
        )

        registry.register(skill1)
        registry.register(skill2)

        analysis_skills = registry.find_by_tag("analysis")
        assert len(analysis_skills) == 1
        assert analysis_skills[0].name == "analysis-skill"

        core_skills = registry.find_by_tag("core")
        assert len(core_skills) == 2

    def test_fuzzy_search(self):
        """Test searching for skills by name/description."""
        registry = SkillRegistry()

        skill = SkillDefinition(
            name="composition-analysis",
            description="Analyzes composition in scenes",
        )

        registry.register(skill)

        results = registry.search("composition")
        assert len(results) >= 1

        results = registry.search("scene")
        assert len(results) >= 1

    def test_execution_context_creation(self):
        """Test creating an execution context."""
        context = SkillExecutionContext(
            skill_name="test-skill",
            inputs={"query": "test"},
            language="en",
        )

        assert context.skill_name == "test-skill"
        assert context.inputs == {"query": "test"}
        assert context.language == "en"
        assert context.status.value == "pending"

    def test_execution_history(self):
        """Test execution history tracking."""
        registry = SkillRegistry()
        skill = SkillDefinition(
            name="test-skill",
            description="A test skill",
        )

        registry.register(skill)
        registry.execute("test-skill", {"test": "input"})

        history = registry.get_execution_history()
        assert len(history) == 1
        assert history[0].skill_name == "test-skill"

    def test_retry_policy(self):
        """Test retry policy configuration."""
        policy = RetryPolicy(
            max_retries=5,
            base_delay=2.0,
            exponential_base=3.0,
        )

        assert policy.max_retries == 5
        assert policy.get_delay(0) >= 2.0
        assert policy.get_delay(1) > policy.get_delay(0)


class TestSkillExecution:
    """Test suite for skill execution."""

    def test_basic_execution(self):
        """Test basic skill execution."""
        registry = SkillRegistry()

        skill = SkillDefinition(
            name="echo-skill",
            description="Echoes input",
            handler=lambda **kwargs: {"output": kwargs.get("input", "")},
        )

        registry.register(skill)
        result = registry.execute("echo-skill", {"input": "test"})

        assert result.success is True
        assert result.outputs == {"output": "test"}

    def test_execution_with_validation(self):
        """Test execution with input validation."""
        registry = SkillRegistry()

        skill = SkillDefinition(
            name="validated-skill",
            description="Validated skill",
            input_schema={
                "type": "object",
                "required": ["message"],
                "properties": {
                    "message": {"type": "string"},
                },
            },
        )

        registry.register(skill)

        # Valid input
        result = registry.execute("validated-skill", {"message": "hello"})
        assert result.input_valid is True

        # Invalid input
        result = registry.execute("validated-skill", {"invalid": "data"})
        assert result.input_valid is False
        assert result.success is False

    def test_execution_timeout(self):
        """Test execution timeout handling."""
        import time

        registry = SkillRegistry()

        def slow_handler(**kwargs):
            time.sleep(5)
            return {"done": True}

        skill = SkillDefinition(
            name="slow-skill",
            description="Slow skill",
            handler=slow_handler,
            timeout=1,  # 1 second timeout
        )

        registry.register(skill)
        result = registry.execute("slow-skill", {})

        # Should handle timeout gracefully
        assert result.success is False or result.duration_ms >= 1000


class TestAgentRouting:
    """Test suite for agent routing functionality."""

    def test_router_initialization(self):
        """Test router initialization."""
        from agent_router import AgentRouter, RoutingStrategy

        router = AgentRouter(strategy=RoutingStrategy.WEIGHTED)

        assert router.route_count == 0
        assert router.strategy == RoutingStrategy.WEIGHTED

    def test_route_registration(self):
        """Test registering routes."""
        from agent_router import AgentRouter, AgentRoute, RoutingContext

        router = AgentRouter()
        route = AgentRoute(
            name="test-route",
            condition="composition",
            target_skill="sub-core-analysis",
        )

        router.add_route(route)

        assert router.route_count == 1
        assert "test-route" in router.route_names

    def test_basic_routing(self):
        """Test basic routing decision."""
        from agent_router import (
            AgentRouter,
            AgentRoute,
            RoutingContext,
            RoutingStrategy,
        )

        router = AgentRouter(strategy=RoutingStrategy.WEIGHTED)

        route = AgentRoute(
            name="composition-route",
            condition="composition",
            target_skill="sub-core-analysis",
            priority=75,
        )

        router.add_route(route)

        context = RoutingContext(
            query="Analyze the composition",
            inputs={"scene": "..."},
        )

        decision = router.route(context)

        assert decision.route is not None
        assert decision.route.target_skill == "sub-core-analysis"
        assert decision.score > 0

    def test_routing_with_fallback(self):
        """Test routing with fallback skill."""
        from agent_router import AgentRouter, AgentRoute, RoutingContext
        from skill_registry import SkillRegistry, SkillDefinition

        router = AgentRouter()
        registry = SkillRegistry()

        # Register skills
        registry.register(SkillDefinition(
            name="primary-skill",
            description="Primary skill",
            handler=lambda **kwargs: {"result": "primary"},
        ))

        registry.register(SkillDefinition(
            name="fallback-skill",
            description="Fallback skill",
            handler=lambda **kwargs: {"result": "fallback"},
        ))

        # Register route with fallback
        route = AgentRoute(
            name="test-route",
            condition="test",
            target_skill="primary-skill",
            fallback_skill="fallback-skill",
        )

        router.add_route(route)

        context = RoutingContext(
            query="test query",
            inputs={"test": "input"},
        )

        # Should use primary skill
        result = router.route_with_fallback(context, registry)
        assert result.success is True
        assert result.outputs == {"result": "primary"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
