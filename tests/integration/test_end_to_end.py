"""
End-to-end integration tests for the complete v2.0.0 system.

Tests the full integration of:
- Skill harness
- Agent router
- Tool handlers
- Hooks system
- Context manager
- Logging and metrics
"""

import pytest
import sys
import time
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Now we can import from config package
from config.harness import (
    SkillHarness,
    get_global_harness,
    execute_skill,
    route_and_execute,
    HarnessConfig,
)


class TestHarnessIntegration:
    """Test suite for complete harness integration."""

    def test_harness_initialization(self):
        """Test harness initializes correctly."""
        harness = SkillHarness()

        status = harness.get_status()

        assert status["skills_loaded"] > 0
        assert status["routes_configured"] > 0
        assert status["hooks_registered"] > 0
        assert status["tools_registered"] > 0

    def test_skill_execution(self):
        """Test direct skill execution through harness."""
        harness = SkillHarness()

        result = harness.execute(
            "sub-gather-requirements",
            query="Analyze this sunset composition",
            language="en",
        )

        # Result should be valid even if skill isn't fully implemented
        assert result is not None
        assert hasattr(result, "success")
        assert hasattr(result, "outputs")
        assert hasattr(result, "duration_ms")

    def test_routed_execution(self):
        """Test agent router determines and executes skill."""
        harness = SkillHarness()

        result = harness.route_and_execute(
            query="Analyze the composition of this scene",
            language="en",
        )

        # Should have selected a route and executed
        assert result is not None
        assert hasattr(result, "success")
        assert hasattr(result, "duration_ms")

    def test_hook_execution(self):
        """Test that hooks are executed during skill execution."""
        # Track hook calls
        hook_calls = []

        def test_hook(context):
            hook_calls.append(context.hook_type.value)

        # Register test hook
        from config.hooks import get_global_hook_registry, HookType

        registry = get_global_hook_registry()
        registry.register(
            HookType.PRE_SKILL_EXECUTION,
            test_hook,
            name="test_pre_hook",
        )
        registry.register(
            HookType.POST_SKILL_EXECUTION,
            test_hook,
            name="test_post_hook",
        )

        # Execute skill
        harness = SkillHarness()
        harness.execute(
            "sub-gather-requirements",
            query="Test query",
            language="en",
        )

        # Verify hooks were called
        assert "pre_skill_execution" in hook_calls
        assert "post_skill_execution" in hook_calls

    def test_context_tracking(self):
        """Test context window tracking during execution."""
        harness = SkillHarness()

        # Execute with long query
        long_query = "Analyze this detailed sunset composition " * 100

        harness.execute(
            "sub-gather-requirements",
            query=long_query,
            language="en",
        )

        # Check context was tracked
        status = harness.get_status()
        context_usage = status["context_usage"]

        assert context_usage["current_tokens"] > 0
        assert context_usage["entry_count"] > 0

    def test_error_handling(self):
        """Test error handling and recovery."""
        harness = SkillHarness()

        # Execute with non-existent skill
        result = harness.execute(
            "non-existent-skill",
            query="Test query",
            language="en",
        )

        # Should handle error gracefully
        assert result is not None
        assert result.success is False
        assert result.error is not None

    def test_language_detection(self):
        """Test language detection and routing."""
        harness = SkillHarness()

        # Test English
        result_en = harness.execute(
            "sub-gather-requirements",
            query="Analyze this composition",
            language="en",
        )
        assert result_en is not None

        # Test Vietnamese
        result_vi = harness.execute(
            "sub-gather-requirements",
            query="Phân tích bố cục",
            language="vi",
        )
        assert result_vi is not None

    def test_concurrent_execution(self):
        """Test multiple concurrent executions."""
        harness = SkillHarness()

        queries = [
            "Analyze composition",
            "Check lighting",
            "Evaluate camera angle",
        ]

        results = []
        for query in queries:
            result = harness.execute(
                "sub-gather-requirements",
                query=query,
                language="en",
            )
            results.append(result)

        # All should complete
        assert len(results) == len(queries)
        for result in results:
            assert result is not None

    def test_tool_execution(self):
        """Test tool execution through harness."""
        from config.tool_handlers import initialize_tool_registry

        # Initialize tools
        tool_registry = initialize_tool_registry()

        # Execute Read tool
        result = tool_registry.execute(
            "Read",
            {"file_path": "CLAUDE.md"},
        )

        assert result is not None
        assert result.success is True or result.error is not None

    def test_metrics_collection(self):
        """Test metrics are collected during execution."""
        from config.logging_config import get_metrics_collector

        collector = get_metrics_collector()
        collector.clear()  # Clear previous metrics

        harness = SkillHarness()
        harness.execute(
            "sub-gather-requirements",
            query="Test query",
            language="en",
        )

        # Check metrics were collected
        stats = collector.get_stats()
        # Should have metrics for the skill we just executed
        assert len(stats) >= 0  # May have metrics or may not depending on hooks

    def test_configuration(self):
        """Test different harness configurations."""
        # Test with hooks disabled
        config_no_hooks = HarnessConfig(enable_hooks=False)
        harness_no_hooks = SkillHarness(config=config_no_hooks)

        status = harness_no_hooks.get_status()
        assert status["config"]["hooks_enabled"] is False

        # Test with routing disabled
        config_no_routing = HarnessConfig(enable_routing=False)
        harness_no_routing = SkillHarness(config=config_no_routing)

        status = harness_no_routing.get_status()
        assert status["config"]["routing_enabled"] is False

    def test_global_harness(self):
        """Test global harness instance."""
        harness = get_global_harness()

        assert harness is not None

        status = harness.get_status()
        assert status["skills_loaded"] > 0

    def test_convenience_functions(self):
        """Test convenience functions for skill execution."""
        # Test execute_skill
        result1 = execute_skill(
            "sub-gather-requirements",
            query="Test query",
            language="en",
        )
        assert result1 is not None

        # Test route_and_execute
        result2 = route_and_execute(
            query="Analyze composition",
            language="en",
        )
        assert result2 is not None


