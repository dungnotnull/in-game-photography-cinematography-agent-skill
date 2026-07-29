# SKILL.md — Skill Registry Documentation

## Overview

The `in-game-photography-cinematography` skill uses a dynamic agent registry pattern with chain-of-thought routing for specialized sub-agents. This document describes how skills are registered, resolved, executed, and validated.

---

## Skill Architecture

### Core Components

1. **SkillDefinition**: Schema for skill metadata and contracts
2. **SkillRegistry**: Central registry for all skills
3. **AgentRouter**: Chain-of-thought router for agent selection
4. **HookRegistry**: Lifecycle hooks for execution management
5. **ToolRegistry**: Schema-defined tool execution

### Design Philosophy

- **Dynamic Resolution**: Skills are loaded and resolved at runtime, not hardcoded
- **Chain-of-Thought Routing**: Intelligent routing based on context and priorities
- **Lifecycle Management**: Hooks provide cross-cutting concerns (logging, monitoring)
- **Schema Validation**: All inputs/outputs validated against JSON schemas
- **Graceful Degradation**: Fallback chains ensure robustness

---

## Registration Process

### 1. Skill Definition

Skills are defined using the `SkillDefinition` dataclass:

```python
from config.skill_registry import SkillDefinition

skill = SkillDefinition(
    name="sub-core-analysis",
    description="Analyze scenes and propose camera settings",
    version="1.0.0",
    input_schema={
        "type": "object",
        "required": ["scene_description", "language"],
        "properties": {
            "scene_description": {"type": "string"},
            "language": {"type": "string"},
        },
    },
    output_schema={
        "type": "object",
        "required": ["composition", "angle", "lighting"],
    },
    tool_dependencies=["WebSearch", "Read"],
    tags=["analysis", "core"],
)
```

### 2. Registration

Skills can be registered programmatically or from directories:

```python
from config.skill_registry import get_global_registry

registry = get_global_registry()
registry.register(skill)

# Or register from directory
count = registry.register_from_directory("skills/")
```

### 3. Markdown Frontmatter

Skills defined as markdown files with YAML frontmatter:

```markdown
---
name: sub-core-analysis
description: Analyze scenes and propose camera settings for virtual photography
version: 1.0.0
tags: [analysis, core]
---

## Role & Persona
You are a virtual photography advisor...

## Workflow
...
```

---

## Resolution Algorithm

### 1. Direct Resolution

Resolve by exact name:

```python
skill = registry.resolve("sub-core-analysis")
```

### 2. Tag-Based Search

Find skills by tags:

```python
analysis_skills = registry.find_by_tag("analysis")
```

### 3. Fuzzy Search

Search by name or description:

```python
results = registry.search("composition analysis")
```

### Resolution Priority

1. Exact name match (score: 100)
2. Partial name match (score: 80)
3. Description match (score: 60)
4. No match (None)

---

## Execution Protocol

### 1. Context Creation

Create execution context with inputs:

```python
from config.skill_registry import SkillExecutionContext

context = SkillExecutionContext(
    skill_name="sub-core-analysis",
    inputs={
        "scene_description": " sunset over mountains",
        "language": "en",
    },
    language="en",
)
```

### 2. Execution

Execute with validation:

```python
result = registry.execute(
    skill_name="sub-core-analysis",
    inputs=context.inputs,
    context=context,
)
```

### 3. Result Handling

Process execution result:

```python
if result.success:
    print(f"Output: {result.outputs}")
    print(f"Duration: {result.duration_ms}ms")
    print(f"Tokens: {result.tokens_used}")
else:
    print(f"Error: {result.error}")
```

---

## Agent Routing

### 1. Route Definition

Define routing rules:

```python
from config.agent_router import AgentRoute, RoutingStrategy

route = AgentRoute(
    name="analysis_route",
    condition="composition" or "camera" or "lighting",
    target_skill="sub-core-analysis",
    priority=75,
    fallback_skill="sub-advisor",
    tags=["analysis", "routing"],
)
```

### 2. Chain-of-Thought Decision

Router analyzes context and selects appropriate skill:

