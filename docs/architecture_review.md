# Architectural Review: SEC Edgar Agent

## Executive Summary

The `sec-edgar-agent` implements a sophisticated 4-phase multi-agent architecture (Planning, Execution, Validation, Synthesis). The codebase structures closely follow the proposed architectural diagram, showing a clear separation of concerns and modular design.

However, we identified critical gaps between the _proposed_ capabilities (e.g., "re-execution if needed") and the _actual_ implementation (validation warns but does not correct). There are also opportunities to significantly improve performance through parallelism and robustness through structured outputs.

## Analysis of Current Implementation

### Strengths

1.  **Clean Modularity**: The codebase uses a clear `BaseAgent` abstraction and a well-defined `Orchestrator` that manages the lifecycle.
2.  **Type Safety**: Usage of Pydantic (`Task`, `Plan`, `AgentContext`) ensures data consistency across agents.
3.  **Tool Registry**: The decorator-based `ToolRegistry` provides a clean way to expose Python functions to the LLM.
4.  **Streaming Support**: `StreamingOrchestrator` is already implemented, which is excellent for user experience.

### Critical Gaps

1.  **Missing Feedback Loop (The "Toothless" Validator)**:

    - **Issue**: The `ValidatorAgent` runs, detects issues, and logs warnings (`self.logger.warning`), but the `Orchestrator` proceeds to the Synthesis phase regardless of the validation outcome.
    - **Impact**: Incorrect or incomplete data is passed to the Synthesizer, potentially leading to hallucinations or poor answers, defeating the purpose of the validation phase.

2.  **Sequential Execution (Performance Bottleneck)**:

    - **Issue**: The `ExecutorAgent` runs tasks serially (`while... _get_next_task`).
    - **Impact**: Independent tasks (e.g., retrieving data for three different companies) are blocked by each other. This significantly increases latency for complex queries.

3.  **Fragile Parsing**:

    - **Issue**: Example: `PlannerAgent` relies on `_extract_text` and regex/string splitting to find JSON (` text.split("```json") `).
    - **Impact**: Highly susceptible to breakage if the model outputs slightly malformed markdown or chatty preamble.

4.  **Ephemeral State**:
    - **Issue**: `AgentContext` is purely in-memory.
    - **Impact**: Long-running research tasks cannot be resumed if the process crashes or is restarted.

## Recommendations

### 1. Close the Validation Loop

**Priority: High**
Modify the `Orchestrator` to handle failed validation by routing control back to a previous phase.

**Proposed Logic:**

```python
# In Orchestrator.run()
max_retries = 3
while retries < max_retries:
    # ... Plan & Execute ...

    if not is_simple:
        validation = self.validator.run(context)
        if not validation.content["valid"]:
             # Add a corrective task to the plan
             self._add_correction_tasks(context, validation.content["issues"])
             retries += 1
             continue # Loop back to execution
    break
```

### 2. Implement Parallel Execution

**Priority: High**
Update `ExecutorAgent` to identify _all_ executable tasks (dependencies met) and run them concurrently.

**Proposed Logic:**

- Change `_get_next_task` to `_get_executable_tasks`.
- Use `asyncio.gather` to run tool calls for multiple tasks simultaneously.
- _Note_: This requires making the agent methods `async`.

### 3. Adopt Structured Outputs

**Priority: Medium**
Replace regex/JSON parsing with OpenAI's `response_format={ "type": "json_object" }` or Pydantic-based extraction (e.g., `instructor` library or raw tool calling for structural enforcement).

**Benefit**: drastically reduces "Failed to parse plan" errors.

### 4. Database-Backed State

**Priority: Low/Future**
Persist `AgentContext` to a database (SQLite/PostgreSQL). This enables:

- Resumable workflows.
- Analytics on agent performance.
- Audit trails for compliance.

### 5. Configurable Prompts

**Priority: Medium**
Move system prompts (currently hardcoded strings in `*.py` files) to a configuration file (YAML/JSON) or a dedicated prompt management class. This allows easier iteration on prompt engineering without code deploys.