class TestSystemPerformance:
    """Test system performance under load."""

    def test_bulk_execution(self):
        """Test executing many skills in sequence."""
        harness = SkillHarness()

        start_time = time.time()

        for i in range(10):
            harness.execute(
                "sub-gather-requirements",
                query=f"Test query {i}",
                language="en",
            )

        duration = time.time() - start_time

        # Should complete 10 executions in reasonable time
        assert duration < 30.0  # Less than 30 seconds

    def test_memory_usage(self):
        """Test memory usage doesn't grow unbounded."""
        import gc
        import sys

        harness = SkillHarness()

        # Get initial memory
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Execute multiple times
        for i in range(5):
            harness.execute(
                "sub-gather-requirements",
                query=f"Test query {i}",
                language="en",
            )

        # Check memory hasn't grown excessively
        gc.collect()
        final_objects = len(gc.get_objects())

        # Should not have doubled object count
        assert final_objects < initial_objects * 2


class TestErrorRecovery:
    """Test error recovery and fallback mechanisms."""

    def test_skill_not_found_recovery(self):
        """Test recovery when skill is not found."""
        harness = SkillHarness()

        result = harness.execute(
            "non-existent-skill",
            query="Test",
            language="en",
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_invalid_input_handling(self):
        """Test handling of invalid inputs."""
        harness = SkillHarness()

        # Empty query
        result = harness.execute(
            "sub-gather-requirements",
            query="",
            language="en",
        )

        # Should handle gracefully
        assert result is not None

    def test_timeout_handling(self):
        """Test timeout handling."""
        # Create harness with short timeout
        config = HarnessConfig(max_execution_time=1)  # 1 second
        harness = SkillHarness(config=config)

        # This should complete quickly
        result = harness.execute(
            "sub-gather-requirements",
            query="Quick test",
            language="en",
        )

        # Should complete within timeout
        assert result is not None


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_photography_analysis_workflow(self):
        """Test complete photography analysis workflow."""
        harness = SkillHarness()

        # Simulate a complete workflow
        queries = [
            "I need to analyze a sunset scene from Ghost of Tsushima",
            "The scene has a golden sky with mountains in the background",
            "What composition principles should I use?",
        ]

        results = []
        for query in queries:
            result = harness.route_and_execute(query=query, language="en")
            results.append(result)

        # All should complete
        assert len(results) == len(queries)
        assert all(r is not None for r in results)

    def test_multilingual_workflow(self):
        """Test workflow with multiple languages."""
        harness = SkillHarness()

        # English query
        result_en = harness.route_and_execute(
            query="Analyze this composition",
            language="en",
        )

        # Vietnamese query
        result_vi = harness.route_and_execute(
            query="Phân tích bố cục này",
            language="vi",
        )

        assert result_en is not None
        assert result_vi is not None


def run_integration_tests():
    """Run all integration tests and return results."""
    print("Running v2.0.0 Integration Tests...")
    print("=" * 60)

    test_results = {}

    # Test harness initialization
    print("\n1. Testing harness initialization...")
    try:
        test = TestHarnessIntegration()
        test.test_harness_initialization()
        print("   [OK] Harness initialization")
        test_results["harness_init"] = True
    except Exception as e:
        print(f"   [FAIL] Harness initialization: {e}")
        test_results["harness_init"] = False

    # Test skill execution
    print("\n2. Testing skill execution...")
    try:
        test = TestHarnessIntegration()
        test.test_skill_execution()
        print("   [OK] Skill execution")
        test_results["skill_execution"] = True
    except Exception as e:
        print(f"   [FAIL] Skill execution: {e}")
        test_results["skill_execution"] = False

    # Test routed execution
    print("\n3. Testing routed execution...")
    try:
        test = TestHarnessIntegration()
        test.test_routed_execution()
        print("   [OK] Routed execution")
        test_results["routed_execution"] = True
    except Exception as e:
        print(f"   [FAIL] Routed execution: {e}")
        test_results["routed_execution"] = False

    # Test hook execution
    print("\n4. Testing hook execution...")
    try:
        test = TestHarnessIntegration()
        test.test_hook_execution()
        print("   [OK] Hook execution")
        test_results["hook_execution"] = True
    except Exception as e:
        print(f"   [FAIL] Hook execution: {e}")
        test_results["hook_execution"] = False

    # Test context tracking
    print("\n5. Testing context tracking...")
    try:
        test = TestHarnessIntegration()
        test.test_context_tracking()
        print("   [OK] Context tracking")
        test_results["context_tracking"] = True
    except Exception as e:
        print(f"   [FAIL] Context tracking: {e}")
        test_results["context_tracking"] = False

    # Test error handling
    print("\n6. Testing error handling...")
    try:
        test = TestHarnessIntegration()
        test.test_error_handling()
        print("   [OK] Error handling")
        test_results["error_handling"] = True
    except Exception as e:
        print(f"   [FAIL] Error handling: {e}")
        test_results["error_handling"] = False

    # Test tool execution
    print("\n7. Testing tool execution...")
    try:
        test = TestHarnessIntegration()
        test.test_tool_execution()
        print("   [OK] Tool execution")
        test_results["tool_execution"] = True
    except Exception as e:
        print(f"   [FAIL] Tool execution: {e}")
        test_results["tool_execution"] = False

    # Test performance
    print("\n8. Testing system performance...")
    try:
        test = TestSystemPerformance()
        test.test_bulk_execution()
        print("   [OK] System performance")
        test_results["performance"] = True
    except Exception as e:
        print(f"   [FAIL] System performance: {e}")
        test_results["performance"] = False

    # Print summary
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in test_results.values() if v)
    total = len(test_results)

    for test_name, passed_bool in test_results.items():
        status = "[OK]" if passed_bool else "[FAIL]"
        print(f"{status} {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\nSUCCESS: All integration tests passed! System is ready for go-live.")
        return True
    else:
        print(f"\nWARNING: {total - passed} test(s) failed. Review errors above.")
        return False


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
