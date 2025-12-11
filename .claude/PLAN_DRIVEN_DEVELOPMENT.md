# Plan-Driven Development Framework

**Created:** 12/10/2025 05:45 PM PST (via pst-timestamp)
**Purpose:** Autonomous agentic development infrastructure for structured execution
**Status:** Active Framework

---

## Table of Contents

1. [Philosophy](#philosophy)
2. [Plan Document Standards](#plan-document-standards)
3. [Execution Protocols](#execution-protocols)
4. [Checkpointing & Handoff](#checkpointing--handoff)
5. [Progress Tracking](#progress-tracking)
6. [Go/No-Go Gates](#gono-go-gates)
7. [Agent Coordination](#agent-coordination)
8. [Templates](#templates)

---

## Philosophy

### Core Principles

1. **Plans are the Source of Truth**
   - All work begins with a plan document
   - Plans are living documents, updated as work progresses
   - Plans enable handoff between sessions, humans, and agents

2. **Autonomous Execution with Human Oversight**
   - Agents execute plans autonomously within defined scope
   - Clear checkpoints for human validation
   - Go/No-Go gates prevent wasted effort

3. **Transparency Through Documentation**
   - Every decision is documented
   - Every checkpoint is timestamped
   - Every handoff preserves context

4. **Incremental Progress with Validation**
   - Small, verifiable steps
   - Test/validate before proceeding
   - Fail fast, learn quickly

### When to Use Plan-Driven Development

**Use for:**
- Multi-day/multi-week initiatives
- Work requiring multiple agent invocations
- Tasks with unclear/evolving requirements
- Work requiring coordination between Claude and Codex
- Projects with validation gates

**Don't use for:**
- Single-file edits
- Trivial bug fixes
- Exploratory research (use agents directly)

---

## Plan Document Standards

### Plan Document Types

| Type | Purpose | Location | Lifecycle |
|------|---------|----------|-----------|
| **Strategic Plan** | High-level vision, market analysis, multi-month roadmap | `Plans/Strategic_*.md` | Months-Years |
| **Feature Plan** | Technical design for specific feature | `Plans/Feature_*.md` | Weeks-Months |
| **Sprint Plan** | Time-boxed execution with clear deliverables | `Plans/Sprint_*.md` | 1-4 Weeks |
| **Investigation Plan** | Research spikes, POCs, technical validation | `Plans/Investigation_*.md` | Days-Weeks |

### Naming Convention

```
Plans/{Type}_{Description}_{YYYY-MM-DD}.md

Examples:
- Plans/Strategic_Developer_API_Startup_2025-12-10.md
- Plans/Feature_Table_Parsing_Pipeline_2025-12-15.md
- Plans/Sprint_Validation_Week1_2025-12-10.md
- Plans/Investigation_XBRL_vs_HTML_Parsing_2025-12-12.md
```

### Required Sections

Every plan MUST include:

```markdown
# {Plan Title}

**Created:** {timestamp via pst-timestamp}
**Last Updated:** {timestamp via pst-timestamp}
**Status:** Draft | In Progress | Blocked | Completed | Abandoned
**Owner:** {primary responsible person/agent}
**Type:** Strategic | Feature | Sprint | Investigation

## Objective
{One-paragraph goal statement}

## Success Criteria
- [ ] Measurable criterion 1
- [ ] Measurable criterion 2
- [ ] Measurable criterion 3

## Approach
{How we'll achieve the objective}

## Tasks
{Broken down, actionable items - see Task Standards below}

## Checkpoints
{When human validation is required}

## Risks & Mitigations
{Known blockers and how to handle them}

## Changelog
| Date | Author | Changes |
|------|--------|---------|
| {timestamp} | {name} | Initial creation |
```

### Task Standards

**Task Format:**
```markdown
- [ ] {Action verb} {specific deliverable} - {acceptance criteria}
  - Status: Not Started | In Progress | Blocked | Completed
  - Owner: Claude | Codex | Human | {specific person}
  - Dependencies: {other task IDs}
  - Estimated effort: {XS | S | M | L | XL}
```

**Example:**
```markdown
- [ ] Implement semantic chunker with context preservation - Output chunks of ~500 tokens with section headers
  - Status: In Progress
  - Owner: Codex
  - Dependencies: Parser implementation (Task 1.2)
  - Estimated effort: M
  - Notes: Started 12/10/2025 03:00 PM PST, using sec-parser library
```

### Status Indicators

| Status | Meaning | Next Action |
|--------|---------|-------------|
| `[ ]` Not Started | Task not yet begun | No action needed |
| `[~]` In Progress | Active work happening | Agent should provide progress update |
| `[!]` Blocked | Cannot proceed | Human intervention required |
| `[x]` Completed | Task finished and validated | Update changelog |
| `[-]` Abandoned | Task no longer relevant | Document reason |

---

## Execution Protocols

### Starting a Plan

1. **Create Plan Document**
   ```bash
   /newplan {description}
   # Creates Plans/{Type}_{Description}_{Date}.md
   ```

2. **Initial Planning Session**
   - Claude explores codebase
   - Breaks down work into tasks
   - Identifies checkpoints and risks
   - Estimates effort
   - Outputs plan document

3. **Human Review & Approval**
   - Human reviews plan
   - Approves, requests changes, or rejects
   - Updates status to "Approved - Ready to Execute"

### Executing a Plan

1. **Run Plan Command**
   ```bash
   /runplan Plans/{plan_file}.md
   ```

2. **Agent Execution**
   - Reads plan document
   - Identifies next task(s) to execute
   - Updates task status to "In Progress"
   - Executes work
   - Updates task status to "Completed"
   - Updates changelog with timestamp

3. **Checkpointing**
   - At each checkpoint, agent pauses
   - Provides summary of work completed
   - Asks for human validation
   - Waits for "continue" before proceeding

### Handoff to Codex

For tasks marked `Owner: Codex` or mechanical repetitive work:

```bash
/handoffcodex Plans/{plan_file}.md --task-id {task_number}
```

**Codex receives:**
- Full plan context
- Specific task to execute
- Acceptance criteria
- Codebase context

**Codex returns:**
- Task completion status
- Files modified
- Test results
- Any blockers encountered

---

## Checkpointing & Handoff

### Checkpoint Types

| Type | When | Purpose |
|------|------|---------|
| **Validation Checkpoint** | After significant work | Verify correctness before continuing |
| **Decision Checkpoint** | When approach unclear | Get human input on direction |
| **Handoff Checkpoint** | Between sessions/agents | Preserve context across boundaries |
| **Go/No-Go Checkpoint** | Before major commitment | Validate assumptions before proceeding |

### Checkpoint Template

```markdown
## Checkpoint: {Name}

**Timestamp:** {pst-timestamp}
**Type:** Validation | Decision | Handoff | Go/No-Go
**Context:** {What's been done so far}

### Work Completed
- Task 1.1: {summary}
- Task 1.2: {summary}

### Decisions Made
- Decision 1: {what + rationale}
- Decision 2: {what + rationale}

### Questions for Human
1. {question requiring human input}
2. {question requiring human input}

### Next Steps (if approved)
- [ ] Task 2.1
- [ ] Task 2.2

**Status:** ⏸️ AWAITING HUMAN INPUT
```

### Handoff Protocol

When handing off between agents or sessions:

1. **Update plan changelog**
   ```markdown
   | 12/10/2025 05:45 PM PST | Claude | Completed tasks 1.1-1.3, handoff to Codex for tasks 2.1-2.5 |
   ```

2. **Create handoff note**
   ```markdown
   ## Handoff Note: Claude → Codex

   **From:** Claude (Session ID: abc123)
   **To:** Codex
   **Timestamp:** 12/10/2025 05:45 PM PST

   ### Context
   {Brief summary of work so far}

   ### Tasks for Codex
   - [ ] Task 2.1: {specific, actionable}
   - [ ] Task 2.2: {specific, actionable}

   ### Important Constraints
   - Must preserve citation format: [TICKER FORM YEAR, Section, Page]
   - All tests must pass before marking complete

   ### Files Modified So Far
   - src/parsers/chunker.py
   - tests/test_chunker.py
   ```

3. **Resume with context**
   When resuming, agent reads handoff note first

---

## Progress Tracking

### Automated Progress Updates

Plans should be updated automatically with:

```markdown
## Progress Summary

**Last Updated:** 12/10/2025 05:45 PM PST (via pst-timestamp)

### Overall Progress
- [####------] 40% (4/10 tasks completed)

### Tasks by Status
- ✅ Completed: 4
- 🔄 In Progress: 2
- ⏸️ Not Started: 4
- 🚫 Blocked: 0

### Recent Activity (Last 24h)
- 12/10/2025 03:30 PM PST: Completed task 1.2 (Parser implementation)
- 12/10/2025 02:15 PM PST: Started task 1.3 (Chunker implementation)
- 12/10/2025 10:00 AM PST: Checkpoint reached - human validation required
```

### Daily Standup Format

For multi-day plans, add daily updates:

```markdown
## Daily Standup: {Date}

**Yesterday:**
- Completed: Task 1.2, Task 1.3
- Blockers: None

**Today:**
- Plan: Task 2.1, Task 2.2
- Risk: May need human input on architectural decision

**Notes:**
- {any relevant context for next session}
```

---

## Go/No-Go Gates

### When to Use Go/No-Go Gates

- Before starting expensive/time-consuming work
- After validation/POC phase
- When pivoting approach
- Before committing to external dependencies

### Go/No-Go Template

```markdown
## Go/No-Go Gate: {Name}

**Decision Date:** {target date}
**Current Status:** Evaluating | Go | No-Go | Conditional

### Criteria

| # | Criterion | Target | Actual | Pass? |
|---|-----------|--------|--------|-------|
| 1 | {measurable criterion} | {target value} | {actual value} | ✅/❌ |
| 2 | {measurable criterion} | {target value} | {actual value} | ✅/❌ |
| 3 | {measurable criterion} | {target value} | {actual value} | ✅/❌ |

### Decision Matrix

| Criteria Met | Decision | Next Action |
|--------------|----------|-------------|
| All (3/3) | **GO** | Proceed with Phase 2 |
| Most (2/3) | **CONDITIONAL GO** | Address gap, then proceed |
| Half (1-2/3) | **REASSESS** | Pivot approach |
| Few (<1/3) | **NO-GO** | Abandon or major pivot |

### Decision
**Final Status:** {Go | No-Go | Conditional | Deferred}
**Rationale:** {why this decision was made}
**Next Steps:** {what happens next}
```

---

## Agent Coordination

### Multi-Agent Patterns

#### Pattern 1: Sequential Handoff
```
Claude (Planning) → Claude (Implementation) → Codex (Repetitive work) → Claude (Validation)
```

**When to use:** Clear phases of work with different requirements

**Example:**
1. Claude plans table parsing approach
2. Claude implements POC for one table
3. Codex applies pattern to 100 companies
4. Claude validates results

#### Pattern 2: Parallel Execution
```
Claude (Task 1) ┐
Claude (Task 2) ├→ Merge results
Codex (Task 3) ┘
```

**When to use:** Independent tasks that can run simultaneously

**Example:**
1. Claude implements semantic chunker (Task 1)
2. Another Claude implements citation generator (Task 2)
3. Codex writes test suite (Task 3)
4. Merge and integrate

#### Pattern 3: Iterative Refinement
```
Claude (Draft) → Human (Review) → Claude (Refine) → Repeat
```

**When to use:** Work requiring iteration based on feedback

**Example:**
1. Claude creates first draft of API design
2. Human reviews and provides feedback
3. Claude refines based on feedback
4. Repeat until approved

### Coordination Conventions

**Task Ownership:**
```markdown
- [ ] Task X - Owner: Claude (Architecture/design decisions)
- [ ] Task Y - Owner: Codex (Mechanical repetitive work)
- [ ] Task Z - Owner: Human (Final approval/validation)
```

**Shared Context:**
All agents have access to:
- Full plan document
- Changelog with all updates
- Handoff notes
- Test results and validation status

---

## Templates

### Template: Feature Plan

```markdown
# Feature: {Name}

**Created:** {pst-timestamp}
**Status:** Draft
**Owner:** {name}
**Type:** Feature

## Objective
{What are we building and why?}

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Technical Approach
{High-level architecture/design}

## Tasks

### Phase 1: POC
- [ ] Task 1.1: {specific deliverable}
  - Status: Not Started
  - Owner: Claude
  - Effort: M

### Phase 2: Implementation
- [ ] Task 2.1: {specific deliverable}
  - Status: Not Started
  - Owner: Codex
  - Effort: L

### Phase 3: Validation
- [ ] Task 3.1: {specific deliverable}
  - Status: Not Started
  - Owner: Claude
  - Effort: S

## Checkpoints
1. **After Phase 1:** POC validation - does the approach work?
2. **After Phase 2:** Full implementation - tests passing?
3. **After Phase 3:** Production readiness - ready to ship?

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| {risk 1} | H/M/L | H/M/L | {mitigation} |

## Changelog
| Date | Author | Changes |
|------|--------|---------|
| {timestamp} | {name} | Initial creation |
```

### Template: Sprint Plan

```markdown
# Sprint: {Name}

**Created:** {pst-timestamp}
**Duration:** {X weeks}
**Sprint Goal:** {One-sentence goal}
**Status:** Planning

## Sprint Overview
{Context and objectives}

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Weekly Breakdown

### Week 1: {Focus}
- [ ] Day 1-2: {tasks}
- [ ] Day 3-4: {tasks}
- [ ] Day 5: {tasks}

### Week 2: {Focus}
- [ ] Day 1-2: {tasks}
- [ ] Day 3-4: {tasks}
- [ ] Day 5: {tasks}

## Daily Standups
{Updated daily with progress}

## Sprint Retrospective
{Filled at end of sprint}

## Changelog
| Date | Author | Changes |
|------|--------|---------|
| {timestamp} | {name} | Sprint planning |
```

### Template: Investigation Plan

```markdown
# Investigation: {Question}

**Created:** {pst-timestamp}
**Status:** Active
**Owner:** {name}
**Type:** Investigation

## Question
{What are we trying to learn?}

## Hypotheses
1. {Hypothesis 1}
2. {Hypothesis 2}

## Experiments
- [ ] Experiment 1: {test hypothesis 1}
  - Method: {how to test}
  - Success: {what validates hypothesis}
  - Duration: {time estimate}

## Findings
{Updated as we learn}

## Decision
**Based on findings:** {Go | No-Go | Pivot}
**Rationale:** {why}
**Next Steps:** {what to do}

## Changelog
| Date | Author | Changes |
|------|--------|---------|
| {timestamp} | {name} | Initial investigation |
```

---

## Integration with Existing Commands

### /newplan
- Creates plan in `Plans/` directory
- Uses appropriate template based on plan type
- Initializes with timestamp, owner, changelog

### /runplan
- Reads plan document
- Identifies next tasks to execute
- Updates status as work progresses
- Adds changelog entries
- Stops at checkpoints for human input

### /handoffcodex
- Extracts tasks marked for Codex
- Creates handoff note with context
- Executes via Codex CLI
- Receives results back
- Updates plan with completion status

### /handoff
- Generates comprehensive handoff document
- Includes all plans, status, next steps
- Useful for end-of-session or context sharing

---

## Best Practices

### For Plan Authors
1. **Be specific in tasks** - "Implement X" is bad, "Implement X that does Y with Z acceptance criteria" is good
2. **Include validation in every task** - How do you know it's done?
3. **Estimate effort honestly** - Better to overestimate than under-deliver
4. **Update as you go** - Don't wait until end to update changelog

### For Plan Executors (Agents)
1. **Read the full plan before starting** - Understand context and constraints
2. **Update status immediately** - When you start a task, mark it in progress
3. **Stop at checkpoints** - Don't skip validation gates
4. **Document decisions** - Future you/agents need context

### For Plan Reviewers (Humans)
1. **Review plans before execution** - Catch issues early
2. **Provide clear feedback** - "Looks good" vs. "Change X because Y"
3. **Don't skip checkpoints** - Validation gates exist for a reason
4. **Update changelog when you review** - Document approval

---

## Example Workflow

### Scenario: Building Table Parser

1. **Planning Phase**
   ```bash
   /newplan Feature: XBRL Table Parsing Pipeline
   ```
   - Claude explores codebase
   - Creates feature plan with tasks
   - Identifies checkpoints
   - Human reviews and approves

2. **Phase 1: POC** (Claude)
   ```bash
   /runplan Plans/Feature_Table_Parsing_2025-12-10.md
   ```
   - Claude implements POC for one table
   - Tests with Apple Segment Information
   - Reaches checkpoint: "Does approach work?"
   - Human validates: "Yes, proceed"

3. **Phase 2: Scale** (Codex)
   ```bash
   /handoffcodex Plans/Feature_Table_Parsing_2025-12-10.md --tasks 2.1-2.5
   ```
   - Codex applies pattern to 100 companies
   - Runs tests
   - Reports results back
   - Human reviews test results

4. **Phase 3: Integration** (Claude)
   ```bash
   /runplan Plans/Feature_Table_Parsing_2025-12-10.md
   ```
   - Claude integrates into API
   - Writes API tests
   - Updates documentation
   - Marks plan as complete

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 12/10/2025 05:45 PM PST | Claude/Wolfgang | Initial framework creation |

---

*This framework is itself a living document. Update as patterns emerge and practices evolve.*