```python
from config.agent_router import AgentRouter, RoutingContext

router = AgentRouter(strategy=RoutingStrategy.WEIGHTED)
router.add_route(route)

context = RoutingContext(
    query="Analyze this sunset composition",
    inputs={"scene": "..."},
    language="en",
)

decision = router.route(context)
print(decision.reasoning)  # Chain-of-thought explanation
```

### 3. Execution with Fallback

Execute with automatic fallback:

```python
result = router.route_with_fallback(context, registry)
```

---

## Hook Integration

### 1. Hook Registration

Register lifecycle hooks:

```python
from config.hooks import HookType, HookPriority, get_global_hook_registry

registry = get_global_hook_registry()

def my_logging_hook(context):
    print(f"Skill {context.skill_name} executed in {context.duration_ms}ms")

registry.register(
    HookType.POST_SKILL_EXECUTION,
    my_logging_hook,
    name="my_logger",
    priority=HookPriority.NORMAL,
)
```

### 2. Hook Execution

Hooks execute automatically at lifecycle points:

```python
from config.hooks import HookContext

context = HookContext(
    hook_type=HookType.POST_SKILL_EXECUTION,
    skill_name="sub-core-analysis",
    duration_ms=1234,
)

registry.execute_hooks(HookType.POST_SKILL_EXECUTION, context)
```

### 3. Decorator Registration

Use decorator for cleaner registration:

```python
from config.hooks import hook, HookType, HookPriority

@hook(HookType.PRE_SKILL_EXECUTION, priority=HookPriority.HIGH)
def log_start(context):
    print(f"Starting {context.skill_name}")
```

---

## Tool Dependencies

### 1. Tool Definition

Define tools with schemas:

```python
from config.tool_schemas import ToolDefinition, get_global_tool_registry

tool = ToolDefinition(
    name="WebSearch",
    description="Search the web for information",
    input_schema={
        "type": "object",
        "required": ["query"],
        "properties": {
            "query": {"type": "string"},
            "max_results": {"type": "integer"},
        },
    },
    handler=lambda query, max_results=5: {"results": [...]},
    timeout=30,
)

registry = get_global_tool_registry()
registry.register(tool)
```

### 2. Tool Execution

Execute tools through registry:

```python
result = registry.execute(
    "WebSearch",
    {"query": "composition techniques", "max_results": 10},
)

if result.success:
    print(result.data)
```

---

## Error Recovery

### 1. Fallback Chain

When primary execution fails, try fallbacks:

1. Try alternate source
2. Use cached data
3. Query knowledge base
4. Use default values
5. Explicit limitation notice

### 2. Degradation Levels

| Level | Condition | Behavior |
|-------|-----------|----------|
| 0 | All sources reachable | Full analysis |
| 1 | Some sources fail | Use secondary, flag substitutions |
| 2 | Most sources fail | Knowledge base only |
| 3 | Required input missing | Proceed with available, flag gaps |
| 4 | All sources fail | Emit "DATA UNAVAILABLE" |

### 3. Limitation Notice

Always emit when degraded:

```markdown
---
⚠️ LIMITATION NOTICE
This output was generated with reduced data availability (Level [0–4]).
Cross-check with current data before acting on it.
---
```

---

## Performance Optimization

### 1. Token Management

Context window tracking and pruning:

```python
from config.context_manager import ContextManager

manager = ContextManager(max_tokens=100000)
manager.track_tokens(45000)  # Track usage

if manager.should_prune():
    manager.prune_strategy = "recent_priority"
    pruned = manager.prune()
```

### 2. Caching

Cache results for expensive operations:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def cached_search(query: str):
    return web_search(query)
```

### 3. Rate Limiting

Respect API rate limits:

```python
tool = ToolDefinition(
    name="WebSearch",
    rate_limit=10,  # 10 requests per minute
    ...
)
```

---

## Validation Schema

### Input Schema Example

```json
{
  "type": "object",
  "required": ["scene_description", "language"],
  "properties": {
    "scene_description": {
      "type": "string",
      "minLength": 10,
      "maxLength": 1000
    },
    "language": {
      "type": "string",
      "enum": ["en", "vi", "other"]
    },
    "photo_mode_available": {
      "type": "boolean",
      "default": true
    }
  }
}
```

### Output Schema Example

```json
{
  "type": "object",
  "required": ["composition", "angle", "lighting"],
  "properties": {
    "composition": {
      "type": "object",
      "properties": {
        "principles": {"type": "array", "items": {"type": "string"}},
        "score": {"type": "number", "minimum": 0, "maximum": 10}
      }
    },
    "angle": {"type": "string"},
    "lighting": {"type": "string"}
  }
}
```

---

## Testing

### 1. Unit Tests

Test individual components:

```python
def test_skill_registration():
    registry = SkillRegistry()
    skill = SkillDefinition(name="test", description="Test skill")
    registry.register(skill)
    assert registry.resolve("test") is not None
```

### 2. Integration Tests

Test full execution flow:

```python
def test_full_execution():
    registry = SkillRegistry()
    registry.register_from_directory("skills/")
    result = registry.execute("sub-core-analysis", test_inputs)
    assert result.success
    assert result.outputs is not None
```

### 3. Performance Tests

Benchmark execution:

```python
def test_execution_performance():
    start = time.time()
    result = registry.execute("sub-core-analysis", inputs)
    duration = time.time() - start
    assert duration < 5.0  # Must complete in under 5 seconds
```

---

## Monitoring

### 1. Metrics Collection

Collect execution metrics:

```python
from config.hooks import HookType, hook

@hook(HookType.POST_SKILL_EXECUTION)
def collect_metrics(context):
    metrics = {
        "skill": context.skill_name,
        "duration": context.duration_ms,
        "tokens": context.tokens_used,
    }
    send_to_monitoring(metrics)
```

### 2. Logging

Structured logging output:

```json
{
  "timestamp": "2026-07-21T10:30:00Z",
  "level": "INFO",
  "component": "sub-core-analysis",
  "event_type": "skill_execution",
  "metrics": {
    "duration_ms": 1234,
    "tokens_used": 45678
  }
}
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SKILL_ENVIRONMENT` | development | Environment (dev/staging/prod) |
| `SKILL_DEBUG` | false | Enable debug mode |
| `SKILL_MAX_EXECUTION_TIME` | 300 | Max skill execution time (seconds) |
| `SKILL_MAX_TOKENS` | 100000 | Context window size |
| `SKILL_WARNING_THRESHOLD` | 0.85 | Token warning threshold |
| `SKILL_LOG_LEVEL` | INFO | Logging level |
| `SKILL_ENABLE_HOOKS` | true | Enable lifecycle hooks |
| `SKILL_ENABLE_ROUTING` | true | Enable agent routing |

### Config File

Optional JSON config file:

```json
{
  "skill_name": "in-game-photography-cinematography",
  "skill_version": "2.0.0",
  "environment": "development",
  "execution": {
    "max_execution_time": 300,
    "max_retries": 3
  },
  "context": {
    "max_tokens": 100000,
    "warning_threshold": 0.85
  }
}
```

---

## Best Practices

### 1. Skill Design

- Keep skills focused on single responsibility
- Use clear, descriptive names
- Provide comprehensive input/output schemas
- Include fallback handlers for critical tools

### 2. Routing

- Define clear, testable conditions
- Use appropriate priorities
- Provide fallback skills for resilience
- Document routing decisions in chain-of-thought

### 3. Hooks

- Use appropriate priorities (CRITICAL for error handling)
- Keep hooks fast and non-blocking
- Handle exceptions gracefully
- Document side effects

### 4. Tools

- Always define input/output schemas
- Set appropriate timeouts
- Implement fallback handlers for external tools
- Respect rate limits

---

## Security Considerations

### 1. Input Validation

- Always validate against schemas
- Sanitize user inputs
- Check for malicious patterns

### 2. API Keys

- Never hardcode credentials
- Use environment variables
- Rotate keys regularly

### 3. Rate Limiting

- Respect API rate limits
- Implement backoff strategies
- Monitor for abuse

---

## References

- Skill Definition: `config/skill_registry.py`
- Agent Routing: `config/agent_router.py`
- Hooks: `config/hooks.py`
- Tools: `config/tool_schemas.py`
- Settings: `config/settings.py`
- Domain Knowledge: `references/domain/`
- Prompt Templates: `references/prompts/`
